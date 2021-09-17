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


def rsi(data, length):
    upMoves = []
    downMoves = []
    for i in range(len(data) - length, len(data)):
        if i > 0:
            change = data[i] - data[i - 1]
            if change > 0:
                upMoves.append(change)
                downMoves.append(0)
            else:
                downMoves.append(abs(change))
                upMoves.append(0)
    avgU = sum(upMoves) / length
    avgD = sum(downMoves) / length
    relativeStrength = avgU / avgD
    return 100 - 100 / (1 + relativeStrength)
