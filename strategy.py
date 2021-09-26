import importlib, os
from time import sleep, time
from datetime import datetime
import numpy as np
from api.binanceApi import Client, client
import matplotlib.dates as mdates
import matplotlib
import matplotlib.pyplot as plt
from binance.client import Client


class StrategyBase:
    def __init__(self, start_fiat, start_crypto):
        self.start_fiat = start_fiat
        self.start_crypto = start_crypto

        self.balance_fiat = start_fiat
        self.balance_crypto = start_crypto
        self.sells = []
        self.buys = []

        self.after_sell_balances = [start_fiat]

    def load_data(self, x, y):
        self.klines = y
        self.times = x

    def calculate_indicators(self):
        """Fill indicator_decisions and buy/sell_amounts"""
        raise NotImplementedError

    def _buy(self, buy_time, price, crypto_amount):
        cost = price * crypto_amount
        if self.balance_fiat > cost:
            self.buys.append([buy_time, price, crypto_amount, cost])
            self.balance_crypto += crypto_amount
            self.balance_fiat -= cost

    def _sell(self, sell_time, price, crypto_amount):
        if self.balance_crypto > crypto_amount:
            profit = price * crypto_amount
            self.sells.append([sell_time, price, crypto_amount, profit])
            self.balance_fiat += profit
            self.balance_crypto -= crypto_amount
            self.after_sell_balances.append([self.balance_fiat, self.balance_crypto])

    def _calculate_results(self):
        self.fiat_profit = self.balance_fiat - self.start_fiat
        self.crypto_profit = self.balance_crypto - self.start_crypto

        self.fiat_profit_percentage = round(self.fiat_profit / self.start_fiat * 100, 2)
        self.crypto_profit_percentage = round(
            self.crypto_profit / self.start_crypto * 100, 2
        )

    def run_strategy(self):
        """
        Iterates over whole dataset to fill buys and sells
        """
        self.calculate_indicators()
        for i in range(len(self.x)):
            transaction_time = self.x[i]
            transaction_price = self.y[i]
            if self.indicator_decisions[i]:
                amount = self.buy_amounts[i]
                self._buy(transaction_time, transaction_price, amount)
            else:
                amount = self.sell_amounts[i]
                self._sell(transaction_time, transaction_price, amount)
        self.buys = np.array(self.buys)
        self.sells = np.array(self.sells)

        self._calculate_results(self)

    # region plotting
    def _plot_price_over_time(self, ax):
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=len(self.times) // 10))
        ax.plot(self.times, self.klines[:, 4], color="blue")
        ax.legend(["ETHBUSD"])

    def _plot_indicator_over_time(self, ax):
        # use super to call it and then plot
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=len(self.times) // 10))

    def _plot_decision_markers(self, ax):
        buy_marker_style = matplotlib.markers.MarkerStyle(marker="^")
        sell_marker_style = matplotlib.markers.MarkerStyle(marker="v")
        ax.scatter(
            self.buys[:, 0], self.buys[:, 1], marker=buy_marker_style, color="green"
        )
        ax.scatter(
            self.sells[:, 0], self.sells[:, 1], marker=sell_marker_style, color="red"
        )

    def _plot_annotations(self, ax):
        for buy in self.buys:
            ax.annotate(
                str(round(buy[3], 2)) + "$",
                (buy[0], buy[3]),
                color="black",
                fontsize="medium",
            )

        for i, balances in enumerate(self.after_sell_balances):
            fiat, crypto = balances
            ax.annotate(
                str(round(fiat, 2) + "$"),
                (self.buys[i][0], 0),
                xytext=(0, 8),
                textcoords="offset points",
                color="black",
                fontsize="medium",
            )
            ax.annotate(
                str(round(crypto, 2) + "$"),
                (self.buys[i][0], 0),
                xytext=(0, 2),
                textcoords="offset points",
                color="black",
                fontsize="medium",
            )

        for i, sell in enumerate(self.sells):
            profit_percentage = sell[1] / self.after_sell_balances[i][0] * 100
            if profit_percentage < 0:
                color = "red"
            else:
                color = "green"
            coords = (sell[0], sell[1])
            ax.annotate(
                str(round(profit_percentage, 2)) + "%",
                coords,
                xytext=(4, 4),
                textcoords="offset points",
                color=color,
                fontsize="large",
                fontweight="bold",
                backgroundcolor="#FFFFFF60",
            )

    def plot_strategy_run(self):
        self.times = [mdates.date2num(date_time) for date_time in self.buys[:, 0]]

        fig, (dax, iax) = plt.subplots(
            2, 1, figsize=(20, 10), gridspec_kw={"height_ratios": [3, 1]}
        )
        dax.set_title(f"Overall strategy profit: ${self.strategy_profit}")
        self._plot_price_over_time(dax)
        self._plot_indicator_over_time(iax)
        self._plot_annotations(dax)
        plt.show()

    # endregion


class StrategyTest:
    def __init__(self) -> None:
        self.runs = []

    def _prepare_datasets(self):
        datasets = []
        for i in range(5):
            # Prepare data y
            klines1m = client.get_klines(
                symbol="ETHBUSD", interval=Client.KLINE_INTERVAL_3MINUTE
            )
            klines = np.array(klines1m).astype(float)
            # X axis
            times = [datetime.fromtimestamp(int(t) // 1000) for t in klines[:, 0]]
            datasets.append([times, klines])
        return datasets

    def _plot_iterations(self):
        for i, run in enumerate(self.runs):
            print(i, "profits:")
            print("\t Fiat average:", str(run.fiat_profit_percentage) + "%")
            print("\t Crypto average profit:", str(run.crypto_profit_percentage) + "%")

    def iterate_strategy(self, strategy_class):
        """
        Runs the strategy using its variables on many different datasets
        """
        datasets = self._prepare_datasets()
        start_fiat = 100
        start_crypto = 0
        for dataset in datasets:
            strategy = strategy_class(start_fiat, start_crypto)
            strategy.load_data(*dataset)
            strategy.run_strategy()
            strategy.plot_strategy_run()
            self.runs.append(strategy)
        self._plot_iterations()

    def _load_strategies(self, names=""):
        self.strategy_classes = []
        if not names:
            names = [file_name.rstrip(".py") for file_name in os.listdir("strategies")]
        else:
            names.split(" ")

        for name in names:
            strategy_module = importlib.import_module(name, "strategies")
            self.strategy_classes.append(strategy_module.Strategy)

    def test_strategies(self, names=""):
        for strategy_class in self.strategy_classes:
            self.iterate_strategy(strategy_class)
