from typing import Dict, List
from datamodel import OrderDepth, Position, Product, TradingState, Order


class Trader:


    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        result = {}

        for symbol, listing in state.listings.items():
            if symbol == "PEARLS":
                product_name = listing['product']
                order_depth: OrderDepth = state.order_depths[symbol]
                orders: list[Order] = []

                acceptable_buy_price = 9999
                acceptable_sell_price = 10001


                if state.position.setdefault(product_name, 0) >= 0:
                    # We buy here
                    # We look at SELL orders (Negative volume)
                    if len(order_depth.sell_orders) > 0:
                        best_ask = min(order_depth.sell_orders.keys())
                        best_ask_volume = order_depth.sell_orders[best_ask]

                        # Makes sure that the ask is less than or equal to our acceptable_buy_price
                        # Also makes sure that our position is within range
                        if best_ask <= acceptable_buy_price:
                            print("BUY", str(-best_ask_volume) + "x", best_ask)
                            orders.append(Order(symbol, best_ask, -best_ask_volume))

                        state.position[product_name] += -best_ask_volume;
                else:
                    # We sell here
                    # We look at BUY orders (Positive volume)
                    if len(order_depth.buy_orders) > 0:
                        best_bid = max(order_depth.buy_orders.keys())
                        best_bid_volume = order_depth.buy_orders[best_bid]

                        # Makes sure that the bid is greater than or equal to our acceptable_sell_price,
                        # Also makes sure that our position is within range
                        if best_bid >= acceptable_sell_price:
                            print("SELL", str(best_bid_volume) + "x", best_bid)
                            orders.append(Order(symbol, best_bid, best_bid_volume))

                        state.position[product_name] += best_bid_volume;

                result[symbol] = orders

        return result
