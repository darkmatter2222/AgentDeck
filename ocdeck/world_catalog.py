"""Declarative, individually switchable scene recipes. No I/O or mutable artwork."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Scene:
    title: str
    group: str
    sky: str = ""
    prop: str = ""
    costume: str = ""
    action: str = "dance"
    color: str = "#83e6d4"
    words: str = ""


SCENES = {
    "sky_fireworks": Scene("Sky fireworks", "july4", "fireworks", "rocket", action="cheer", color="#ff8090"),
    "ground_fountain": Scene("Ground fountain", "july4", "fountain", "fountain", action="applaud", color="#ffd280"),
    "smoke_bombs": Scene("Color smoke", "july4", "smoke", "canister", action="look_up", color="#c4a7ff"),
    "thanksgiving_table": Scene("A feast to share", "thanksgiving", prop="feast", action="nod", color="#e5a15c"),
    "thanksgiving_bite": Scene(
        "One more bite", "thanksgiving", prop="pie", action="bob", words="Yum!", color="#e5a15c"
    ),
    "christmas_lights": Scene("String the lights", "christmas", "lights", "tree", "elf", "wave"),
    "christmas_santa": Scene("Santa Jelly", "christmas", "snow", "gift", "santa", "cheer", "#ff8090"),
    "christmas_elf": Scene("Workshop elf", "christmas", "lights", "gift", "elf", "applaud"),
    "christmas_snow": Scene("Snowy Christmas", "christmas", "snow", "snowman", "scarf", "wave"),
    "holi_colors": Scene("Holi colors", "holi", "confetti", "powder", action="spin", color="#ff70ce"),
    "easter_hunt": Scene("Egg hunt", "easter", prop="eggs", costume="bunny", action="edge_peek", color="#c4a7ff"),
    "ghost_hover": Scene("Little ghost", "halloween", "stars", "pumpkin", "ghost", "look_up", "#dbfff1"),
    "skeleton_dance": Scene("Skeleton dance", "halloween", prop="pumpkin", costume="skeleton", action="dance"),
    "reaper_stroll": Scene("Tiny reaper", "halloween", "fog", "scythe", "reaper", "tiptoe"),
    "masked_jelly": Scene("Masquerade", "halloween", prop="candy", costume="mask", action="wave", color="#c4a7ff"),
    "rain": Scene("Rainy day", "rain", "rain", "puddle", "umbrella", "look_up", "#69bfff"),
    "snow": Scene("Snow day", "snow", "snow", "snowman", "scarf", "cheer"),
    "hot": Scene("Feeling the heat", "hot", "sun", "fan", "sweat", "rest", "#ffd280"),
    "cloudy": Scene("Cloud watching", "cloudy", "clouds", action="look_up"),
    "wind": Scene("Windy day", "wind", "wind", "windsock", action="lean_back"),
    "storm": Scene("Thunderstorm", "storm", "rain", "cloud", "umbrella", "retreat", "#c4a7ff"),
    "fog": Scene("Foggy morning", "fog", "fog", "lamp", action="tiptoe"),
    "tornado": Scene("Toy tornado", "demo", "tornado", "windsock", action="retreat"),
    "hurricane": Scene("Toy hurricane", "demo", "hurricane", "cloud", action="lean_back"),
    "straight_line_wind": Scene("Strong wind", "wind", "wind", "leaf", action="lean_back"),
}

# Fifty additional experiences: each combines a concrete motif, movement and context.
EXTRAS = [
    (
        "new_year_countdown",
        "New year stars",
        "newyear",
        "stars",
        "clock",
        "party",
        "cheer",
        "#ffd280",
        "Happy new year!",
    ),
    ("new_year_confetti", "Confetti parade", "newyear", "confetti", "balloon", "party", "dance", "#ff70ce", ""),
    ("valentine_hearts", "Floating hearts", "valentine", "hearts", "heart", "", "wave", "#ff8090", ""),
    ("valentine_letter", "A little kindness", "valentine", "hearts", "letter", "bow", "nod", "#ff8090", "For you!"),
    ("lunar_lanterns", "Lantern evening", "lunar", "lanterns", "lantern", "", "look_up", "#ff8090", ""),
    ("lunar_envelope", "Lucky envelope", "lunar", "stars", "letter", "party", "cheer", "#ffd280", "Good wishes!"),
    ("diwali_diyas", "Diwali lamps", "diwali", "stars", "diya", "", "wave", "#ffd280", ""),
    ("diwali_rangoli", "Rangoli colors", "diwali", "confetti", "rangoli", "", "applaud", "#ff70ce", ""),
    ("eid_crescent", "Crescent evening", "eid", "stars", "crescent", "", "look_up", "#ffd280", "Eid Mubarak!"),
    ("eid_sweets", "Share sweets", "eid", "lanterns", "sweets", "", "nod", "#c4a7ff", ""),
    ("hanukkah_lights", "Festival candles", "hanukkah", "stars", "menorah", "", "wave", "#69bfff", ""),
    ("hanukkah_dreidel", "Dreidel spin", "hanukkah", "", "dreidel", "", "spin", "#69bfff", ""),
    ("st_patrick_clover", "Lucky clover", "patrick", "", "clover", "bow", "cheer", "#59f3c2", ""),
    ("st_patrick_rainbow", "Rainbow end", "patrick", "rainbow", "pot", "", "edge_peek", "#ffd280", ""),
    ("earth_day_seed", "Plant a seed", "earth", "", "seedling", "gardener", "nod", "#59f3c2", "Grow little one!"),
    ("earth_day_globe", "Our little planet", "earth", "stars", "globe", "", "wave", "#69bfff", ""),
    (
        "birthday_cake",
        "Birthday candles",
        "birthday",
        "confetti",
        "cake",
        "party",
        "cheer",
        "#ff70ce",
        "Happy birthday!",
    ),
    ("birthday_balloons", "Birthday balloons", "birthday", "balloons", "gift", "party", "dance", "#c4a7ff", ""),
    ("spring_blossoms", "Blossom breeze", "spring", "petals", "flower", "", "look_up", "#ff8090", ""),
    ("spring_butterfly", "Butterfly visitor", "spring", "butterflies", "flower", "", "wave", "#c4a7ff", ""),
    ("spring_seedling", "Garden morning", "spring", "", "seedling", "gardener", "nod", "#59f3c2", ""),
    ("spring_kite", "Kite afternoon", "spring", "clouds", "kite", "", "look_up", "#ff70ce", ""),
    ("summer_lemonade", "Lemonade break", "summer", "sun", "lemonade", "sunhat", "nod", "#ffd280", ""),
    ("summer_sandcastle", "Sandcastle builder", "summer", "sun", "sandcastle", "sunhat", "applaud", "#e5c180", ""),
    ("summer_beachball", "Beach ball", "summer", "clouds", "beachball", "shades", "cheer", "#69bfff", ""),
    ("summer_fireflies", "Firefly evening", "night", "fireflies", "grass", "", "look_up", "#ffd280", ""),
    ("autumn_leaves", "Leaf drift", "autumn", "leaves", "leaf", "scarf", "wave", "#e5a15c", ""),
    ("autumn_rake", "Leaf pile", "autumn", "leaves", "rake", "", "scoot", "#e5a15c", ""),
    ("autumn_acorn", "Acorn treasure", "autumn", "", "acorn", "", "edge_peek", "#e5c180", ""),
    ("autumn_cocoa", "Cozy cocoa", "autumn", "smoke", "cocoa", "scarf", "rest", "#c4a7ff", ""),
    ("winter_snowangel", "Snow angel", "winter", "snow", "snowangel", "scarf", "dance", "#dbfff1", ""),
    ("winter_snowball", "Snowball play", "winter", "snow", "snowball", "beanie", "cheer", "#69bfff", ""),
    ("winter_icicles", "Icicle sparkle", "winter", "icicles", "snowman", "beanie", "look_up", "#69bfff", ""),
    ("winter_mittens", "Mitten weather", "winter", "snow", "mittens", "scarf", "wave", "#ff8090", ""),
    ("rain_puddle_jump", "Puddle hop", "rain", "rain", "puddle", "boots", "cheer", "#69bfff", ""),
    ("rain_umbrella", "Under my umbrella", "rain", "rain", "flower", "umbrella", "wave", "#c4a7ff", ""),
    ("rain_window", "Rain on the window", "rain", "rain", "window", "", "rest", "#69bfff", ""),
    ("rain_rainbow", "After-rain rainbow", "after_rain", "rainbow", "puddle", "", "cheer", "#ff70ce", ""),
    ("snow_catch", "Catch a snowflake", "snow", "snow", "snowflake", "beanie", "look_up", "#dbfff1", ""),
    ("snow_sled", "Tiny sled", "snow", "snow", "sled", "scarf", "scoot", "#ff8090", ""),
    ("hot_popsicle", "Popsicle pause", "hot", "sun", "popsicle", "sweat", "nod", "#ff70ce", ""),
    ("hot_fan", "Personal fan", "hot", "wind", "fan", "shades", "rest", "#69bfff", ""),
    ("wind_pinwheel", "Pinwheel spin", "wind", "wind", "pinwheel", "", "spin", "#ff70ce", ""),
    ("wind_scarf", "Scarf in the breeze", "wind", "leaves", "windsock", "scarf", "lean_back", "#c4a7ff", ""),
    ("night_stargazing", "Stargazing", "night", "stars", "telescope", "", "look_up", "#c4a7ff", ""),
    ("night_meteor", "A shooting star", "night", "meteor", "crescent", "", "cheer", "#ffd280", ""),
    ("night_lullaby", "Moonlight rest", "night", "stars", "music", "nightcap", "rest", "#69bfff", ""),
    ("morning_sunrise", "Good morning", "morning", "sunrise", "flower", "", "reform", "#ffd280", "Morning!"),
    ("halloween_witch", "Friendly witch", "halloween", "stars", "broom", "witch", "wave", "#c4a7ff", ""),
    ("christmas_train", "Gift train", "christmas", "lights", "train", "elf", "cheer", "#ff8090", ""),
]
SCENES.update({row[0]: Scene(*row[1:]) for row in EXTRAS})
GROUPS = {s.group for s in SCENES.values()}
