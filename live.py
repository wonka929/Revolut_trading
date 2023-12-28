import pandas as pd
from yahoo_fin import stock_info
import yfinance as yf
import plotly as py
from plotly.offline import plot, init_notebook_mode
#init_notebook_mode()
import cufflinks as cf
from time import sleep
import datetime
#%matplotlib inline
cf.set_config_file(offline=True)

stocks_list = ('DOCU', 'CTAS', 'SFIX', 'BYND')


while 15<=datetime.datetime.now().hour<22:
	#count=0
	#fig1 = py.subplots.make_subplots(rows=3, cols=1)
	for stock in stocks_list:
		#count = count + 1
		data = yf.download(  # or pdr.get_data_yahoo(...
			# tickers list or string as well
			tickers = stock,

			# use "period" instead of start/end
			# valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
			# (optional, default is '1mo')
			period = "1d",

			# fetch data by interval (including intraday if period < 60 days)
			# valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
			# (optional, default is '1d')
			interval = "1m",

			# group by ticker (to access via data['SPY'])
			# (optional, default is 'column')
			group_by = 'column',

			# adjust all OHLC automatically
			# (optional, default is False)
			auto_adjust = False,

			# download pre/post regular market hours data
			# (optional, default is False)
			prepost = False,

			# use threads for mass downloading? (True/False/Integer)
			# (optional, default is True)
			threads = True,

			# proxy URL scheme use use when downloading?
			# (optional, default is None)
			proxy = None
		    )
		
		print(stock)
		# visualiz stock data
		qf = cf.QuantFig(data)
		qf.add_bollinger_bands() 
		qf.add_rsi(periods=20,color='java')
		#qf.add_macd()
		fig = qf.iplot(asFigure=True)
		#qf.iplot()
		#fig1.append_trace(fig['data'][0], count, 1)
		py.offline.plot(fig, filename=stock + '.html', auto_open=False)
		
	print('Vado in sleep...')
	sleep(1*60)

print('ciao')
