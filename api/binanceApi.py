# Api Key: Ttzpi4PEcHkWCAImsDRp9O5s0kaYKFeunbuqaExVfv8NysgFCVBcSwqpXoc8q8xv
from utils.colors import negative, positive
from pprint import pprint
from binance.client import Client
import logging as log
import numpy as np
from datetime import datetime
from matplotlib import pyplot as plt
from api.googleApi import getHistoricalInterest

log.basicConfig(filename="./logs/binance-api.log", level=log.DEBUG)
client = Client(
    "Ttzpi4PEcHkWCAImsDRp9O5s0kaYKFeunbuqaExVfv8NysgFCVBcSwqpXoc8q8xv",
    api_secret="muSXFvuIeFrr6JpvAeVrhdEjEYRrRRuLqYX5tQ87arBegZW5z8B0Aacgqz5aky20",
)

# for key, value in client.get_account().items():
#     if key == "balances":
#         print("Balances:")
#         for balance in value:
#             if float(balance["free"]) != 0 or float(balance["locked"]) != 0:
#                 print("Free:",balance["asset"], positive(balance["free"]), "Locked:", negative(balance["locked"]))
#     else:
#         print(key.capitalize(), ": ", value)

# klines1m = client.get_klines(symbol='BTCUSDT', interval=Client.KLINE_INTERVAL_1MINUTE)
# klines5m = client.get_klines(symbol='BTCUSDT', interval=Client.KLINE_INTERVAL_5MINUTE)
# klines30m = client.get_klines(symbol='BTCUSDT', interval=Client.KLINE_INTERVAL_30MINUTE)
# klines1h = client.get_klines(symbol='BTCUSDT', interval=Client.KLINE_INTERVAL_1HOUR)
# klines1d = client.get_klines(symbol='BTCUSDT', interval=Client.KLINE_INTERVAL_1DAY)
# "Open time",
# "Open",
# "High",
# "Low",
# "Close",
# "Volume",
# "Close time",
# "Quote asset volume",
# "Number of trades",
# "Taker buy base asset volume",
# "Taker buy quote asset volume",
# "Can be ignored"


def getNormalizedPrices(symbol, interval=Client.KLINE_INTERVAL_1HOUR):
    klines1h = client.get_klines(symbol=symbol, interval=interval)
    nKlines = np.array(klines1h)

    def fromTimestamp(x):
        return datetime.fromtimestamp(x / 10 ** 3)

    timestamps = np.vectorize(fromTimestamp)(nKlines[:, 6].astype(np.int64))
    maxPrice = nKlines[:, 4].astype(float).max()
    minPrice = nKlines[:, 4].astype(float).min()
    diff = maxPrice - minPrice
    normalizedPrices = np.vectorize(lambda x: ((x - minPrice) / diff) * 100)(
        nKlines[:, 4].astype(float)
    )
    return normalizedPrices
