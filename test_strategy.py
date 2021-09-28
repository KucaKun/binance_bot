import importlib, os
from colorama.initialise import colorama_text
import numpy as np
import argparse
from pathlib import Path
from progressbar import progressbar
import colorama
from matplotlib import pyplot as plt
from style import set_plot_style, DEFAULT_LINE_COLOR, BLUE, RED, GREEN, TICKS_COLOR


class StrategyTest:
    def __init__(self) -> None:
        self.runs = []

    def _plot_runs_profits(self, ax):
        x = range(len(self.runs))
        y = [run.profit_percentage for run in self.runs]
        ax.bar(x, y, edgecolor=TICKS_COLOR, color=BLUE)
        ax.legend(["Every run profit percentage"])

    def _plot_summary(self):
        self.fig, dax = plt.subplots(1, 1, figsize=(20, 10), sharex=True)
        set_plot_style(self.fig, [dax])
        self._plot_runs_profits(dax)
        plt.show()

    def _test_summary(self):
        average_profit = np.average([run.profit_percentage for run in self.runs])
        print(
            "Average strategy profit percentage:", str(round(average_profit, 2)) + "%"
        )
        self._plot_summary()

    def _run_summary(self, run, i):
        print("Run #", i, end=" ")
        if run.profit_percentage > 0:
            color = colorama.Fore.GREEN
        else:
            color = colorama.Fore.RED

        print(
            color + "Profit:",
            str(run.profit_percentage) + "%",
            colorama.Fore.RESET,
            end=" ",
        )
        if run.hodl_profit_percentage > 0:
            color = colorama.Fore.GREEN
        else:
            color = colorama.Fore.RED
        print(
            "Hold profit:" + color,
            str(run.hodl_profit_percentage) + "%" + colorama.Fore.RESET,
        )

    def _load_datasets(self):
        return np.load(self.args.dataset_path, allow_pickle=True)

    def iterate_strategy(self, strategy_class):
        """
        Runs the strategy using its variables on many different datasets
        """
        datasets = self._load_datasets()
        for i, dataset in progressbar(enumerate(datasets)):
            strategy = strategy_class(
                self.args.fiat, self.args.crypto, self.from_ticker, self.to_ticker
            )
            strategy.load_data(*dataset)
            strategy.run_strategy()
            self.runs.append(strategy)
        for i, run in enumerate(self.runs):
            self._run_summary(run, i)
        self._test_summary()

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
        file_name = Path(self.args.dataset_path).stem
        dataset_data, _, _ = file_name.split("_")
        self.from_ticker, self.to_ticker, self.interval, _, _ = dataset_data.split("-")

    def cli(self):
        parser = argparse.ArgumentParser(
            description="Test your chosen strategy on a dataset."
        )
        parser.add_argument("strategy", type=str)
        parser.add_argument("dataset_path", type=str)
        parser.add_argument(
            "--fiat", type=int, help="starting fiat balance", default=100
        )
        parser.add_argument(
            "--crypto", type=int, help="starting crypto balance", default=0
        )

        self.args = parser.parse_args()
        self._read_dataset_name()
        self.test_strategies(self.args.strategy)


if __name__ == "__main__":
    colorama.init()
    test = StrategyTest()
    test.cli()
