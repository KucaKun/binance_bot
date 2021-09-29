from style import GREEN, TICKS_COLOR, set_axes_style, set_plot_style
from utils.enums import Decision
import matplotlib.dates as mdates
import matplotlib
import matplotlib.pyplot as plt
import numpy as np


class StrategyBase:
    def __init__(self, start_fiat, start_crypto, from_ticker, to_ticker):
        self.start_fiat = start_fiat
        self.start_crypto = start_crypto

        self.balance_fiat = start_fiat
        self.balance_crypto = start_crypto
        self.avg_buy_price = 0
        self.sells = []
        self.buys = []
        self.from_ticker = from_ticker
        self.to_ticker = to_ticker
        self.ticker = from_ticker + to_ticker

    @property
    def did_anything(self):
        return len(self.buys) and len(self.sells)

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
        fiat_cost = price * crypto_amount
        if self.balance_fiat > fiat_cost:
            old_price = self.balance_crypto * self.avg_buy_price
            new_price = crypto_amount * price
            self.avg_buy_price = (
                (old_price + new_price) / (self.balance_crypto + crypto_amount)
                if old_price != 0
                else price
            )
            self.balance_crypto += crypto_amount
            self.balance_fiat -= fiat_cost
            self.buys.append(
                [
                    buy_time,
                    price,
                    crypto_amount,
                    fiat_cost,
                    self.balance_fiat,
                    self.balance_crypto,
                    self.avg_buy_price,
                ]
            )

    def _sell(self, sell_time, price, crypto_amount):
        if self.balance_crypto > crypto_amount:
            fiat_cost = price * crypto_amount
            self.balance_fiat += fiat_cost
            self.balance_crypto -= crypto_amount

            profit = fiat_cost - self.avg_buy_price * crypto_amount
            self.sells.append(
                [
                    sell_time,
                    price,
                    crypto_amount,
                    fiat_cost,
                    self.balance_fiat,
                    self.balance_crypto,
                    profit,
                ]
            )

    def _calculate_results(self):
        self.start_balance = self.start_fiat + self.start_crypto * self.klines[0, 4]
        self.end_balance = self.balance_fiat + self.balance_crypto * self.klines[-1, 4]

        self.overall_profit = self.end_balance - self.start_balance
        self.profit_percentage = round(
            self.overall_profit / self.start_balance * 100, 2
        )

        if self.did_anything:
            self.hodl_profit = round(
                self.sells[-1][1] * (self.start_fiat / self.buys[0][1])
                - self.start_fiat,
                2,
            )
            lucky_sell = self.sells[np.argmax(self.sells[:, 1])]
            self.lucky_hodl_profit = round(
                lucky_sell[1] * (self.start_fiat / self.buys[0][1]) - self.start_fiat, 2
            )
            self.hodl_profit_percentage = round(
                self.hodl_profit / self.start_balance * 100, 2
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
        self.legend.append(self.ticker)

    def _plot_indicator_over_time(self, ax):
        # use super to call it and then plot
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=len(self.times) // 10))

    def _plot_details(self, ax):
        texts = []
        coords = []
        for buy, sell in zip(self.buys, self.sells):
            date_time = mdates.date2num(buy[0])
            balance = buy[4] + buy[5] * buy[1]
            text = f"Buy: {str(round(buy[3], 2))}{self.to_ticker} Balance: {str(round(balance, 2))}{self.to_ticker}"
            coord = (date_time, buy[1])
            texts.append({"buy": text})
            coords.append({"buy": coord})

            date_time = mdates.date2num(sell[0])
            balance = sell[4] + sell[5] * sell[1]
            text = f"Sell: {str(round(sell[3], 2))}{self.to_ticker} Balance: {str(round(balance, 2))}{self.to_ticker}"
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
        self.legend.append(f"BUY")
        self.scatter_sell = ax.scatter(
            self.sells[:, 0], offset_sells, marker=sell_marker_style, color="red"
        )
        self.legend.append(f"SELL")
        self._plot_details(ax)

    def _plot_profits(self, ax):
        for i, sell in enumerate(self.sells):
            date_time = mdates.date2num(sell[0])
            if sell[-1] < 0:
                color = "red"
            else:
                color = "green"
            coords = (date_time, sell[1])
            ax.annotate(
                "\$" + str(round(sell[-1], 2)),
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
        ax.set_title(
            ax.get_title()
            + f"\nHold profit would be: {self.hodl_profit}{self.to_ticker}"
        )
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
            ax.get_title()
            + f"\nLucky hold profit would be: {self.lucky_hodl_profit}{self.to_ticker}"
        )
        self.legend.append("Lucky hold")

    def _plot_wallet_balance(self, ax):
        ax = ax.twinx()
        set_axes_style([ax])
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=len(self.times) // 10))
        balances = self.sells[:, 4] + self.sells[:, 5] * self.sells[:, 1]
        ax.plot(
            self.sells[:, 0],
            balances,
            color=GREEN,
            linewidth=1,
            linestyle="dotted",
        )
        ax.legend([f"{self.to_ticker} Balance"], loc="lower right")

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
            set_plot_style(self.fig, (dax, iax))
            dax.set_title(
                f"Overall strategy profit: {round(self.overall_profit, 2)}{self.to_ticker}",
                color=TICKS_COLOR,
            )
            self.legend = []
            self._plot_wallet_balance(dax)
            self._plot_hodl(dax)
            self._plot_lucky_hodl(dax)
            self._plot_price_over_time(dax)
            self._plot_profits(dax)
            self._plot_decision_markers(dax)
            self._plot_indicator_over_time(iax)
            dax.legend(self.legend)
            plt.ion()
            plt.show(block=False)
        else:
            print("Strategy was empty")

    # endregion
