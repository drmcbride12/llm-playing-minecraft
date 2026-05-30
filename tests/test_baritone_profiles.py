import unittest

from llm_playing_minecraft.baritone_profiles import (
    load_baritone_profile,
    render_profile_commands,
)


class BaritoneProfileTests(unittest.TestCase):
    def test_loads_bold_profile(self):
        profile = load_baritone_profile("bold")

        self.assertEqual(profile.name, "bold")
        self.assertIn("#set allowParkour true", profile.commands())
        self.assertIn("#set maxFallHeightNoWater 5", profile.commands())

    def test_renders_commands_without_comments(self):
        profile = load_baritone_profile("bold")
        rendered = render_profile_commands(profile, include_comments=False)

        self.assertIn("#set allowParkour true", rendered)
        self.assertNotIn("# risk_level", rendered)


if __name__ == "__main__":
    unittest.main()
