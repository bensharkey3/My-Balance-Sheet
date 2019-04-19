import pandas as pd
import glob
import os
from urllib.request import Request, urlopen
import json


# get the latest file exported from google sheets
list_of_files = glob.glob(r'C:\Users\user\Downloads\My Balance Sheet**.xlsx')
ssheet = max(list_of_files, key=os.path.getctime)

asx1 = pd.read_excel(r'C:\Users\user\Google Drive\asx1.xlsx', parse_dates=['close_date'])
df1 = pd.DataFrame(columns=['code', 'close_date', 'close_price'])
AssetInfo = pd.read_excel(ssheet, sheet_name='AssetInfo')
asx_codes = AssetInfo[AssetInfo['Exchange'] == 'ASX']['Code'].unique()

for i in asx_codes:
    temp = pd.read_json('https://www.asx.com.au/asx/1/share/{ticker}/prices?interval=daily&count=1'.format(ticker=i), orient='split')
    temp = temp[['code', 'close_date', 'close_price']]
    df1 = df1.append(temp, sort=False)

# list of stock symbols
symbols = ['GOOG', 'AAPL']

# api key for alpha vantage
apikey = 'PIHXDM5NYLGDIL1M'
functstock = 'TIME_SERIES_DAILY'
functaud = 'FX_DAILY'
from_symbol = 'AUD'
to_symbol = 'USD'

# create an empty df to append rows to
df = pd.DataFrame(columns=['4. close'])

# get aud/usd exchange rate
url = 'https://www.alphavantage.co/query?function={}&from_symbol={}&to_symbol={}&apikey={}'.format(functaud, from_symbol, to_symbol, apikey)
request = Request(url)
response = urlopen(request)
data = json.loads(response.read())
dfasx = pd.DataFrame.from_dict(data['Time Series FX (Daily)'], orient="index")[['4. close']]
dfasx = dfasx[dfasx.index == df1['close_date'].max()]
audusd = float(dfasx.iloc[0][0])

# add a row to df for each symbol
for i in symbols:
    symbol = i
    url = 'https://www.alphavantage.co/query?function={}&symbol={}&apikey={}'.format(functstock, symbol, apikey)
    request = Request(url)
    response = urlopen(request)
    data = json.loads(response.read())
    i = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient="index")[['4. close']]
    i['code'] = symbol
    i = i[i.index == i.index.max()]
    df = df.append(i, sort=False)
    
df.reset_index(inplace=True)
df.rename(columns={'4. close':'close_price', 'index':'close_date'}, inplace=True)
df['close_price'] = df['close_price'] * (1/audusd)

# concat two dfs together
dfn = pd.concat([df1, df])






# add error checking on api calls