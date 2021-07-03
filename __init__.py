from jesse.strategies import Strategy
import jesse.indicators as ta
from jesse import utils


class stratv1(Strategy):

    def filters(self):
        #Filters we use to ensure a trade does not happen under certain conditions
        return [
            self.stop_loss_entry_filter,
            self.take_profit_entry_filter,
            self.zero_money_entry_filter,
            self.qty_less_than_or_zero,
        ]

    def stop_loss_entry_filter(self):
        #Here we ensure that the stop-loss is lower than or equal to the high of the candle, as it being higher causes the script to error out
       return (self.hp['stop'] * self.price) <= self.high
    
    def take_profit_entry_filter(self):
         #Here we ensure that the take-profit is higher than or equal to the high of the candle, as it being lower causes the script to error out
       return (self.hp['profit'] * self.price) >= self.high

    def zero_money_entry_filter(self):
        #Here we check to see if we have avaliable margin AND capital.
       return (self.available_margin > 0) and (self.capital > 0)
    
    def qty_less_than_or_zero(self):
        #This filter is to ensure our qty is greater than 0, as a negative qty is not possible.
        return (utils.size_to_qty(self.capital, self.high, fee_rate=self.fee_rate)) > 0
    
    
    @property
    def plus(self):
        #We pull the directional movement indicator and assign it to dm
        dm = ta.dm(self.candles, 14)
        #We return the plus value from the named tuple given by dm
        return dm.plus

    @property
    def minus(self):
        #Once again pull the directional movement indicator and assign it to dm
        dm = ta.dm(self.candles, 14)
        #Now we return the plus value from the named tuple given by dm
        return dm.minus

    @property
    def t3(self):
        #We assign the t3 indicator to the variable t, and importantly, we pull in 1D data, not the default 1h route we use
        t = ta.t3(self.get_candles('Binance', 'NANO-USDT', '1D'))
        #A simple if else, if the high of the current candle is greater than t, we return True, else False.
        if self.high > t:
                return True
        else:
            return False    

    @property
    def trixdiverg(self):
        #Here we take the same indicator, trix and two different time frames, and assign each to the variables th and td respectively.
        td = ta.trix(self.get_candles('Binance', 'NANO-USDT', '1D'))
        th = ta.trix(self.get_candles('Binance', 'NANO-USDT', '1h'))
        #We check if th is greater than td, by doing this we are checking if the 1h rate of change of a triple exponentially smoothed average, is greater than the rate of change for the day.
        #This allows us to find upward movement before it happens on the longer term set of candles by using the shorter term candle set.
        #The reason we use trix, is simply because it's shown to have a positive correlation across 12 years of data with stocks and we wanted to impliment a way to utilize it with crypto.
        #Source: Technical Market Indicators Analysis and Performance by Richard J. Bauer Jr. PhD. 1999
        if th > td:
                return True
        else:
            return False

    def should_long(self) -> bool:
        #Here we check if the DM+ indicator is currently above the negative and our t3 function returns true, OR the DM+ indicator is currently above the DM- and our trixdiverg function returns true.
        if ((self.plus > self.minus) and (self.t3 == True) or (self.plus > self.minus) and (self.trixdiverg == True)):
           return True
        
    def should_short(self) -> bool:
        #If the DM+ is LOWER than DM-, and our current low, is LOWER then the triple exponentially smoothed average for the 1h candles.
        if (self.plus < self.minus) and self.low < ta.tema(self.candles):
           return True

    def should_cancel(self) -> bool:
        #We don't like holding stuff that isn't going through, just cancel it and try again.
        return True

    def go_long(self):
        #Here we define some easy variables, we assign out entry point, stop-loss and our take-profit, as well as our qty.
        entry = self.high
        stop = self.price * .95
        profit = self.price * 1.3
        #We use utils.size_to_qty, and tell it to use all our money to get the qty.
        qty = utils.size_to_qty(self.capital, self.high, fee_rate=self.fee_rate)
        #Now we assign our buy, stop_loss and take_profit to qty and their respective variable we just defined.
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, profit

    def go_short(self):
        #We use utils.size_to_qty, and tell it to use all our money to get the qty.
        qty = utils.size_to_qty(self.capital, self.high, fee_rate=self.fee_rate)
        #We assign our sell value to the low of the current candle.
        self.sell = qty, self.low
        
    def update_position(self):
        #If we're long and there's a directional movement crossover to the south, sell sell sell!
       if self.is_long and (self.plus < self.minus):
          self.liquidate()
        #If we're long and our profit and loss percent is less -5, sell sell sell!   
       if self.is_long and (self.position.pnl_percentage < -5):
          self.liquidate()
        #Anything above a 40 rsi, means it's going to come down in price, soon, anything below 40 is a rather good indicator of it being overbought and thus not actively going down.
       if self.is_long and ta.rsi(self.candles) > 40:
          self.liquidate()
        #If we're short, and it drops below -5% profit, liquidate because it's gonna keep going!
       if self.is_short and (self.position.pnl_percentage < -5):
          self.liquidate() 
                 
