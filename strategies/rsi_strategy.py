from style import BLUE, RED, TICKS_COLOR
from strategy import StrategyBase
from utils.enums import Decision
from utils.indicators import rsi
import numpy as np


class Strategy(StrategyBase):
    def __init__(self, start_fiat, start_crypto, from_ticker, to_ticker):
        self.min_transaction = 10

        self.rsi_window_size = 10
        self.rsi_low = 30
        self.rsi_high = 80
        self.min_factor = 0.3

        # Restrainers
        self.max_vol_rsi = 46
        self.accepted_loss_percent = 2

        self.rsi_values = []
        self.vol_rsi_values = []
        super().__init__(start_fiat, start_crypto, from_ticker, to_ticker)

    def calculate_decision(self, data):
        decision = Decision.WAIT
        amount = 0

        if len(data) < self.rsi_window_size:
            rsi_value = 50
        else:
            rsi_value = rsi(data[:, 4], self.rsi_window_size)
        self.rsi_values.append(rsi_value)

        if len(data) < self.rsi_window_size:
            volume_rsi_value = 50
        else:
            volume_rsi_value = rsi(data[:, 5], self.rsi_window_size * 4)
        self.vol_rsi_values.append(volume_rsi_value)

        if not len(data):
            return decision, amount

        volume = data[-1][5]
        avg_volume = np.average(data[:, 5])
        if volume_rsi_value < self.max_vol_rsi:
            if rsi_value > self.rsi_high:
                if self.balance_crypto > 0:
                    decision = Decision.SELL
                    diff_percent = (rsi_value - self.rsi_high) / (100 - self.rsi_high)
                    factor = self.min_factor + diff_percent * (1 - self.min_factor)
                    amount = self.balance_crypto * factor
                    if amount < self.min_transaction / data[-1, 4]:
                        decision = Decision.WAIT

            elif rsi_value < self.rsi_low:
                if self.balance_fiat > 0:
                    decision = Decision.BUY
                    diff_percent = (self.rsi_low - rsi_value) / self.rsi_low
                    factor = self.min_factor + diff_percent * (1 - self.min_factor)
                    amount = self.balance_fiat * factor
                    if amount < self.min_transaction:
                        decision = Decision.WAIT

        # risk management
        if self.avg_buy_price != 0 and decision == Decision.WAIT:
            current_price = data[-1][4]
            current_loss_percentage = 100 - (
                (current_price - self.avg_buy_price) / current_price * 100
            )
            if current_loss_percentage > self.accepted_loss_percent:
                decision = Decision.SELL
                amount = self.balance_crypto

        return decision, amount

    def _plot_indicator_over_time(self, ax):
        super()._plot_indicator_over_time(ax)
        ax.plot(self.times, self.rsi_values, color=RED, linewidth=1)
        ax.plot(self.times, self.vol_rsi_values, color=BLUE, linewidth=1)
        ax.set_title(f"RSI with window size: {self.rsi_window_size}", color=TICKS_COLOR)
        ax.fill_between(self.times, 0, self.rsi_low, color="C0", alpha=0.3)
        ax.fill_between(self.times, self.rsi_high, 100, color="C0", alpha=0.3)
