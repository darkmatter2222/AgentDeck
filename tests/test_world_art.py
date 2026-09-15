"""Art regressions: coverage, time, scene ownership and character preservation."""

import unittest
from PIL import Image, ImageDraw
from ocdeck.world_props import prop, _prop
from ocdeck.world_art import sky
from ocdeck.world_catalog import SCENES
from ocdeck.world import World
from ocdeck.world_settings import settings
from ocdeck.world_weather import WeatherService
from ocdeck.jelly import Jelly, DeckGeometry


class ArtworkTests(unittest.TestCase):
    def test_all_objects_have_material_motion_and_repeat_cleanly(self):
        names = {s.prop for s in SCENES.values() if s.prop} | {"icicles"}
        for name in sorted(names):
            with self.subTest(name=name):
                frames = [prop(name, p) for p in range(8)]
                self.assertTrue(all(im.size == (40, 40) and im.getbbox() for im in frames))
                self.assertGreater(len({im.tobytes() for im in frames}), 1)
                self.assertIs(prop(name, 8), frames[0])
        self.assertLessEqual(_prop.cache_info().currsize, 512)

    def test_object_scale_and_previously_aliased_shapes(self):
        def height(name):
            box = prop(name).getbbox()
            return box[3] - box[1]

        self.assertLess(height("acorn"), height("snowman") * 0.6)
        for a, b in (("fan", "pinwheel"), ("snowflake", "icicles"), ("lamp", "lantern"), ("powder", "rangoli")):
            self.assertNotEqual(prop(a).tobytes(), prop(b).tobytes())

    def test_every_atmosphere_moves_without_forced_30_second_reset(self):
        for kind in {s.sky for s in SCENES.values() if s.sky}:
            frames = []
            for p in (0, 3, 9, 17, 33, 65, 239, 240):
                im = Image.new("RGBA", (128, 84))
                sky(ImageDraw.Draw(im), kind, 128, 84, p, "#83e6d4")
                frames.append(im.tobytes())
            with self.subTest(kind=kind):
                self.assertGreater(len(set(frames)), 1)
        # The former int(now*8)%240 introduced a jump in drifting backgrounds.
        im = Image.new("RGBA", (128, 84))
        sky(ImageDraw.Draw(im), "clouds", 128, 84, 0, "#83e6d4")
        later = Image.new("RGBA", (128, 84))
        sky(ImageDraw.Draw(later), "clouds", 128, 84, 240, "#83e6d4")
        self.assertNotEqual(im.tobytes(), later.tobytes())

    def test_all_scenes_at_each_native_size_and_reduced_motion(self):
        for size, rows, cols in ((72, 2, 3), (80, 3, 5), (96, 4, 8)):
            for scene in SCENES:
                with self.subTest(size=size, scene=scene):
                    o = settings(
                        dict(
                            scene_override=scene,
                            auto_location=False,
                            weather=False,
                            captions=False,
                            reduced_motion=True,
                        )
                    )
                    world = World(o, WeatherService(o))
                    jelly = Jelly(DeckGeometry(rows, cols, size, size), seed=2, options={"thoughts": "off"})
                    jelly.settle(0, 0)
                    world.tick(1, jelly)
                    for available in ({0}, {0, 1, rows * cols - 1}):
                        source = jelly.crops(available)
                        snapshots = {k: im.tobytes() for k, im in source.items()}
                        a = world.decorate(1, jelly, source, available)
                        b = world.decorate(19, jelly, source, available)
                        self.assertEqual(set(a), set(b))
                        self.assertTrue(set(a) <= available)
                        for k in a:
                            self.assertEqual(a[k].size, (size, size))
                            self.assertEqual(a[k].tobytes(), b[k].tobytes())
                        self.assertEqual(snapshots, {k: im.tobytes() for k, im in source.items()})
                        # Decorations may never replace opaque character pixels.
                        for k, im in source.items():
                            for y in range(size):
                                for x in range(size):
                                    pixel = im.getpixel((x, y))
                                    if pixel[3] == 255:
                                        self.assertEqual(a[k].getpixel((x, y)), pixel)
                    self.assertEqual(world.decorate(1, jelly, {}, set()), {})

    def test_sun_remains_visible_when_only_bottom_left_key_is_free(self):
        o = settings(dict(scene_override="hot", auto_location=False, weather=False, captions=False, props=False))
        world = World(o, WeatherService(o))
        jelly = Jelly(DeckGeometry(), seed=2)
        jelly.settle(3, 0)
        world.tick(1, jelly)
        frames = world.decorate(1, jelly, {}, {3})
        self.assertIn(3, frames)
        self.assertIsNotNone(frames[3].getbbox())


if __name__ == "__main__":
    unittest.main()
