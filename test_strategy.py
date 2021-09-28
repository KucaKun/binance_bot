import importlib, os
import re
from colorama.ansi import Fore
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

    def _plot_avg_runs_profit(self, ax):
        average_profit = np.average([run.profit_percentage for run in self.runs])
        x = range(len(self.runs))
        y = [average_profit for run in self.runs]
        ax.plot(x, y, linestyle="dashed", linewidth=1)
        self.legend.append("Average")

    def _plot_separate_runs_profits(self, ax):
        average_profit = np.average([run.profit_percentage for run in self.runs])
        x = range(len(self.runs))
        y = [run.profit_percentage for run in self.runs]
        colors = [RED if bar <= 0 else GREEN for bar in y]
        ax.bar(x, y, edgecolor=TICKS_COLOR, color=colors)
        ax.set_ylabel("%")
        ax.set_xlabel("Run #")
        ax.set_title(
            f"Average run profit percentage is {round(average_profit,2)}%",
            color=TICKS_COLOR,
        )
        self.legend.append("Profit percentage")

    def _plot_summary(self):
        self.fig, rax = plt.subplots(1, 1, figsize=(20, 10), sharex=True)
        self.legend = []
        set_plot_style(self.fig, (rax,))
        self._plot_separate_runs_profits(rax)
        self._plot_avg_runs_profit(rax)
        self.legend.reverse()
        rax.legend(self.legend)
        plt.show()

    def _test_summary(self):
        average_profit = np.average([run.profit_percentage for run in self.runs])
        sum_profit = np.average([run.overall_profit for run in self.runs])
        print(
            "Average strategy profit percentage:", str(round(average_profit, 2)) + "%"
        )
        print(
            f"After giving it {self.args.fiat} {self.to_ticker} every run, you'd now have {round(sum_profit,2)} {self.to_ticker} more!"
        )
        print(
            f"After giving it {self.args.fiat} {self.to_ticker} once at the start and running for the whole time, you'd now have {round(self.joined_runs.overall_profit,2)} {self.to_ticker} more!"
        )
        print(f"Hodl profit would be {self.joined_runs.hodl_profit} {self.to_ticker}!")
        diff = round(self.joined_runs.overall_profit - self.joined_runs.hodl_profit, 2)
        if diff > 0:
            print(
                Fore.GREEN
                + f"Strategy is better than hodl by {abs(diff)} {self.to_ticker}!"
                + Fore.RESET
            )
        else:
            print(
                Fore.RED
                + f"Strategy is worse than hodl by {abs(diff)} {self.to_ticker}!"
                + Fore.RESET
            )

        if not self.args.no_plot:
            self._plot_summary()

    def _run_summary(self, run, i):

        print("Run #", i, end=" ")
        if not run.did_anything:
            print("Did nothing")
            return
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
        return np.flipud(np.load(self.args.dataset_path, allow_pickle=True))

    def iterate_strategy(self, strategy_class):
        """
        Runs the strategy using its variables on many different datasets
        """
        datasets = self._load_datasets()
        giga_times = []
        giga_klines = []
        # Separate runs
        for i, dataset in progressbar(enumerate(datasets)):
            strategy = strategy_class(
                self.args.fiat, self.args.crypto, self.from_ticker, self.to_ticker
            )
            strategy.load_data(*dataset)
            strategy.run_strategy()
            self.runs.append(strategy)
            giga_times += list(dataset[0])
            giga_klines += list(dataset[1])
        for i, run in enumerate(self.runs):
            self._run_summary(run, i)

        # Joined runs
        giga_times = np.array(giga_times)
        giga_klines = np.array(giga_klines)
        strategy = strategy_class(
            self.args.fiat, self.args.crypto, self.from_ticker, self.to_ticker
        )
        strategy.load_data(giga_times, giga_klines)
        strategy.run_strategy()
        if not self.args.no_plot:
            strategy.plot_strategy_run()
        self.joined_runs = strategy

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
        parser.add_argument(
            "--no_plot", action="store_true", help="dont plot", default=False
        )

        self.args = parser.parse_args()
        self._read_dataset_name()
        self.test_strategies(self.args.strategy)


if __name__ == "__main__":
    colorama.init()
    test = StrategyTest()
    test.cli()
