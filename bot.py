from abc import ABC, abstractproperty
from utils.enums import Decision


class Bot(ABC):
    def __init__(self, fiat_budget, crypto_budget):
        self.fiat_budget = fiat_budget
        self.crypto_budget = crypto_budget

    @abstractproperty
    def _decision(self):
        """
        Calculates whether to buy, sell or wait.

        Returns:
            Decision enum
        """
        pass

    @abstractproperty
    def _amount(self):
        """
        Calculates the amount of crypto to move.
        """
        pass

    def decide(self, klines):
        """
        Creates a decision of whether to buy or sell and the amount,

        Args:
            klines (list): list of all binance klines, from shortest to longest timespans

        Returns:
            decision, amount

        """
        decision = self._decision
        amount = self._amount

        if decision == Decision.BUY:
            self.fiat_budget -= amount
            self.crypto_budget -= amount * self.currentPrice
        elif decision == Decision.SELL:
            self.fiat_budget += amount * self.currentPrice
            self.crypto_budget -= amount
        elif decision == Decision.WAIT:
            pass

        return decision, self._amount
