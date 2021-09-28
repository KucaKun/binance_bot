import matplotlib.pyplot as plt


def plotOnTrends(trends, data, name=None):
    plt.title(f"Plot of {str(name)} on trends")
    plt.plot(trends.index, trends, color="red", linestyle="dashed")
    plt.plot(trends.index, data, color="blue")
    plt.grid(True)
    plt.legend(["trends", str(name)])
    plt.ion()


plt.show(block=False)


def dualPlot(data1, data2, name1=None, name2=None):
    plt.title(f"Dual plot {str(name1)}, {str(name2)}")
    plt.plot(range(0, len(data1)), data1, color="red")
    plt.plot(range(0, len(data1)), data2, color="blue")
    plt.grid(True)
    if name1 or name2:
        plt.legend([str(name1), str(name2)])
    plt.ion()


plt.show(block=False)


def plot(data, name=None):
    plt.title(f"Plot for {str(name)}")
    plt.plot(range(0, len(data)), data, color="red")
    plt.grid(True)
    if name:
        plt.legend([str(name)])
    plt.ion()


plt.show(block=False)
