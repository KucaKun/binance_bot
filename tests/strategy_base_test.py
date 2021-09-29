from unittest import TestCase
from strategies.rsi_strategy import Strategy
from test_strategy import StrategyTest
import numpy as np


class StrategyBaseTestCase(TestCase):
    def setUp(self) -> None:
        self.strategy_tester = StrategyTest()
        self.strategy_tester._parse_args(
            ["rsi_strategy", "./datasets/ETH-BUSD-3m-latest-70_21-09-28_19-46.npy"]
        )
        self.strategy = Strategy(100, 0, "ETH", "BUSD")

        self.datasets = self.strategy_tester._load_datasets()
        giga_times = []
        giga_klines = []
        for i, dataset in enumerate(self.datasets):
            giga_times += list(dataset[0])
            giga_klines += list(dataset[1])
        giga_times = np.array(giga_times)
        giga_klines = np.array(giga_klines)

        self.strategy.load_data(giga_times, giga_klines)
        self.strategy.run_strategy()
        return super().setUp()

    def test_buys_sells(self):
        pass

    def test_profit_percentages(self):
        profits = self.strategy.sells[:, -1]
        unsold_profit = (
            self.strategy.balance_crypto * self.strategy.klines[-1][1]
            - self.strategy.avg_buy_price * self.strategy.balance_crypto
        )
        end_balance = self.strategy.start_fiat + np.sum(profits) + unsold_profit
        self.assertAlmostEqual(self.strategy.end_balance, end_balance, 1)
