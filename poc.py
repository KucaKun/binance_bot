import matplotlib
from numpy.lib.function_base import average
from api.binanceApi import Client, client
import numpy as np
from utils.plots import plot_klines
from utils.indicators import rsi
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime

# Constants
START_FIAT_BALANCE = 100
RSI_SIZE = 5


# Prepare data
klines1m = client.get_klines(symbol="ETHBUSD", interval=Client.KLINE_INTERVAL_3MINUTE)
klines = np.array(klines1m).astype(float)

# Prepare RSI
rsis = []
for i in range(RSI_SIZE):
    rsis.append(0)
for i in range(RSI_SIZE, 500):
    rsis.append(rsi(klines[0:i, 4], 5))
rsi_low = 10
rsi_high = 90

# prepare times
times = mdates.date2num([datetime.fromtimestamp(int(t) // 1000) for t in klines[:, 0]])

# Prepare buys sells
marker_offset = 2
buys = []
sells = []
profit_percentages = []
buy_costs = []
bought = False

buy_prices = []
balance_crypto = 0
balance_fiat = START_FIAT_BALANCE

for i, indicator in enumerate(rsis):
    if indicator > rsi_high:
        if balance_crypto > 0:
            price = klines[:, 4][i]
            sells.append([times[i], price + marker_offset])
            balance_fiat = balance_crypto * price
            wallet = average(buy_prices) * balance_crypto
            profit = balance_fiat - wallet
            profit_percentage = round(profit / wallet * 100, 2)
            profit_percentages.append(
                {
                    "time": times[i],
                    "price": price,
                    "profit_percentage": str(profit_percentage) + "%",
                }
            )
            balance_crypto = 0
            buy_prices = []
    elif indicator < rsi_low:
        if balance_fiat > 0:
            price = klines[:, 4][i]
            buys.append([times[i], price - marker_offset])
            buy_prices.append(price)
            buy_costs.append(
                {
                    "time": times[i],
                    "price": klines[:, 4].min(),
                    "buy_cost": "$" + str(round(balance_fiat, 2)),
                }
            )
            balance_crypto += balance_fiat / price
            balance_fiat = 0

# Convert the rest crypto to fiat
if balance_crypto > 0:
    balance_fiat = balance_crypto * price
    balance_crypto = 0

profit_sum = round(balance_fiat - START_FIAT_BALANCE, 2)


buys = np.array(buys)
sells = np.array(sells)


# Prepare plot
fig, (dax, iax) = plt.subplots(
    2, 1, figsize=(20, 10), gridspec_kw={"height_ratios": [3, 1]}
)
dax.set_title(f"Overall strategy profit: ${profit_sum}")
dax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
dax.xaxis.set_major_locator(mdates.MinuteLocator(interval=len(times) // 10))
iax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
iax.xaxis.set_major_locator(mdates.MinuteLocator(interval=len(times) // 10))

# plot data
dax.plot(times, klines[:, 4], color="blue")
dax.legend(["ETHBUSD"])

# plot rsi
iax.plot(times, rsis, color="red")
iax.set_title(f"RSI with window size: {RSI_SIZE}")
iax.fill_between(times, 0, rsi_low, color="C0", alpha=0.3)
iax.fill_between(times, rsi_high, 100, color="C0", alpha=0.3)

# plot markers
buy_marker_style = matplotlib.markers.MarkerStyle(marker="^")
sell_marker_style = matplotlib.markers.MarkerStyle(marker="v")
dax.scatter(buys[:, 0], buys[:, 1], marker=buy_marker_style, color="green")
dax.scatter(sells[:, 0], sells[:, 1], marker=sell_marker_style, color="red")

for annotation in buy_costs:
    dax.annotate(
        annotation["buy_cost"],
        (annotation["time"], annotation["price"]),
        color="black",
        fontsize="medium",
    )

for annotation in profit_percentages:
    if annotation["profit_percentage"][0] == "-":
        color = "red"
    else:
        color = "green"
    coords = (annotation["time"], annotation["price"])
    dax.annotate(
        annotation["profit_percentage"],
        coords,
        xytext=(4, 4),
        textcoords="offset points",
        color=color,
        fontsize="large",
        fontweight="bold",
        backgroundcolor="#FFFFFF60",
    )

plt.ion()
plt.show(block=False)
