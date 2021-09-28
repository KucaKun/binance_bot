import importlib, os
import numpy as np
import argparse
from pathlib import Path
from progressbar import progressbar


class StrategyTest:
    def __init__(self) -> None:
        self.runs = []

    def _plot_summary(self):
        pass

    def _test_summary(self):
        average_profit = np.average([run.profit_percentage for run in self.runs])
        print(
            "Average strategy profit percentage:", str(round(average_profit, 2)) + "%"
        )

    def _run_summary(self, run, i):
        print("Run #", i)
        print("\tProfit:", str(run.profit_percentage) + "%")
        print("\tHold profit:", str(run.hodl_profit_percentage) + "%")

    def _load_datasets(self):
        return np.load(self.args.dataset_path)

    def iterate_strategy(self, strategy_class, datasets):
        """
        Runs the strategy using its variables on many different datasets
        """
        datasets = self._load_datasets()
        for i, dataset in progressbar(enumerate(datasets)):
            strategy = strategy_class(
                self.fiat, self.crypto, self.from_ticker, self.to_ticker
            )
            strategy.load_data(*dataset)
            strategy.run_strategy()
            self._run_summary(strategy, i)
            self.runs.append(strategy)
        self._test_summary()
        self._plot_summary()

    def _load_strategies(self, names=""):
        self.strategy_classes = []
        if not names:
            names = [file_name.rstrip(".py") for file_name in os.listdir("strategies")]
        else:
            names = names.split(" ")

        for name in names:
            strategy_module = importlib.import_module("strategies." + name)
            self.strategy_classes.append(strategy_module.Strategy)

    def test_strategies(self, names=""):
        self._load_strategies(names)
        for strategy_class in self.strategy_classes:
            print("Iterating", strategy_class.__name__)
            self.iterate_strategy(strategy_class)

    def _read_dataset_name(self):
        # {self.args.from_ticker}-{self.args.to_ticker}-{self.args.interval}-{self.args.dataset_type}-{self.args.size}_{now}
        file_name = Path(self.args.strategy).stem
        dataset_data, date_time = file_name.split("_")
        self.from_ticker, self.to_ticker, self.interval, _, _ = dataset_data.split("-")

    def cli(self):
        parser = argparse.ArgumentParser(
            description="Test your chosen strategy on a dataset."
        )
        parser.add_argument("strategy", type=str)
        parser.add_argument("dataset_path", type=str)
        parser.add_argument("--fiat", type=int, help="starting fiat balance")
        parser.add_argument("--crypto", type=int, help="starting crypto balance")

        self.args = parser.parse_args()
        self._read_dataset_name()
        self.test_strategies(self.args.strategy)


if __name__ == "__main__":
    test = StrategyTest()
    test.cli()
