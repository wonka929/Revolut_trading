import quiverquant
import pandas as pd
#Replace <token> with your personal token
quiver = quiverquant.quiver(<token>)
df = quiver.wallstreetbets(date_from=”20200901")

dfWeek = df.groupby([pd.Grouper(key='Date', freq='W-MON'), 'Ticker'])['Count'].sum().reset_index().sort_values('Date')

import yfinance as yf
import datetime as dt
dfLarge = dfWeek[dfWeek["Count"]>1]
dfLarge = dfLarge.sort_values("Date", ascending=True)
dates = dfLarge["Date"].unique()
#Initial capital of mock portfolio
capital = 100000
started = False
startedDFW = False
for date in dates[:-2]:
    dfW = dfLarge[dfLarge["Date"]==date]
    dfW = dfW.sort_values("Count", ascending=False).head(5)
    dfW['prop'] = dfW['Count']/dfW["Count"].sum()
    dfW['buy'] = capital*dfW['prop']
    buyDate = date+pd.Timedelta(days=6)
    dfW['buyDate'] = [buyDate]*len(dfW['buy'])
    if not startedDFW:
        dfWs = dfW
        startedDFW = True
    else:
        dfWs = pd.concat([dfWs, dfW])
    sellDate = date+pd.Timedelta(days=15)
    startedWeek = False
    print(date)
    for index, row in dfW.iterrows():
        ticker = row["Ticker"]
        print(ticker)
        try:
            ytStock = yf.download(ticker, start=str(buyDate.date()), end=str(sellDate.date()), interval="1d").reset_index()
            shares = row["buy"]/ytStock["Adj Close"].values[0]
            ytStock = ytStock.iloc[1:]
        except:
            print("Error")
            ytStock = yf.download("SPY", start=str(buyDate.date()), end=str(sellDate.date()), interval="1d").reset_index()
            shares = row["buy"]/ytStock["Adj Close"].values[0]
            ytStock = ytStock.iloc[1:]
        ytStock["OpenAmount"] = ytStock["Open"]*shares
        ytStock["CloseAmount"] = ytStock["Adj Close"]*shares
        ytStock["Ticker"] = [ticker]*len(ytStock["OpenAmount"])
        ytStock = ytStock.fillna(method='ffill')
        ytStock = ytStock.fillna(method='bfill')
        ytStock = ytStock.dropna()
        if not startedWeek:
            dfCombined = ytStock
            startedWeek = True
        else:
            dfCombined = pd.concat([dfCombined, ytStock])
        
        if not started:
            dfAll = ytStock
            started = True
        else:
            dfAll = pd.concat([dfAll, ytStock])
            
    capital = 0
    for ticker in dfCombined["Ticker"].unique():
        dfT = dfCombined[dfCombined["Ticker"]==ticker]
        capital+=dfT["CloseAmount"].values[-1]
    print("Week end capital: ", capital)


dfDay = dfAll.groupby("Date").sum().reset_index()
dfDay["Fund"] = ["WSB"]*len(dfDay["Close"])
dfSPY = yf.download("SPY", start="2018-09-01", end="2021-02-18", interval="1d").reset_index()
dfSPY["Fund"] = ["S&P 500"] * len(dfSPY["Open"])
shares = 100000/dfSPY["Open"].values[0]
dfSPY["OpenAmount"] = dfSPY["Open"]*shares
dfSPY["CloseAmount"] = dfSPY["Close"]*shares
dfCombined = pd.concat([dfDay, dfSPY])


import plotly.express as px
import plotly
fig = px.line(dfCombined, x="Date", y="CloseAmount", title='WSB', color="Fund", color_discrete_sequence=["rgb(229, 81, 39)","rgb(118, 213, 232)" ])
wsbReturn = (capital-100000)/100000*100
fig.update_layout(title="<b>+"+str(round(wsbReturn, 2))+"% Return</b><br>Aug 2018 - Feb 2021", titlefont=dict(color='rgb(229, 81, 39)', size=20), plot_bgcolor='rgb(32,36,44)', paper_bgcolor='rgb(32,36,44)')
fig.update_xaxes(title_text="",color='white', showgrid=False, tickfont=dict(size=10))
fig.update_yaxes(title_text="$", color='white', showgrid=False, titlefont=dict(size=20),gridcolor="rgb(228,49,34)")
fig.update_layout(
    legend=dict(
        title=dict(text="",font=dict(color='white')),
        x=.85, y=1.15,
        font=dict(
            color='white',
            size=15
        )
    )
)
fig.update_traces(line=dict(width=3))
fig.show()


import plotly.graph_objects as go
fig = go.Figure(px.bar(dfWs, x="buyDate", y="buy", color='Ticker',text='Ticker',color_discrete_sequence=px.colors.qualitative.Light24))
fig.update_layout(title="Portfolio by Week", titlefont=dict(color='rgb(228,49,34)'), plot_bgcolor='rgb(32,36,44)', paper_bgcolor='rgb(32,36,44)')
fig.update_xaxes(title_text="",color='white', showgrid=False, fixedrange=False)
fig.update_yaxes(title_text="$",color='white', showgrid=False,  fixedrange=False,gridwidth=1,gridcolor="rgb(109,177,174)")
fig.update_layout(
    legend=dict(
        title=dict(text="Ticker",font=dict(color="white")),
        
        font=dict(
            color='white'
        ),
        
    )
)
fig.show()
