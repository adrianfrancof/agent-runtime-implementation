import unittest

from arp.loops.control import (
    Evaluation, LoopExhausted, learning_loop, planning_loop, reasoning_loop,
    reflection_loop, validation_loop,
)


class LoopTests(unittest.TestCase):
    def test_reasoning_verifies(self):
        self.assertEqual(reasoning_loop(lambda: 1, lambda x: x + 1, lambda x: x * 2, lambda x: x == 4), 4)

    def test_reflection_retries(self):
        result = reflection_loop(
            0, lambda n: Evaluation(n >= 2, "increase"), lambda n, _: n + 1, attempts=3
        )
        self.assertEqual(result, 2)

    def test_validation_passes_feedback(self):
        seen = []
        def generate(feedback):
            seen.append(feedback)
            return len(seen)
        result = validation_loop(generate, lambda n: Evaluation(n == 2, "retry"), attempts=2)
        self.assertEqual(result, 2)
        self.assertEqual(seen, ["", "retry"])

    def test_planning_replans(self):
        outcome = planning_loop(
            "goal", lambda goal, feedback: feedback or "first",
            lambda plan: plan, lambda result: Evaluation(result == "retry", "retry"), attempts=2
        )
        self.assertEqual(outcome, "retry")

    def test_learning_store_and_adapt(self):
        stored, adapted = [], []
        result = learning_loop(lambda: 3, lambda n: n * 2, stored.append, adapted.append, iterations=2)
        self.assertEqual(result, [6, 6])
        self.assertEqual(stored, adapted)

    def test_exhaustion_and_invalid_bounds(self):
        with self.assertRaises(LoopExhausted):
            validation_loop(lambda _: 1, lambda _: Evaluation(False, "no"), attempts=1)
        with self.assertRaises(ValueError):
            learning_loop(lambda: 1, lambda x: x, lambda _: None, lambda _: None, iterations=0)
