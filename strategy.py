from binance.client import Client
from threading import Thread
from utils.enums import Decision
from time import sleep, time


class Strategy:
    def __init__(self, symbol, client, fiat_budget, crypto_budget, test=False):
        self.symbol = symbol
        self.client = client
        self.bot = Bot(fiat_budget, crypto_budget)
        self.test = test
        self.balance = 0

    @property
    def balance_in_fiat(self):
        return self.bot.crypto_budget * self.price + self.bot.fiat_budget

    def get_klines(self):
        return self.client.get_klines(
            symbol=self.symbol, interval=Client.KLINE_INTERVAL_1DAY
        )

    def _iteration(self):
        decision, amount = self.bot.decide(self.klines)
        if decision == Decision.BUY:
            self.fiat_budget -= amount
            self.crypto_budget -= amount * self.price
            if not self.test:
                print("buy")
        elif decision == Decision.SELL:
            self.fiat_budget += amount * self.price
            self.crypto_budget -= amount
            if not self.test:
                print("sell")
        elif decision == Decision.WAIT:
            pass

    def _loop(self):
        while True:
            start = time()
            self.klines = self.get_klines()
            self._iteration()
            duration = time() - start
            if not self.test:
                sleep(60 - duration)

    def start_loop(self):
        self.thread = Thread(target=self.loop)


class TestStrategy:
    def test(self):
        klines = self.get_klines()
        start = 0
        end = len(klines) // 2
        for i in range(len(klines) // 2):
            klines[start : end + i]
            self._iteration(test=True)
