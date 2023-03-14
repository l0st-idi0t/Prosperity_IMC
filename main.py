from algorithm import *


def __main__():
    test = Trader()
    tradingState = TradingState(0, {}, {}, {}, {}, {}, {})

    print(test.run(tradingState))


if __name__ == "__main__":
    __main__()
