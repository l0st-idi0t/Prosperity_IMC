import matplotlib.pyplot as plt
import pandas as pd

from algorithm import Trader
from datamodel import *


class Simulation:
    def __init__(self):
        # Simulation data
        self.position = {}
        self.my_trades = {}
        self.market_trades = {}
        self.observations = {}
        self.order_depths = {}
        self.listings = {}
        self.resting_orders = {}

        # History
        self.historical_prices = {}
        self.historical_positions = {}

        # Trader's cash values
        self.pnl = 0
        self.historical_pnl = list()
        self.cash = 0
        self.historical_cash = list()

        # Initial values for the time and the state
        self.state = TradingState(0, {}, {}, {}, {}, {}, {})
        self.prev_time = 0

        # Simulation's position limit
        self.position_limit = 20

    def process_orders(self, product: Product, orders: List[Order]):

        # If there are no orders, then don't do anything
        if len(orders) == 0: return

        # Get order depths, { Price: Quantity }
        depth = self.order_depths[product]

        # Copy of buy and sell orders
        buy_orders = depth.buy_orders.copy()
        sell_orders = depth.sell_orders.copy()

        # If there are no market orders, then don't do anything
        if len(sell_orders) + len(buy_orders) == 0: return;

        # Keep track of new last price
        new_last_price = 0

        # Keep track of change in cash and position
        delta_position = 0
        delta_cash = 0
        delta_pnl = 0

        # Going through sell orders
        for order in orders:
            # Get the volume of the order
            volume = abs(order.quantity)
            
            # Sell order
            if order.quantity < 0:
                while len(buy_orders):
                    # Get the best bid (Highest buy price)
                    best_bid = max(buy_orders.keys())

                    # Skip order if the best bid does not match the order price
                    if best_bid < order.price: break

                    # Update new last price
                    new_last_price = best_bid

                    # Change values by transaction volume
                    taken_volume = min(volume, abs(buy_orders[best_bid]))
                    volume -= taken_volume
                    buy_orders[best_bid] -= taken_volume
                    delta_position -= taken_volume

                    # Selling so cash increases
                    delta_cash += best_bid * taken_volume

                    # Delist orders if they are fulfilled
                    if buy_orders[best_bid] == 0: del buy_orders[best_bid]
                    if volume == 0: break

            # Buy order
            else:
                while len(sell_orders):
                    # Get the best ask (Lowest sell price)
                    best_ask = min(sell_orders.keys())

                    # Skip order if the best ask does not match the order price
                    if best_ask > order.price: break

                    # Update new last price
                    new_last_price = best_ask

                    # Change values by transaction volume
                    taken_volume = min(volume, abs(sell_orders[best_ask]))
                    volume -= taken_volume
                    sell_orders[best_ask] += taken_volume
                    delta_position += taken_volume

                    # Buying so cash decreases
                    delta_cash -= best_ask * taken_volume

                    # Delist orders if they are fulfilled
                    if sell_orders[best_ask] == 0: del sell_orders[best_ask]
                    if volume == 0: break

        # If the position change of all orders violates position limit, then reject orders
        if abs(self.position[product] + delta_position) > self.position_limit:
            return

        # Update values
        depth.sell_orders = sell_orders
        depth.buy_orders = buy_orders
        self.position[product] += delta_position
        self.cash += delta_cash

        # Update history
        self.historical_prices[product].append(new_last_price)
        self.historical_positions[product].append(self.position[product])

        # Calculate PNL
        last_price = 0
        if len(self.historical_prices[product]) == 0:
            self.pnl = self.cash
        else:
            self.pnl = self.cash + sum(self.historical_prices[product]) / len(self.historical_prices[product]) * self.historical_positions[product][-1]


            

    # Process actions
    def step(self, trader: Trader):
        # Act on our trader's actions at this time
        output = trader.run(self.state)

        # Loop through each product
        for product in output:

            # Process our trader's orders
            self.process_orders(product, output[product])
            output[product] = []

    def simulate(self, round: int, day: int, trader: Trader):
        # The file path for the prices and trades of the selected round
        prices_path = f"markets/round_{round}/prices_round_{round}_day_{day}.csv"
        trades_path = f"markets/round_{round}/trades_round_{round}_day_{day}_nn.csv"

        # Data frames for each csv
        df_prices = pd.read_csv(prices_path, sep=';')
        df_trades = pd.read_csv(trades_path, sep=';')

        # Iterate through each row of the data frame
        for _, row in df_prices.iterrows():
            # The current time and product being traded
            time = row["timestamp"]
            product = row["product"]

            # Update the current state's timestamp
            self.state.timestamp = time

            # Product initialization
            self.position.setdefault(product, 0)
            self.my_trades.setdefault(product, [])
            self.market_trades.setdefault(product, [])
            self.resting_orders.setdefault(product, [])
            self.historical_prices.setdefault(product, [])
            self.historical_positions.setdefault(product, [])
            self.listings.setdefault(product, Listing(product, product, product))

            # If time has elapsed
            if time != self.prev_time:
                self.step(trader)

            # Setup order depth
            depth = self.order_depths.setdefault(product, OrderDepth())
            for i in range(1, 4):
                if row[f"bid_price_{i}"] > 0: depth.buy_orders[row[f"bid_price_{i}"]] = row[f"bid_volume_{i}"]
                if row[f"ask_price_{i}"] > 0: depth.sell_orders[row[f"ask_price_{i}"]] = -row[f"ask_volume_{i}"]

            # Get all trades that happened at this time
            trades = df_trades[df_trades['timestamp'] == time]

            # Process each of those trades
            for _, trade in trades.iterrows():
                # Get the product that is being traded
                symbol = trade['symbol']

                # Skip any trades that aren't for our product
                if symbol != product: continue

                # Create a new trade object and add it to market_trades
                t = Trade(symbol, trade['price'], trade['quantity'], trade['buyer'], trade['seller'], time)
                self.market_trades[product].append(t)

            # Update the trading state
            self.state = TradingState(time, self.listings, self.order_depths, self.my_trades, self.market_trades, self.position, self.observations)

            # Update historical_cash
            self.historical_cash.append(self.cash)

            # Update historical_pnl
            self.historical_pnl.append(self.pnl)

            # Update prev_time
            self.prev_time = time

        else:
            # Step again after data has been read
            self.step(trader)





        # Output trader's end cash
        print(f"Ending PNL: {self.pnl} seashells")
        print(f"Ending Cash: {self.cash} seashells")

        # Show cash over time
        plt.plot(df_prices["timestamp"], self.historical_pnl)
        plt.show()







if __name__ == '__main__':
    simulation = Simulation();
    simulation.simulate(2, -1, Trader())
