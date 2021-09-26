from strategy import StrategyBase
from utils.enums import Decision


class Strategy(StrategyBase):
    def calculate_decision(self, data):
        decision = Decision.BUY
        amount = self.balance_crypto
        return decision, amount
