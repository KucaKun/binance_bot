from unittest import TestCase
from test_strategy import StrategyTest


class StrategyTesterTestCase(TestCase):
    def setUp(self) -> None:
        self.strategy_tester = StrategyTest()
        return super().setUp()
