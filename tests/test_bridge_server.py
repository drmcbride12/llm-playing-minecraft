import json
import time
import unittest

from llm_playing_minecraft.bridge_server import BridgeController
from llm_playing_minecraft.schema import AgentAction


class BridgeControllerTests(unittest.TestCase):
    def test_manual_command_is_delivered_once(self):
        controller = BridgeController(
            planner=lambda goal, observation, history: AgentAction(
                reason="unused",
                baritone_command="#stop",
            ),
            default_goal="survive",
            auto_plan=False,
        )

        controller.queue_manual_command("client-a", "#mine oak_log")

        first = controller.command_for("client-a", 0)
        second = controller.command_for("client-a", first["command"]["id"])

        self.assertEqual(first["command"]["baritone_command"], "#mine oak_log")
        self.assertIsNone(second["command"])

    def test_observation_auto_plans(self):
        def planner(goal, observation, history):
            self.assertEqual(goal, "collect wood")
            self.assertIn("oak_log", observation)
            return AgentAction(reason="Need logs.", baritone_command="#mine oak_log")

        controller = BridgeController(
            planner=planner,
            default_goal="collect wood",
            auto_plan=True,
            max_workers=1,
        )

        controller.update_observation("client-a", json.dumps({"summary": "oak_log nearby"}))

        command = None
        for _ in range(100):
            command = controller.command_for("client-a", 0)["command"]
            if command:
                break
            time.sleep(0.01)

        self.assertIsNotNone(command)
        self.assertEqual(command["baritone_command"], "#mine oak_log")


if __name__ == "__main__":
    unittest.main()
