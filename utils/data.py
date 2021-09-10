from numpy import diff


def pairedMovement(a, b):
    """If both klines go up, go up."""
    output = [1]
    for i in range(0, len(a)):
        if i == 0:
            continue
        elif a[i - 1] < a[i] and b[i - 1] < b[i]:
            # Go up
            output.append(output[i - 1] + 1)
        elif a[i - 1] > a[i] and b[i - 1] > b[i]:
            output.append(output[i - 1] - 1)
        else:
            output.append(output[i - 1])
    return output


def pairedWave(a, b):
    """If both klines go up, give one."""
    output = []
    for i in range(0, len(a)):
        if i == 0:
            continue
        diffA = a[i] - a[i - 1]
        diffB = b[i] - b[i - 1]
        output.append((diffA + diffB) / 2)
    output.append(output[0])

    return output
