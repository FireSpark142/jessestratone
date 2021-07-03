from jesse.indicators.avgprice import avgprice
from jesse.indicators.midprice import midprice
from jesse.indicators.obv import obv
from jesse.indicators.trix import trix
from jesse.strategies import Strategy
import jesse.indicators as ta
from jesse import utils


class stratv1(Strategy):

    def filters(self):
        return [
            self.stop_loss_entry_filter,
            self.take_profit_entry_filter,
            self.zero_money_entry_filter,
            self.qty_less_than_or_zero,
        ]

    def stop_loss_entry_filter(self):
       return (self.hp['stop'] * self.price) <= self.high
    
    def take_profit_entry_filter(self):
       return (self.hp['profit'] * self.price) >= self.high

    def zero_money_entry_filter(self):
       return (self.available_margin > 0) and (self.capital > 0)
    
    def qty_less_than_or_zero(self):
        return (utils.size_to_qty(self.capital, self.high, fee_rate=self.fee_rate)) > 0
    
    
    @property
    def plus(self):
        dm = ta.dm(self.candles, 14)
        return dm.plus

    @property
    def minus(self):
        dm = ta.dm(self.candles, 14)
        return dm.minus

    @property
    def trixd(self):
        t = ta.t3(self.get_candles('Binance', 'NANO-USDT', '1D'))
        if self.high > t:
                return True
        else:
            return False    

    @property
    def trixdiverg(self):
        td = ta.trix(self.get_candles('Binance', 'NANO-USDT', '1D'))
        th = ta.trix(self.get_candles('Binance', 'NANO-USDT', '1h'))

        if th > td:
                return True
        else:
            return False

    def should_long(self) -> bool:
        if ((self.plus > self.minus) and (self.trixd == True) or (self.plus > self.minus) and (self.trixdiverg == True)):
           return True
        
    def should_short(self) -> bool:
        if (self.plus < self.minus) and self.low < ta.tema(self.candles):
           return True

    def should_cancel(self) -> bool:
        return True

    def go_long(self):
        entry = self.high
        stop = self.price * .95
        profit = self.price * 1.3
        qty = utils.size_to_qty(self.capital, self.high, fee_rate=self.fee_rate)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, profit

    def go_short(self):
        qty = utils.size_to_qty(self.capital, self.high, fee_rate=self.fee_rate)

        self.sell = qty, self.low
        
    def update_position(self):
       qty = self.position.qty
       
       if self.is_long and (self.plus < self.minus):
          self.liquidate()   
       if self.is_long and (self.position.pnl_percentage < -5):
          self.liquidate()
       if self.is_long and ta.rsi(self.candles) > 40:
          self.liquidate()
       if self.is_short and (self.position.pnl_percentage < -5):
          self.liquidate() 
                 

