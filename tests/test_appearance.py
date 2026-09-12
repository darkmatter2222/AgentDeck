import queue
import threading
import time
import unittest
from ocdeck.appearance import Appearance, THEMES, appearance, animation_phase
from ocdeck.art import frame
from ocdeck.device import DeviceLoop
from ocdeck.model import Registry

class AppearanceTests(unittest.TestCase):
    def test_overrides_and_validation(self):
        c = {'appearance': {'theme':'ocean'}, 'buttons': {'2': {'layout':'harness'}}}
        self.assertEqual(appearance(c,1).theme,'ocean')
        self.assertEqual(appearance(c,1).layout,'harness')
        self.assertEqual(appearance(c,0).layout,'classic')
        for value in (float('nan'),float('inf'),-1,4):
            with self.assertRaises(ValueError): appearance({'appearance':{'speed':value}})
        with self.assertRaises(ValueError): appearance({'appearance':{'theme':'typo'}})

    def test_render_matrix_and_black_empty_slots(self):
        for theme in THEMES:
            for layout in ('classic','harness','minimal'):
                a=Appearance(theme=theme,layout=layout,secondary='custom',custom_text='Long text '*20)
                for harness in ('opencode','claude','copilot','gemini','cursor','custom'):
                    for state in ('running','idle','input','ready','unknown','off'):
                        im=frame(state,'Project',0,12,80,a,harness)
                        self.assertEqual(im.size,(80,80))
                        if state=='off': self.assertIsNone(im.getbbox())

    def test_motion_and_brightness(self):
        a=Appearance()
        self.assertEqual(animation_phase(0,a),animation_phase(2,a))
        self.assertEqual(animation_phase(5,a,False),24)
        self.assertEqual(animation_phase(9,Appearance(effect='steady')),24)
        bright=frame('running','Test',0,24)
        dim=frame('running','Test',0,24,80,Appearance(brightness=.3))
        self.assertLess(sum(dim.tobytes()),sum(bright.tobytes()))

    def test_identical_pixels_still_update_focus_assignment(self):
        r=Registry(lambda _:True); stop=threading.Event(); q=queue.Queue()
        d=DeviceLoop(r,q,stop,{'animations':False,'fps':30},True)
        r.upsert({'id':'old','process':{'pid':1},'label':'Same'})
        thread=threading.Thread(target=d.run); thread.start()
        try:
            deadline=time.monotonic()+2
            while not d.presented[0] and time.monotonic()<deadline: time.sleep(.01)
            r.remove('old'); r.upsert({'id':'new','process':{'pid':2},'label':'Same'})
            deadline=time.monotonic()+2
            while d.presented[0]['id']!='new' and time.monotonic()<deadline: time.sleep(.01)
            d.press(0,True)
            self.assertEqual(q.get_nowait()['id'],'new')
        finally:
            stop.set(); thread.join(3)
