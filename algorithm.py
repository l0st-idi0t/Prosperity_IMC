from typing import Dict, List
from datamodel import OrderDepth, Position, TradingState, Order


class Trader:

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        result = {}

        for product in state.order_depths.keys():
            if product == 'PEARLS':
                order_depth: OrderDepth = state.order_depths[product]
                orders: list[Order] = []

                acceptable_buy_price = 9999
                acceptable_sell_price = 10001

                # We buy here
                # We look at SELL orders (Negative volume)
                if len(order_depth.sell_orders) > 0:
                    best_ask = min(order_depth.sell_orders.keys())
                    best_ask_volume = order_depth.sell_orders[best_ask]

                    # Makes sure that the ask is less than or equal to our acceptable_buy_price
                    # Also makes sure that our position is within range
                    if best_ask <= acceptable_buy_price and state.position[product] >= -20 and state.position[product] <= 20:
                        print("BUY", str(-best_ask_volume) + "x", best_ask)
                        orders.append(Order(product, best_ask, -best_ask_volume))

                        # Our position increases by the volume
                        state.position[product] += -best_ask_volume;

                # We sell here
                # We look at BUY orders (Positive volume)
                if len(order_depth.buy_orders) > 0:
                    best_bid = max(order_depth.buy_orders.keys())
                    best_bid_volume = order_depth.buy_orders[best_bid]

                    # Makes sure that the bid is greater than or equal to our acceptable_sell_price,
                    # Also makes sure that our position is within range
                    if best_bid >= acceptable_sell_price and state.position[product] >= -20 and state.position[product] <= 20:
                        print("SELL", str(best_bid_volume) + "x", best_bid)
                        orders.append(Order(product, best_bid, -best_bid_volume))

                        # Our position decreases by the volume
                        state.position[product] += -best_bid_volume;

                result[product] = orders

        return result
