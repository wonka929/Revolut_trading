#!/usr/bin/env python
# coding: utf-8

import yfinance as yf
import pandas as pd
import tqdm
import matplotlib.pyplot as plot
import pickle
import os
from stockstats import StockDataFrame as Sdf

pd.options.mode.chained_assignment = None  # default='warn'


# ## Importazione della lista di stock supportata da revolut

stocks_list = pd.read_csv('Stock_list.csv', sep=';')
stocks = ''
for item in stocks_list['Ticker']:
    stocks = stocks + ' ' + str(item)


# ### Scaricamento dei dati di storico delle aziende

data = yf.download(  # or pdr.get_data_yahoo(...
        #tickers list or string as well
        tickers = stocks,

        # use "period" instead of start/end
        # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        # (optional, default is '1mo')
        period = "1y",

        # fetch data by interval (including intraday if period < 60 days)
        # valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
        # (optional, default is '1d')
        interval = "1d",

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

data.to_pickle('dataset.pkl')

# Salvataggio dello storico e riapertura dello stesso

data = pd.read_pickle('dataset.pkl')

#ff = pd.read_pickle('descriptions.pkl')

# Fillna dei dati NAN con 0

data.fillna(value=0, inplace=True)


# Questa funzione serve per filtrare i dati del dataframe sul singolo stock e utilizzare Adj Close al posto di Close per i dati di chiusura giornata

def get_stock_data(df, stocksimbol):
    df = df.xs(stocksimbol, axis=1, level = 1, drop_level=True)
    df.drop(columns='Close', inplace=True)
    df.rename(columns = {'Adj Close':'Close'}, inplace=True)
    df.columns = df.columns.str.lower()
    return df



#data = pd.read_pickle('dataset.pkl')
data = data.drop(data.index[0])

score = []
name = []
diff = []

# Per ogni stock, filtra il database sui dati di quello stock e lo manda in pancia a stockstats perchè possa estrarre le statistiche di preformance

for symbol in tqdm.tqdm(data.columns.get_level_values(1).unique().values):
    try:
        stock  = Sdf.retype(get_stock_data(data, symbol))

# Si gioca con il MACD. Si genera il segnale e la line. Quando il MACD supera il segnale si crea un segnale di Compra. Quando è il contrario si crea un segnale di Vendi. Altrimenti è Hold.
# In questo modo si crea un vettore per cui il valore 0 = Hold, 1 = Buy e -1 = Sell
		
        signal = stock['macds']        # Your signal line
        macd   = stock['macd']         # The MACD that need to cross the signal line to give you a Buy/Sell signal
        listLongShort = ["No data"]    # Since you need at least two days in the for loop

        for i in range(1, len(signal)):
            #                          # If the MACD crosses the signal line upward
            if macd[i] > signal[i] and macd[i - 1] <= signal[i - 1]:
                listLongShort.append(1)
            #                          # The other way around
            elif macd[i] < signal[i] and macd[i - 1] >= signal[i - 1]:
                listLongShort.append(-1)
            #                          # Do nothing if not crossed
            else:
                listLongShort.append(0)

        stock['Advice'] = listLongShort
        # The advice column means "Buy/Sell/Hold" at the end of this day or
        # at the beginning of the next day, since the market will be closed
        stock['Advice'][0] = 0

        if stock[stock['Advice']!=0]['advice'][-1] == 1 and stock[stock['Advice']!=0]['advice'].index[-1] != stock['Advice'].index[-1]:
            stock['Advice'][-1] = -1

        elif stock[stock['Advice']!=0]['advice'][-1] == 1 and stock[stock['Advice']!=0]['advice'].index[-1] == stock['Advice'].index[-1]:
            stock['Advice'][-1] = 0

# Questo genera il risultato di gain simulato ad aver usato il criterio del MACD nel periodo per l'investimento			

        gain = stock['close']*stock['Advice']*(-1)
        delta = (stock['close'][-1]-stock['close'][0])/(stock['close'][0])
        
        score.append(gain.sum()/(stock['close'][0]))
        name.append(symbol)
        diff.append(delta)
		
    except:
        continue


diff = pd.DataFrame(diff, index=name)
scores = pd.DataFrame(score, index=name)
scores.rename(columns={0:'Performance'}, inplace=True)


#Si selezionano solo gli stock che hanno performato, usando il MACD, più di un certo valore di ritorno nel periodo.

filtered = scores[scores['Performance']>1.50]
filtered.sort_values(by='Performance', ascending=False).to_csv('best_performers_MACD.csv', sep=';', decimal=',')

# Di queste, si controlla il valore di performance MACD paragonato alla differenza di prezzo che hanno avuto nel periodo. Se il MACD e la differenza di prezzo si equivalgono, vuole dire che tutto il guadagno è causato solo dall'aumento dell'azione, non dalla bontà del MACD come incide.

filtered['delta'] = filtered['Performance'] - filtered['diff']
#filtered.sort_values(by='delta', ascending=False).to_csv('best_performers_MACD.csv', sep=';', decimal=',')

fig, ax = plot.subplots(figsize=(10,5))
filtered.sort_values(by='delta', ascending=False).drop(columns='diff').plot(figsize=(10,5), ax=ax)
filtered.sort_values(by='delta', ascending=False)['diff'].plot.bar(figsize=(10,5), ax=ax)
plot.savefig('Performance_comparison.svg')
plot.close()


# Prendiamo i best performer del MACD dal sile salvato.

data = pd.read_pickle('dataset.pkl')
data = data.drop(data.index[0])
filtered = pd.read_csv('best_performers_MACD.csv', sep=';', decimal=',').set_index('Unnamed: 0')


# Ricalcoliamo le prestazioni ed i segnali solo per quelli

score = []
name = []
advice = {}

for company in filtered.index.values:
    stock  = Sdf.retype(get_stock_data(data, company))

    signal = stock['macds']        # Your signal line
    macd   = stock['macd']         # The MACD that need to cross the signal line to give you a Buy/Sell signal
    listLongShort = ["No data"]    # Since you need at least two days in the for loop

    for i in range(1, len(signal)):
        #                          # If the MACD crosses the signal line upward
        if macd[i] > signal[i] and macd[i - 1] <= signal[i - 1]:
            listLongShort.append(1)
        #                          # The other way around
        elif macd[i] < signal[i] and macd[i - 1] >= signal[i - 1]:
            listLongShort.append(-1)
        #                          # Do nothing if not crossed
        else:
            listLongShort.append(0)

    stock['Advice'] = listLongShort

    # The advice column means "Buy/Sell/Hold" at the end of this day or
    #  at the beginning of the next day, since the market will be closed
    stock['Advice'][0] = 0
    gain = stock['close']*stock['Advice']*(-1)
    stock['gain'] = gain

    stock['advice_text'] = stock['Advice'].replace({0:'HOLD', 1:'BUY', -1:'SELL'})
    advice[company]=stock['advice_text'][-1]
    stock['Advice']=stock['Advice']*stock['close'].max()
    stock.drop(columns=['volume', 'gain']).plot(figsize=(30,10))
    plot.title(str(round(gain.sum()*100/(stock['close'][0]))) + '%')
    plot.savefig(str(company) + '.png')
    plot.close()


# Creiamo una tabella riassuntiva del consiglio di Buy, Hold e Sell dell'ultimo giorno , con link alla pagina dedicata allo stock di TradingView

tutte_azioni = pd.DataFrame.from_dict(advice, orient='index')
tutte_azioni['link'] = 'https://www.tradingview.com/symbols/' + tutte_azioni.index.values
tab = tutte_azioni.to_markdown()
print(tab)

# Mandiamo la tabella su Telegram

os.system("telegram-send "+ "'" + tab + "'")


## Ripetiamo la tabella dei consigli solo per gli stock possediamo in questo momento

data = pd.read_pickle('dataset.pkl')
data = data.drop(data.index[0])
owned = ['NVDA','AMD','NVAX','NLOK']

score = []
name = []
advice = {}

for company in owned:
	try:
		stock  = Sdf.retype(get_stock_data(data, company))

		signal = stock['macds']        # Your signal line
		macd   = stock['macd']         # The MACD that need to cross the signal line
		#                                              to give you a Buy/Sell signal
		listLongShort = ["No data"]    # Since you need at least two days in the for loop

		for i in range(1, len(signal)):
		    #                          # If the MACD crosses the signal line upward
		    if macd[i] > signal[i] and macd[i - 1] <= signal[i - 1]:
		        listLongShort.append('BUY')
		    #                          # The other way around
		    elif macd[i] < signal[i] and macd[i - 1] >= signal[i - 1]:
		        listLongShort.append('SELL')
		    #                          # Do nothing if not crossed
		    else:
		        listLongShort.append('HOLD')

		stock['Advice'] = listLongShort

		# The advice column means "Buy/Sell/Hold" at the end of this day or
		#  at the beginning of the next day, since the market will be closed
		stock['Advice'][0] = 'HOLD'
		stock.drop(columns=['volume']).plot(figsize=(30,10))
		plot.title(company)
		plot.savefig(str(company) + '_owned.png')
		plot.close()
		advice[company]=stock['Advice'][-1]
	except:
		continue

azione = pd.DataFrame.from_dict(advice, orient='index')
azione['link'] = 'https://www.tradingview.com/symbols/' + azione.index.values
tab = azione.to_markdown()
print(tab)

os.system("telegram-send "+ "'" + tab + "'")

# Ritagliamo i margini dei grafici di tutte le azioni che abbiamo plottato

from PIL import Image, ImageOps
import glob
import os

# Trim all png images with white background in a folder
# Usage "python PNGWhiteTrim.py ../someFolder"

filePaths = glob.glob(os.getcwd() + "/*.png") #search for all png images in the folder

for filePath in filePaths:
	try:
		image=Image.open(filePath)
		image.load()
		imageSize = image.size
		
		# remove alpha channel
		invert_im = image.convert("RGB") 
		
		# invert image (so that white is 0)
		invert_im = ImageOps.invert(invert_im)
		imageBox = invert_im.getbbox()
		
		cropped=image.crop(imageBox)
		cropped.save(filePath)
	except:
		continue

