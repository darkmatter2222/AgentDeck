"""Win32 contract regression tests; physical desktop acceptance is separate."""
import unittest
from ocdeck.focus import focus_window

class Desktop:
    def __init__(self):
        self.foreground=100;self.focus=201;self.attached=set();self.events=[]
        self.minimized=False;self.denied=set();self.raise_focus=False;self.direct=False
    def GetWindowThreadProcessId(self,hwnd,_): return {100:10,200:20}.get(hwnd,0)
    def IsWindow(self,hwnd): return hwnd in (100,200,201)
    def IsHungAppWindow(self,hwnd): return False
    def IsChild(self,parent,child): return parent==200 and child==201
    def IsIconic(self,hwnd): return self.minimized
    def ShowWindowAsync(self,hwnd,mode): self.events.append(('restore',hwnd));self.minimized=False;return True
    def GetForegroundWindow(self): return self.foreground
    def GetGUIThreadInfo(self,thread,ptr): ptr._obj.hwndFocus=self.focus;return True
    def SetForegroundWindow(self,hwnd):
        if self.direct or {10,20}<=self.attached: self.foreground=hwnd;return True
        return False
    def PeekMessageW(self,*args): self.events.append(('queue',));return False
    def AttachThreadInput(self,current,other,attach):
        self.events.append(('attach',other,attach))
        if attach and other in self.denied:return False
        if attach:self.attached.add(other)
        else:self.attached.remove(other)
        return True
    def BringWindowToTop(self,hwnd): pass
    def SetActiveWindow(self,hwnd): pass
    def SetFocus(self,hwnd):
        self.events.append(('focus',hwnd))
        if self.raise_focus:raise OSError('test focus failure')
        if 20 in self.attached:self.focus=hwnd

class FocusTests(unittest.TestCase):
    def test_attaches_destination_and_foreground_preserves_input_child(self):
        u=Desktop();result=focus_window(u,30,200,sleep=lambda _:None)
        self.assertTrue(result['ok']);self.assertTrue(result['keyboardFocus'])
        self.assertEqual(u.events[0],('queue',))
        self.assertIn(('focus',201),u.events)
        self.assertEqual(u.events[-2:],[('attach',20,False),('attach',10,False)])
        self.assertFalse(u.attached)
    def test_minimized_window_restored(self):
        u=Desktop();u.minimized=True
        self.assertTrue(focus_window(u,30,200,sleep=lambda _:None)['ok'])
        self.assertEqual(u.events[0],('restore',200))
    def test_direct_success_requires_keyboard_focus(self):
        u=Desktop();u.direct=True;u.focus=0
        result=focus_window(u,30,200,sleep=lambda _:None)
        self.assertTrue(result['ok']);self.assertIn(('focus',200),u.events)
    def test_denied_attachment_does_not_report_success(self):
        u=Desktop();u.denied.add(20)
        result=focus_window(u,30,200,sleep=lambda _:None)
        self.assertFalse(result['ok']);self.assertEqual(result['attachmentFailures'],[20])
        self.assertFalse(u.attached)
    def test_exception_always_detaches(self):
        u=Desktop();u.raise_focus=True
        with self.assertRaises(OSError):focus_window(u,30,200,sleep=lambda _:None)
        self.assertFalse(u.attached)
    def test_already_focused_needs_no_attachment(self):
        u=Desktop();u.foreground=200
        self.assertTrue(focus_window(u,30,200,sleep=lambda _:None)['ok'])
        self.assertFalse(u.events)
