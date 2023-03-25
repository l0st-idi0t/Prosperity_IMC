from typing import Dict, List
from datamodel import OrderDepth, Position, Product, TradingState, Order
from statistics import mean, median

class Trader:
    
    def __init__(self):
        self.profit = 0;
        self.lim = {"PEARLS": 20, "BANANAS": 20, "COCONUTS": 600, "PINA_COLADAS": 300, "BERRIES": 250, "DIVING_GEAR": 50}
        self.r_buys = {}
        self.r_sells = {}

    def pearls_algorithm(self, state: TradingState, order_depth: OrderDepth) -> List[Order]:
        # The product we are trading are pearls
        product = "PEARLS"

        # List of all orders we make
        orders: list[Order] = []

        # Acceptable buy and sell prices
        acceptable_buy_price = 9998
        acceptable_sell_price = 10002

        if state.position.get(product, 0) <= 0:
            # Position is negative, We buy here
            # We look at SELL orders (Negative volume)
            if len(order_depth.sell_orders) > 0:
                best_ask = min(order_depth.sell_orders.keys())
                best_ask_volume = order_depth.sell_orders[best_ask]

                # Makes sure that the ask is less than or equal to our acceptable_buy_price
                if best_ask <= acceptable_buy_price:
                    orders.append(Order(product, best_ask, -best_ask_volume))
        else:
            # Position is positive, We sell here
            # We look at BUY orders (Positive volume)
            if len(order_depth.buy_orders) > 0:
                best_bid = max(order_depth.buy_orders.keys())
                best_bid_volume = order_depth.buy_orders[best_bid]

                # Makes sure that the bid is greater than or equal to our acceptable_sell_price,
                if best_bid >= acceptable_sell_price:
                    orders.append(Order(product, best_bid, -best_bid_volume))

        return orders;

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        result = {}
        cur_buy_means = {}
        cur_sell_means = {}
        
        for sym, order_depth in state.order_depths.items():
            if sym == "PEARLS":
                result = self.pearls_algorithm(state, order_depth);
                return result;
            buy_med = []
            sell_med = []
            for k,v in order_depth.buy_orders.items():
                buy_med += [int(k)]*abs(int(v))
            for k,v in order_depth.sell_orders.items():
                sell_med += [int(k)]*abs(int(v))
            cur_buy_means[sym] = mean(buy_med)
            cur_sell_means[sym] = mean(sell_med)

        for sym in state.listings.keys():
            if sym not in self.r_buys and sym in cur_buy_means:
                self.r_buys[sym] = [cur_buy_means[sym]]
            if sym not in self.r_sells and sym in cur_sell_means:
                self.r_sells[sym] = [cur_sell_means[sym]]
            
            elif sym in self.r_buys and sym in self.r_sells and sym in cur_buy_means and sym in cur_sell_means:
                if len(self.r_buys[sym]) < 50:
                    self.r_buys[sym].append(cur_buy_means[sym])
                elif len(self.r_buys[sym]) == 50:
                    self.r_buys[sym] = self.r_buys[sym][1:] + [cur_buy_means[sym]]
                
                if len(self.r_sells[sym]) < 50:
                    self.r_sells[sym].append(cur_sell_means[sym])
                elif len(self.r_sells[sym]) == 50:
                    self.r_sells[sym] = self.r_sells[sym][1:] + [cur_sell_means[sym]]

        # BUY / SELL #
        results = {}
        for sym in state.listings.keys():
            buy_price = 0
            buy_vol = 0
            sell_price = 0
            sell_vol = 0
            try:
                if len(state.order_depths[sym].buy_orders) > 0:
                    buy_price = min(state.order_depths[sym].sell_orders.keys())
                    buy_vol = state.order_depths[sym].sell_orders[buy_price]

                if len(state.order_depths[sym].sell_orders) > 0:
                    sell_price = max(state.order_depths[sym].buy_orders.keys())
                    sell_vol = state.order_depths[sym].buy_orders[sell_price]
            except: continue
            if sym not in cur_buy_means or sym not in cur_sell_means or sym not in self.r_buys or sym not in self.r_sells or len(self.r_buys[sym]) < 50 or len(self.r_sells[sym]) < 50: continue

            t = []
            s_point = abs(mean(self.r_buys[sym][19:]) - mean(self.r_buys[sym])) <= 0.01
            b_point = abs(mean(self.r_sells[sym][19:]) - mean(self.r_sells[sym])) <= 0.01

            try:
                if sym in state.position.keys():
                    if s_point and mean(self.r_buys[sym][:20]) > mean(self.r_buys[sym]):
                        t.append(Order(sym, sell_price, -sell_vol))
                perc_change = ((mean(self.r_sells[sym][39:49]) - mean(self.r_sells[sym][0:10]))) / mean(self.r_sells[sym][0:10])
                if perc_change > 0:
                    t.append(Order(sym, buy_price, -1))
                results[sym] = t
            except: pass
        return results
