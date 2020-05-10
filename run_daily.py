#!/usr/bin/env python
# coding: utf-8

# In[6]:


import yfinance as yf
import pandas as pd
import pprint
from tqdm.notebook import tqdm
import matplotlib.pyplot as plot
import seaborn as sns
import pickle


# ## Importazione della lista di stock supportata da revolut

# In[7]:


stocks_list = pd.read_csv('Stock_list.csv', sep=';')
stocks = ''
for item in stocks_list['Ticker']:
    stocks = stocks + ' ' + str(item)


# ### Scaricamento dei dati di storico delle aziende

# In[4]:


data = yf.download(  # or pdr.get_data_yahoo(...
        # tickers list or string as well
        tickers = stocks,

        # use "period" instead of start/end
        # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        # (optional, default is '1mo')
        period = "2y",

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


# ### Download dei dati delle aziende

# In[ ]:


#ff = pd.DataFrame(yf.Ticker('MSFT').info)
#to_del = []
#
#for company in tqdm(pos_perf.index):
#    try:
#        ff = ff.append(yf.Ticker(company).info, ignore_index=True).fillna(0)
#    except Exception as e:
#        print(company)
#        to_del.append(company)
#        print(e)
#        continue


# ## Salvataggio dei dati scaricati

# In[8]:


data = pd.read_pickle('dataset.pkl')


# In[9]:


ff = pd.read_pickle('descriptions.pkl')


# In[10]:


data.fillna(value=0, inplace=True)


# ## Analisi sulla performance delle 791 aziende nei 2 anni

# In[11]:


def get_stock_data(df, stocksimbol):
    df = df.xs(stocksimbol, axis=1, level = 1, drop_level=True)
    df.drop(columns='Close', inplace=True)
    df.rename(columns = {'Adj Close':'Close'}, inplace=True)
    df.columns = df.columns.str.lower()
    return df


# In[12]:


import pandas as pd
from stockstats import StockDataFrame as Sdf
from tqdm.notebook import tqdm

data = pd.read_pickle('dataset.pkl')
data = data.drop(data.index[0])

score = []
name = []
diff = []

for symbol in tqdm(data.columns.get_level_values(1).unique().values):
    try:
        stock  = Sdf.retype(get_stock_data(data, symbol))

        signal = stock['macds']        # Your signal line
        macd   = stock['macd']         # The MACD that need to cross the signal line
        #                                              to give you a Buy/Sell signal
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

        if stock[stock['Advice']!=0]['advice'][-1] == 1 and stock[stock['Advice']!=0]['advice'].index[-1] != stock['Advice'].index[-1]:
            stock['Advice'][-1] = -1

        elif stock[stock['Advice']!=0]['advice'][-1] == 1 and stock[stock['Advice']!=0]['advice'].index[-1] == stock['Advice'].index[-1]:
            #stock['Advice'][-2] = -1
            stock['Advice'][-1] = 0

        gain = stock['close']*stock['Advice']*(-1)
        delta = (stock['close'][-1]-stock['close'][0])/(stock['close'][0])
        #stock['gain'] = gain
        #print(gain.sum()/(stock['close'][-1]-stock['close'][0]))
        
        score.append(gain.sum()/(stock['close'][0]))
        name.append(symbol)
        diff.append(delta)
    except:
        continue

diff = pd.DataFrame(diff, index=name)
scores = pd.DataFrame(score, index=name)
scores.rename(columns={0:'Performance'}, inplace=True)


# In[13]:


ff = pd.read_pickle('descriptions.pkl')
ff = ff[['symbol', 'sector']]
ff.set_index('symbol', inplace=True)
scores = pd.merge(ff, scores, left_index=True, right_index=True)
scores = pd.merge(scores, diff, left_index=True, right_index=True)
scores['sector'].replace(0, 'Unknown', inplace=True)
scores.rename(columns={0:'diff'}, inplace=True)
scores.to_csv('scores.csv', sep=';', decimal=',')


# In[14]:


#fig = plot.figure(figsize=(70, 10))
filtered = scores[scores['Performance']>1.50]
#sns.scatterplot(data=filtered.sort_values(by='sector'), x=filtered.index, y='Performance', hue='sector')
#plot.savefig('performance_sector.svg')
filtered.sort_values(by='Performance', ascending=False).to_csv('best_performers_MACD.csv', sep=';', decimal=',')


# In[15]:


ff.query("symbol in " + str(list(filtered.index.values))).to_csv('Best_performer_MACD_values.csv', sep=';', decimal=',')


# In[16]:


filtered['delta'] = filtered['Performance'] - filtered['diff']


# In[17]:


filtered.sort_values(by='delta', ascending=False).to_csv('best_performers_MACD.csv', sep=';', decimal=',')


# In[18]:


fig, ax = plot.subplots(figsize=(10,5))
filtered.sort_values(by='delta', ascending=False).drop(columns='diff').plot(figsize=(10,5), ax=ax)
filtered.sort_values(by='delta', ascending=False)['diff'].plot.bar(figsize=(10,5), ax=ax)
plot.savefig('Performance_comparison.svg')
plot.close()


# In[19]:


import pandas as pd
from stockstats import StockDataFrame as Sdf
from tqdm.notebook import tqdm

data = pd.read_pickle('dataset.pkl')
data = data.drop(data.index[0])
filtered = pd.read_csv('best_performers_MACD.csv', sep=';', decimal=',').set_index('Unnamed: 0')

score = []
name = []

for company in filtered.index.values:
    stock  = Sdf.retype(get_stock_data(data, company))

    signal = stock['macds']        # Your signal line
    macd   = stock['macd']         # The MACD that need to cross the signal line
    #                                              to give you a Buy/Sell signal
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

    #if stock[stock['Advice']!=0]['advice'][-1] == 1:
    #    stock['Advice'][-1] = -1


    #print(stock[stock['Advice']!=0]['advice'][-1])


    gain = stock['close']*stock['Advice']*(-1)
    stock['gain'] = gain
    #score.append(gain.sum()/(stock['close'][-1]-stock['close'][0]))
    #name.append(symbol)
    stock['Advice']=stock['Advice']*100
    stock.drop(columns=['volume', 'gain']).plot(figsize=(30,10))
    plot.title(str(round(gain.sum()*100/(stock['close'][0]))) + '%')
    plot.savefig(str(company) + '_test.png')
    plot.close()


# ## Action on current owned actions

# In[54]:


import pandas as pd
from stockstats import StockDataFrame as Sdf
from tqdm.notebook import tqdm

data = pd.read_pickle('dataset.pkl')
data = data.drop(data.index[0])
owned = ['MSFT','TSLA']

score = []
name = []
advice = {}

for company in owned:
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
    #print(stock['Advice'][-1])
    stock.drop(columns=['volume']).plot(figsize=(30,10))
    plot.title(company)
    plot.savefig(str(company) + '_owned.png')
    plot.close()
    advice[company]=stock['Advice'][-1]

azione = pd.DataFrame.from_dict(advice, orient='index')
azione['link'] = 'https://www.tradingview.com/symbols/' + azione.index.values
print(azione.to_markdown())

