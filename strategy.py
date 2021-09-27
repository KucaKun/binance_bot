import importlib, os
from datetime import datetime
from utils.enums import Decision
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
        self.indicator_values = []

    def load_data(self, x, y):
        self.klines = y
        self.times = x

    def calculate_decision(self, data):
        """Decide whether to buy or sell.
        Returns decision and amount"""
        raise NotImplementedError

    # region running the strategy
    def _buy(self, buy_time, price, fiat_amount):
        crypto_amount = fiat_amount / price
        cost = price * crypto_amount
        if self.balance_fiat > cost:
            self.balance_crypto += crypto_amount
            self.balance_fiat -= cost
            self.buys.append(
                [
                    buy_time,
                    price,
                    crypto_amount,
                    cost,
                    self.balance_fiat,
                    self.balance_crypto,
                ]
            )

    def _sell(self, sell_time, price, crypto_amount):
        if self.balance_crypto > crypto_amount:
            profit = price * crypto_amount
            self.balance_fiat += profit
            self.balance_crypto -= crypto_amount
            self.sells.append(
                [
                    sell_time,
                    price,
                    crypto_amount,
                    profit,
                    self.balance_fiat,
                    self.balance_crypto,
                ]
            )

    def _calculate_results(self):
        self.fiat_profit = self.balance_fiat - self.start_fiat
        self.crypto_profit = self.balance_crypto - self.start_crypto
        self.overall_profit = self.fiat_profit + self.crypto_profit * self.klines[-1, 4]
        self.profit_percentage = self.overall_profit - (
            self.start_fiat + self.start_crypto * self.klines[0, 4]
        )

        self.hodl_profit = round(
            self.sells[-1][1] * (self.start_fiat / self.buys[0][1]) - self.start_fiat, 2
        )
        lucky_sell = self.sells[np.argmax(self.sells[:, 1])]
        self.lucky_hodl_profit = round(
            lucky_sell[1] * (self.start_fiat / self.buys[0][1]) - self.start_fiat, 2
        )

    def run_strategy(self):
        """
        Iterates over whole dataset to fill buys and sells
        """
        for i in range(len(self.times)):
            decision, amount = self.calculate_decision(self.klines[0:i])
            transaction_time = self.times[i]
            transaction_price = self.klines[i, 4]
            if decision == Decision.BUY:
                self._buy(transaction_time, transaction_price, amount)
            elif decision == Decision.SELL:
                self._sell(transaction_time, transaction_price, amount)
            elif decision == Decision.WAIT:
                pass
        self.buys = np.array(self.buys)
        self.sells = np.array(self.sells)

        self._calculate_results()

    # endregion
    # region plotting
    def _plot_price_over_time(self, ax):
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=len(self.times) // 10))
        ax.plot(self.times, self.klines[:, 4], color="blue")
        self.legend.append("ETHBUSD")

    def _plot_indicator_over_time(self, ax):
        # use super to call it and then plot
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=len(self.times) // 10))

    def _plot_details(self, ax):
        texts = []
        coords = []
        for buy, sell in zip(self.buys, self.sells):
            date_time = mdates.date2num(buy[0])
            fiat, crypto = buy[-2 : len(buy)]
            text = f"Buy: \${str(round(buy[3], 2))} Balance: \${str(round(fiat, 2))} + {str(round(crypto, 5))}ETH"
            coord = (date_time, buy[1])
            texts.append({"buy": text})
            coords.append({"buy": coord})

            date_time = mdates.date2num(sell[0])
            fiat, crypto = sell[-2 : len(sell)]
            text = f"Sell: \${str(round(sell[3], 2))} Balance: \${str(round(fiat, 2))} + {str(round(crypto, 5))}ETH"
            coord = (date_time, sell[1])
            texts[-1]["sell"] = text
            coords[-1]["sell"] = coord

        annotation = ax.annotate(
            "",
            (0, 0),
            xytext=(0, -15),
            textcoords="offset points",
            color="white",
            fontsize="medium",
            backgroundcolor="#000000AF",
        )

        def update_annotation(scatter, index, name):
            i = index["ind"][0]
            x, y = scatter.get_offsets()[i]
            annotation.xy = coords[i][name]
            annotation.set_text(texts[i][name])

        def hover(event):
            vis = annotation.get_visible()
            if event.inaxes == ax:
                buy_contains, buy_index = self.scatter_buy.contains(event)
                sell_contains, sell_index = self.scatter_sell.contains(event)
                if buy_contains:
                    update_annotation(self.scatter_buy, buy_index, "buy")
                    annotation.set_visible(True)
                    self.fig.canvas.draw_idle()
                elif sell_contains:
                    update_annotation(self.scatter_sell, sell_index, "sell")
                    annotation.set_visible(True)
                    self.fig.canvas.draw_idle()

                else:
                    if vis:
                        annotation.set_visible(False)
                        self.fig.canvas.draw_idle()

        self.fig.canvas.mpl_connect("motion_notify_event", hover)

    def _plot_decision_markers(self, ax):
        buy_marker_style = matplotlib.markers.MarkerStyle(marker="^")
        sell_marker_style = matplotlib.markers.MarkerStyle(marker="v")
        offset_buys = (
            self.buys[:, 1] - (self.buys[:, 1].max() - self.buys[:, 1].min()) / 100
        )
        offset_sells = (
            self.sells[:, 1] + (self.sells[:, 1].max() - self.sells[:, 1].min()) / 100
        )
        self.scatter_buy = ax.scatter(
            self.buys[:, 0], offset_buys, marker=buy_marker_style, color="green"
        )
        self.scatter_sell = ax.scatter(
            self.sells[:, 0], offset_sells, marker=sell_marker_style, color="red"
        )
        self._plot_details(ax)

    def _plot_profit_percentages(self, ax):
        for i, sell in enumerate(self.sells):
            date_time = mdates.date2num(sell[0])
            previous_balance = (
                self.sells[i - 1][-2] + self.sells[i - 1][-1] * self.sells[i - 1][1]
            )
            current_balance = sell[-2] + sell[-1] * sell[1]
            profit_percentage = (
                (current_balance - previous_balance) / current_balance * 100
            )
            if profit_percentage < 0:
                color = "red"
            else:
                color = "green"
            coords = (date_time, sell[1])
            ax.annotate(
                str(round(profit_percentage, 2)) + "%",
                coords,
                xytext=(4, 4),
                textcoords="offset points",
                color=color,
                fontsize="medium",
                fontweight="bold",
                backgroundcolor="#FFFFFF60",
            )

    def _plot_hodl(self, ax):
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=len(self.times) // 10))
        start = (
            mdates.date2num(self.buys[0][0]),
            mdates.date2num(self.sells[-1][0]),
        )
        end = (self.buys[0][1], self.sells[-1][1])
        ax.plot(
            start,
            end,
            color="#a0a0a0f0",
            linewidth=1,
            linestyle="dashed",
        )
        ax.set_title(ax.get_title() + f"\nHold profit would be: \${self.hodl_profit}")
        self.legend.append("Hold")

    def _plot_lucky_hodl(self, ax):
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=len(self.times) // 10))
        lucky_sell = self.sells[np.argmax(self.sells[:, 1])]
        start = (
            mdates.date2num(self.buys[0][0]),
            mdates.date2num(lucky_sell[0]),
        )
        end = (self.buys[0][1], lucky_sell[1])
        ax.plot(
            start,
            end,
            color="#f3e260f0",
            linewidth=1,
            linestyle="dashed",
        )
        ax.set_title(
            ax.get_title() + f"\nLucky hold profit would be: \${self.lucky_hodl_profit}"
        )
        self.legend.append("Lucky hold")

    def plot_strategy_run(self):
        if len(self.buys) and len(self.sells):
            self.times = [mdates.date2num(date_time) for date_time in self.times]

            self.fig, (dax, iax) = plt.subplots(
                2,
                1,
                figsize=(20, 10),
                gridspec_kw={"height_ratios": [3, 1]},
                sharex=True,
            )
            dax.set_title(f"Overall strategy profit: \${round(self.overall_profit, 2)}")
            self.legend = []
            self._plot_hodl(dax)
            self._plot_lucky_hodl(dax)
            self._plot_price_over_time(dax)
            self._plot_profit_percentages(dax)
            self._plot_decision_markers(dax)
            self._plot_indicator_over_time(iax)
            dax.legend(self.legend)
            plt.show()
        else:
            print("Strategy was empty")

    # endregion


class StrategyTest:
    def __init__(self) -> None:
        self.runs = []

    def _prepare_datasets(self):
        datasets = []
        for i in range(1):
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
            print("\tRun", i, "profits:")
            print("\t\t Fiat average profit:", str(run.fiat_profit_percentage) + "%")
            print(
                "\t\t Crypto average profit:", str(run.crypto_profit_percentage) + "%"
            )

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
            names = names.split(" ")

        for name in names:
            strategy_module = importlib.import_module("strategies." + name)
            self.strategy_classes.append(strategy_module.Strategy)

    def test_strategies(self, names=""):
        self._load_strategies(names)
        for strategy_class in self.strategy_classes:
            print("Iterating", strategy_class.__name__)
            self.iterate_strategy(strategy_class)


if __name__ == "__main__":
    test = StrategyTest()
    test.test_strategies("rsi_strategy")
