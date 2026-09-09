"""Real subprocess + loopback integration, no agent accounts or USB required."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import test_system as system
from ocdeck.broker import Broker
from ocdeck.common import atomic_json, request
from ocdeck.harness import worker

SOURCE = Path(__file__).resolve().parent.parent


class HarnessIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.identity_patch = patch('ocdeck.broker.identity', system.identity)
        self.identity_patch.start()
        self.start_broker()

    def start_broker(self):
        self.broker = Broker(self.root, mock=True)
        self.thread = threading.Thread(target=self.broker.serve)
        self.thread.start()
        for _ in range(200):
            if (self.root / 'discovery.json').exists(): return
            time.sleep(.01)
        self.fail('broker startup timed out')

    def tearDown(self):
        self.broker.stop.set(); self.thread.join(5)
        self.identity_patch.stop(); self.tmp.cleanup()

    def state(self, expected):
        for _ in range(200):
            value = request('GET', '/v1/status', root=self.root)
            if value['slots'][0]['state'] == expected: return value
            time.sleep(.025)
        self.fail(f'expected {expected}: {value}')

    def hook(self, env, event, payload):
        result = subprocess.run(['node', str(SOURCE / 'plugins/harnesses/hook.mjs'), 'claude', event],
                                input=json.dumps(payload), env=env, capture_output=True, text=True, timeout=5)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))

    def test_bridge_restart_pending_identity_and_loss(self):
        binding = self.root / 'binding.json'; descriptor = self.root / 'hook.json'
        atomic_json(binding, {'id':'claude-live', 'process':system.identity(), 'label':'Claude', 'managed':True})
        env = dict(os.environ, OCDECK_HOME=str(self.root), AGENTDECK_HOOK_BINDING=str(descriptor))
        bridge = subprocess.Popen(['node', str(SOURCE/'plugins/harnesses/bridge.mjs'), '--worker',
                                   'claude', str(binding), str(descriptor)], env=env, stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            for _ in range(100):
                if descriptor.exists(): break
                time.sleep(.025)
            self.state('unknown')
            self.hook(env,'SessionStart',{'session_id':'s'}); self.state('idle')
            self.hook(env,'UserPromptSubmit',{'session_id':'s'}); self.state('running')
            self.hook(env,'PreToolUse',{'session_id':'s','tool_name':'AskUserQuestion','tool_use_id':'q'})
            before = self.state('input')
            self.broker.stop.set(); self.thread.join(5)
            self.start_broker()
            after = self.state('input')
            self.assertNotEqual(before['epoch'],after['epoch'])
            self.assertEqual(after['slots'][0]['id'],'claude-live')
            self.assertTrue(all(s['id'] is None for s in after['slots'][1:]))
            self.hook(env,'PostToolUseFailure',{'session_id':'s','tool_use_id':'q'}); self.state('running')
            self.hook(env,'Stop',{'session_id':'s'}); self.state('idle')
            self.hook(env,'Stop',{})  # No session identity -> explicit loss, never false idle.
            self.state('unknown')
        finally:
            bridge.stdin.close()
            bridge.wait(timeout=5)
            self.assertEqual(bridge.returncode,0,bridge.stderr.read().decode())
            bridge.stdout.close(); bridge.stderr.close()
        self.assertFalse(descriptor.exists())

    def test_supervisor_drives_hooks_preserves_args_exit_code_and_cleans_up(self):
        fake = self.root / 'fake harness.py'
        fake.write_text('''import os, subprocess, json, sys, time
from ocdeck.common import request
assert sys.argv[1:] == ['space arg', 'a&b', 'quote"value', '$literal']
for event in ['SessionStart', 'UserPromptSubmit', 'Stop']:
    subprocess.run(['node', os.environ['HOOK_SCRIPT'], 'claude', event],
                   input=json.dumps({'session_id':'s'}),text=True,check=True)
    wanted = {'SessionStart':'idle','UserPromptSubmit':'running','Stop':'idle'}[event]
    for _ in range(100):
        if request('GET','/v1/status')['slots'][0]['state'] == wanted: break
        time.sleep(.03)
    else: raise RuntimeError('state did not reach '+wanted)
sys.exit(7)
''')
        spec = {'id':'worker-test', 'profile':'claude', 'executable':sys.executable,
                'cwd':str(SOURCE), 'args':[str(fake),'space arg','a&b','quote"value','$literal'], 'windowToken':''}
        with patch.dict(os.environ, {'OCDECK_HOME':str(self.root), 'HOOK_SCRIPT':str(SOURCE/'plugins/harnesses/hook.mjs')}), \
             patch('ocdeck.harness.identity',system.identity):
            self.assertEqual(worker(spec),7)
        self.state('off')
        self.assertFalse((self.root/'launches/worker-test.hooks').exists())
