from typing import Dict, List
from datamodel import OrderDepth, Position, Product, TradingState, Order


class Trader:
    
    def __init__(self):
        self.profit = 0;


    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        result = {}

        for product, order_depth in state.order_depths.items():
            if product == "PEARLS":
                orders: list[Order] = []

                acceptable_buy_price = 9998
                acceptable_sell_price = 10002

                if state.position.get(product, 0) <= 0:
                    # Position is negative, We buy here
                    # We look at SELL orders (Negative volume)
                    if len(order_depth.sell_orders) > 0:
                        best_ask = min(order_depth.sell_orders.keys())
                        best_ask_volume = order_depth.sell_orders[best_ask]

                        # Makes sure that the ask is less than or equal to our acceptable_buy_price
                        # Also makes sure that our position is within range
                        if best_ask <= acceptable_buy_price:
                            orders.append(Order(product, best_ask, -best_ask_volume))
                else:
                    # Position is positive, We sell here
                    # We look at BUY orders (Positive volume)
                    if len(order_depth.buy_orders) > 0:
                        best_bid = max(order_depth.buy_orders.keys())
                        best_bid_volume = order_depth.buy_orders[best_bid]

                        # Makes sure that the bid is greater than or equal to our acceptable_sell_price,
                        # Also makes sure that our position is within range
                        if best_bid >= acceptable_sell_price:
                            orders.append(Order(product, best_bid, -best_bid_volume))

                result[product] = orders

        return result
