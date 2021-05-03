import requests
import json
import decimal
import hmac
import time
import pandas as pd
# binance creds
binance_keys = {
	'api_key' : "API-KEY-HERE",
	'secret_key' : "SECRET-KEY-HERE"
}

class Binance:
	# constructor
	def __init__(self):
		self.base = 'https://api.binance.com'
		# all endpoints
		self.endpoints = {
			"order":'/api/v1/order/order',
			"testOrder":'/api/v1/order/test',
			"allOrders":'/api/v1/allOrders',
			"klines":'/api/v1/klines',
			"exchangeInfo": '/api/v1/exchangeInfo'
		}
	#get all symbols currently tradable
	def getTradingSymbols(self):
		url= self.base + self.endpoints["exchangeInfo"]

		try:
			response = requests.get(url)
			#puts the results into a python dictionary
			data = json.loads(response.text)
		except Exception as e:
			print("exeption occured when trying to access "+ url)
			print(e)
			return []

		symbols_list = []
		# put the coins that are being traded into a python list
		for pair in data['symbols']:
			if pair['status']== 'TRADING':
				symbols_list.append(pair['symbol'])
		return symbols_list

	#get data of a trading pair
	def getSymbolData(self, symbol:str, interval:str):
		params= '?&symbol='+symbol+'&interval='+interval
		url= self.base + self.endpoints['klines'] + params
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

		return df

	#convert float to string without scientific notation
	def floatToString(self, f:float):
		ctx = decimal.Context()
		ctx.prec = 12
		d1 = ctx.create_decimal(repr(f))
		return format(d1, 'f')

	#signs our 'place' and 'cancel' orders
	def signRequest(self, params:dict):
		query_string = '&'.join(["{}={}".format(d, params[d]) for d in params])
		signature = hmac.new(binance_keys['secret_key'].encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256)
		params['signature'] = signature.hexdigest()


	#cancels an order
	def cancelOrder(self, symbol:str, orderID:str):
		params = {
			'symbol': symbol,
			'orderID' : orderID,
			'recvWindow' : 5000,
			'timestamp' : int(round(time.time()*1000))
		}

		self.signRequest(params)

		url = self.base + self.endpoints['order']
		try:
			response = requests.post(url, params=params, headers={"X-MBX-APIKEY": binance_keys['api_key']})

			# adding headers to the request to access our binance account
		except Exception as e:
			print("exeption occured when trying to place an order on "+ url)
			print(e)
			response = {'code': '-1', 'msg' :e}
			return None
		return json.loads(response.text)

#gets order info
	def getOrderInfo(self, symbol:str, orderID:str):
		params = {
			'symbol': symbol,
			'orderID' : orderID,
			'recvWindow' : 5000,
			'timestamp' : int(round(time.time()*1000))
		}

		self.signRequest(params)

		url = self.base + self.endpoints['order']
		try:
			# adding headers to the request to access our binance account
			response = requests.get(url, params=params, headers = {"X-MBX-APIKEY": binance_keys['api_key']})
		except Exception as e:
			print("exeption occured when trying to get order info on "+ url)
			print(e)
			response = {'code': '-1', 'msg' :e}
			return None
			return json.loads(response.text)


	#gets all order info based on symbol
	def getAllOrderInfo(self, symbol:str):
		params = {
				'symbol': symbol,
				'timestamp' : int(round(time.time()*1000))
			}

		self.signRequest(params)

		url = self.base + self.endpoints['allOrder']
		try:
			# adding headers to the request to access our binance account
			response = requests.get(url, params=params, headers = {"X-MBX-APIKEY": binance_keys['api_key']})
		except Exception as e:
			print("exeption occured when trying to get all order info on "+ url)
			print(e)
			response = {'code': '-1', 'msg' :e}
			return None
		return json.loads(response.text)

	#places an order
	def placeOrder(self, symbol:str, side:str, type:str, quantity:float, price:float, test:bool=True):
		params = {
			'symbol': symbol,
			'side': side, #BUY or SELL?
			'type': type, #market order, limit order, stop loss?
			'timeInForce': 'GTC', #GTC = good til cancelled (financial term)
			'quantity' : quantity,
			'price' : self.floatToString(price),
			'recvWindow' : 5000,
			'timestamp' : int(round(time.time()*1000))
		}

		self.signRequest(params)

		# picks if its a real order or test order based on given params
		url = ''
		if test:
			url = self.base + self.endpoints['testOrder']
		else:
			url = self.base + self.endpoints['order']

		try:
			# adding headers to the request to access our binance account
			response = requests.post(url, params=params, headers = {"X-MBX-APIKEY": binance_keys['api_key']})
		except Exception as e:
			print("exeption occured when trying to place an order on "+ url)
			print(e)
			response = {'code': '-1', 'msg' :e}
			return None
		return json.loads(response.text)

