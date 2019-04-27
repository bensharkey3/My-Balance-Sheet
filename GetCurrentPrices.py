import pandas as pd
import glob
import os
from urllib.request import Request, urlopen
import json

# api key for alpha vantage
apikey = 'PIHXDM5NYLGDIL1M'
functstock = 'TIME_SERIES_DAILY'
functaud = 'FX_DAILY'
from_symbol = 'AUD'
to_symbol = 'USD'

# get aud/usd exchange rate
urlxr = 'https://www.alphavantage.co/query?function={}&from_symbol={}&to_symbol={}&apikey={}'.format(functaud, from_symbol, to_symbol, apikey)
request = Request(urlxr)
response = urlopen(request)
data = json.loads(response.read())
try:
    dfasx = pd.DataFrame.from_dict(data['Time Series FX (Daily)'], orient="index")[['4. close']]
except:
    print('FX API not working')
dfasx = dfasx[dfasx.index == dfasx.index.max()]
audusd = float(dfasx.iloc[0][0])

# get list of us stock codes from latest file exported from google sheets
#symbols = ['GOOG', 'AAPL']
list_of_files = glob.glob(r'C:\Users\user\Downloads\My Balance Sheet**.xlsx')
ssheet = max(list_of_files, key=os.path.getctime)
AssetInfo = pd.read_excel(ssheet, sheet_name='AssetInfo')
us_codes = AssetInfo[AssetInfo['Exchange'] == 'NYSE']['Code'].unique()

# create an empty df to append rows to
dfus = pd.DataFrame(columns=['4. close'])

# add a row to df for each symbol
for i in us_codes:
    symbol = i
    urlus = 'https://www.alphavantage.co/query?function={}&symbol={}&apikey={}'.format(functstock, symbol, apikey)
    request = Request(urlus)
    response = urlopen(request)
    data = json.loads(response.read())
    try:
        i = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient="index")[['4. close']]
    except:
        print('US stock API not working')
    i['code'] = symbol
    i = i[i.index == i.index.max()]
    dfus = dfus.append(i, sort=False)

dfus.reset_index(inplace=True)
dfus.rename(columns={'4. close':'close_price', 'index':'close_date'}, inplace=True)
dfus['close_price'] = dfus['close_price'].astype(float)

# convert us shares price into aud
dfus['close_price'] = dfus['close_price'] * (1/audusd)

# get asx codes from the latest file exported from google sheets
list_of_files = glob.glob(r'C:\Users\user\Downloads\My Balance Sheet**.xlsx')
ssheet = max(list_of_files, key=os.path.getctime)
dfasx = pd.DataFrame(columns=['code', 'close_date', 'close_price'])
AssetInfo = pd.read_excel(ssheet, sheet_name='AssetInfo')
asx_codes = AssetInfo[AssetInfo['Exchange'] == 'ASX']['Code'].unique()

for i in asx_codes:
    temp = pd.read_json('https://www.asx.com.au/asx/1/share/{ticker}/prices?interval=daily&count=1'.format(ticker=i), orient='split')
    temp = temp[['code', 'close_date', 'close_price']]
    dfasx = dfasx.append(temp, sort=False)

# concat dataframes together, rename columns, return name instead of code
df1 = pd.concat([dfasx, dfus], sort=False)
df1 = df1.merge(AssetInfo, left_on='code', right_on='Code')[['close_date', 'Name', 'close_price']]
df1.rename(columns={'close_date':'Date', 'close_price':'UnitPrice($AU)'}, inplace=True)

# set date to cuurent day
df1['Date'] = pd.datetime.today().strftime('%Y-%m-%d')

# show output
df1