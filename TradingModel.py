import pandas as pd
import requests
import json
import plotly.graph_objs as go
from plotly.offline import plot
from pyti.smoothed_moving_average import smoothed_moving_average as sma
from pyti.bollinger_bands import lower_bollinger_band as lbb
from Binance import Binance

class TradingModel:
    # constructor
    def __init__(self, symbol):
        self.symbol = symbol
        self.exchange = Binance()
        self.df = self.exchange.getSymbolData(symbol, '4h') #gets data on symbol from the last 4 hrs
        self.last_price = self.df['close'][len(self.df['close'])-1]
        self.buy_signals = []

        # compute MAs and lower bollinger band
        try:
            self.df['fast_sma'] = sma(df['close'].tolist(), 10)
            self.df['slow_sma'] = sma(df['close'].tolist(), 30)
            self.df['low_boll'] = lbb(df['close'].tolist(), 14) # bollinger band strategy
        except Exception as e:
            print("exeption occured when trying to compute indicators on "+ self.symbol)
            print(e)
            return None
         
    #gets data from binance api
    def getData(self):
        #binance api
        base = 'https://api.binance.com'
        #candlestick data endpoint
        endpoint = '/api/v1/klines'
        #the btc/usd symbol and the length of the candlestick
        params= '?&symbol='+symbol+'&interval='+interval
        url= base + endpoint + params
        #download data
        data = requests.get(url)
        dictionary = json.loads(data.text)
        df = pd.DataFrame.from_dict(dictionary)
        # cuts out unnecessary info from data frame
        # only needs open time, open price, high, low, close, volume
        df = df.drop(range(6,12), axis=1)
        # raname columns
        col_names = ['time', 'open', 'high', 'low', 'close', 'volume']
        df.columns= col_names
        #convert results to float
        for col in col_names:
            df[col] = df[col].astype(float)
        # add smas
        df['fast_sma'] = sma(df['close'].tolist(), 10)
        df['slow_sma'] = sma(df['close'].tolist(), 30)
        return df


    def strategy(self):
        df= self.df
        buy_signals = []
        # loop through candlesticks
        for i in range(1, len(df['close'])):
            # if the slow SMA - low price is greater than 3% of low price, BUY!
            if df['slow_sma'][i] > df['low'][i] and (df['slow_sma'][i] - df['low'][i]) > 0.03 * df['low'][i]:
                buy_signals.append([df['time'][i], df['low'][i]])

        self.plotData(buy_signals=buy_signals)


    def plotData(self, buy_signals= False):
        df = self.df

        # plot candlesticks
        candle = go.Candlestick(
            x = df['time'],
            open = df['open'],
            close = df['close'],
            high = df['high'],
            low = df['low'],
            name = "Candlesticks")
        #plot moving avgs
        fastSMA= go.Scatter(
            x = df['time'],
            y = df['fast_sma'],
            name = "Fast SMA",
            line= dict(color=('rgba(102,207,255,50)')))
        
        slowSMA= go.Scatter(x = df['time'], y =df['slow_sma'], name = "Slow SMA", line= dict(color=('rgba(255,207,102,50)')))
        
        lowbb = go.Scatter(
            x = df['time'],
            y = df['low_boll'],
            name = "Lower Bollinger Band",
            line = dict(color = ('rgba(255, 102, 207, 50)')))

        data = [candle,slowSMA,fastSMA, lowbb]
        if buy_signals:
            buys = go.Scatter(
                x= [item[0] for item in buy_signals], #time
                y= [item[1] for item in buy_signals], #buying price
                name = "Buy Signals",
                mode = "markers",
                )

            sells = go.Scatter(
                x= [item[0] for item in buy_signals], #time
                y= [item[1]*1.02 for item in buy_signals], #buying price
                name = "Sell Signals",
                mode = "markers",
                )
            data = [candle,slowSMA,fastSMA, buys, sells]
        # style and display
        layout= go.Layout(title = self.symbol)
        fig = go.Figure(data = data, layout = layout)
        plot(fig, filename= self.symbol)

    #if price is 10% below SMA, return true (also try 20%)
    def maStrategy(self, i:int):
        df = self.df
        buy_price = 0.9 * df['slow_sma'][i]
        if buy_price >= df['close'][i]:
            self.buy_signals.append([df['time'][i], df['close'][i], df['close'][i] * 1.045])
            return True

        return False

    # if price 5% below lower bollinger band, return true (also try 2%)
    def bollStrategy(self, i:int):


        df = self.df
        buy_price = 0.98 * df['low_boll'][i]
        if buy_price >= df['close'][i]:
            self.buy_signals.append([df['time'][i], df['close'][i], df['close'][i] * 1.045])
            return True

        return False


def Main():
    #symbol = "BTCUSDT"
    #model = TradingModel(symbol)
    #model.strategy()
    exchange = Binance()
    symbols = exchange.getTradingSymbols()

    for symbol in symbols:
        print(symbol)
        model = TradingModel(symbol)
        plot = False
        # if model.maStrategy(len(model.df['close'])-1):
        #     print("MA strat match on "+symbol)
        #     plot = True

        if model.bollStrategy(len(model.df['close'])-1):
            print("Boll strat match on "+symbol)
            plot = True
        
        if plot:
            model.plotData()
if __name__ == '__main__':
    Main()
