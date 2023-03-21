import matplotlib.pyplot as plt
import pandas as pd
from algorithm import Trader

from datamodel import *

import time as chronos


def simulate(round: int, day: int, trader: Trader):
    # The file path for the prices and trades of the selected round
    prices_path = f"markets/round_{round}/prices_round_{round}_day_{day}.csv"
    trades_path = f"markets/round_{round}/trades_round_{round}_day_{day}_nn.csv"

    # Data frames for each csv
    df_prices = pd.read_csv(prices_path, sep=';')
    df_trades = pd.read_csv(trades_path, sep=';')

    # Initial values for the time and the state
    prev_time = -1
    state = TradingState(-1, {}, {}, {}, {}, {}, {})

    position = {}
    my_trades = {}
    market_trades = {}
    observations = {}

    pnl = 0
    cash = 0
    historical_pnl = list()
    historical_cash = list()
    last_prices = {}

    # Iterate through each row of the data frame
    for _, row in df_prices.iterrows():
        # The current time and 
        time = row["timestamp"]
        product = row["product"]

        # Initialize product
        if product not in position:
            position[product] = 0
            my_trades[product] = []
            market_trades[product] = []


        # Default listing
        listing = {product: {"symbol": product, "product": product, "denomination": product}}

        # Setup order depth
        depth = {product: OrderDepth()}
        for i in range(1, 4):
            if row[f"bid_price_{i}"] > 0: depth[product].buy_orders [row[f"bid_price_{i}"]] = row[f"bid_volume_{i}"]
            if row[f"ask_price_{i}"] > 0: depth[product].sell_orders[row[f"ask_price_{i}"]] = -row[f"ask_volume_{i}"]

        # Get all trades that happened at this time
        trades = df_trades[df_trades['timestamp'] == time]
        for _, trade in trades.iterrows():
            # Get the product that is being traded
            symbol = trade['symbol']
            # Skip any trades that aren't for our product
            if symbol != product: continue
            # Create a new trade object and add it to market_trades
            t = Trade(symbol, trade['price'], trade['quantity'], trade['buyer'], trade['seller'], time)
            market_trades[product].append(t)

        # If time has elapsed
        if time != prev_time and prev_time != -1:

            # Update the current state's timestamp
            state.timestamp = time

            # Act on our trader's action
            output = trader.run(state)

            # Loop through each product
            for product in output:
                # Process our trader's orders
                for order in output[product]:
                    # Get order levels, { Price: Quantity }
                    levels = state.order_depths[order.symbol]

                    if order.quantity < 0:
                        # Sell/Ask order - Need corresponding buy
                        volume = abs(order.quantity)
                        total_volume = volume

                        while len(levels.buy_orders):
                            # Get the best bid (Person willing to pay the most)
                            best_bid = max(levels.buy_orders.keys())

                            # Keep track of the last price
                            last_prices[product] = best_bid

                            # If the best bid does not match the order price
                            if best_bid < order.price:
                                break

                            # The amount that is exchanged
                            taken_volume = min(volume, levels.buy_orders[best_bid])
                            
                            # Update volumes and position by taken_volume
                            volume -= taken_volume
                            levels.buy_orders[best_bid] -= taken_volume
                            position[product] -= taken_volume

                            # Update cash
                            cash += best_bid * taken_volume/total_volume

                            # Add the trade to completed trades
                            my_trades[product].append(Trade(product, best_bid, taken_volume, None, "self", prev_time))

                            # If volume left is 0
                            if volume <= 0: break
                            # Delist the buy order if it is fulfilled
                            if levels.buy_orders[best_bid] <= 0: del levels.buy_orders[best_bid]
                    else:
                        # Buy/Bid order - Need corresponding sell
                        volume = abs(order.quantity)
                        total_volume = volume

                        while len(levels.sell_orders):
                            # Get the best ask (Person willing to pay the most)
                            best_ask = min(levels.sell_orders.keys())

                            # Keep track of the last price
                            last_prices[product] = best_ask

                            # If the best ask does not match the order price
                            if best_ask > order.price:
                                break

                            # The amount that is exchanged
                            taken_volume = -min(volume, levels.sell_orders[best_ask])

                            # Update volumes and position by taken_volume
                            volume -= taken_volume
                            levels.sell_orders[best_ask] -= taken_volume
                            position[product] += taken_volume

                            # Update cash
                            cash -= best_ask * taken_volume/total_volume

                            # Add the trade to completed trades
                            my_trades[product].append(Trade(product, best_ask, taken_volume, "self", None, prev_time))

                            # If volume left is 0
                            if volume <= 0: break
                            # Delist the sell order if it is fulfilled
                            if levels.sell_orders[best_ask] <= 0: del levels.sell_orders[best_ask]

            # Update the trading state
            state = TradingState(time, listing, depth, my_trades, market_trades, position, observations)
        else:
            state.listings[product] = listing[product]
            state.order_depths[product] = depth[product]

        for product in position:
            if abs(position[product]) > 20:
                print(f"Position limit for {product} violated - {position[product]}")
                raise RuntimeError()

        pnl = cash + sum(position[product] * last_prices[product] if product in last_prices else 0 for product in position)
        historical_pnl.append(pnl)
        historical_cash.append(cash)
        prev_time = time

    plt.plot(df_prices["timestamp"], historical_cash)
    plt.show()



if __name__ == '__main__':
    simulate(1, 0, Trader())
