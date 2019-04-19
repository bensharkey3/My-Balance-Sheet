import pandas as pd
import datetime

# read in latest downloaded version of ssheet
ssheet = 'C:\\Users\\user\\Downloads\\My Balance Sheet (80).xlsx'

# create a df for each sheet
AssetInfo = pd.read_excel(ssheet, sheet_name='AssetInfo')
Transactions = pd.read_excel(ssheet, sheet_name='Transactions')
AssetValues = pd.read_excel(ssheet, sheet_name='AssetValues')
CashAccountHoldings = pd.read_excel(ssheet, sheet_name='CashAccountHoldings')

# get most recent date in AssetValues  
date = AssetValues['Date'].max()

# join AssetValues and Transactions (for non dollar amounts in Transactions)
ch = AssetValues[AssetValues['Date'] == date].merge(
    Transactions[Transactions['UnitType'] != 'dollars'].groupby(['Name', 'AccountClass', 'UnitType']).sum().reset_index()
    , on='Name')

# join AssetValues and Transactions (for non dollar amounts in Transactions)
ch = AssetValues[AssetValues['Date'] == date].merge(
    Transactions[Transactions['UnitType'] != 'dollars'].groupby(['Name', 'AccountClass', 'UnitType']).sum().reset_index()
    , on='Name')

# create cd (for dollar amounts in Transactions)
cd = Transactions[Transactions['UnitType'] == 'dollars'].groupby(['AccountClass', 'UnitType']).sum().reset_index()
cd['Name'] = 'cash'
cd['UnitPrice($AU)'] = 1

# union in cd with ch
th = pd.concat([ch, cd], sort=False).reset_index(drop=True)

# fill missing dates
th['Date'] = th['Date'].iloc[0]

# clean CashAccountHoldings to be able to union in
ca = CashAccountHoldings[CashAccountHoldings['Date'] == date]
ca.rename(columns={'Amount($AU)':'Qty'}, inplace=True)
ca = ca[['Date', 'Name', 'Qty']]
ca['UnitPrice($AU)'] = 1
ca['AccountClass'] = 'savings'
ca['UnitType'] = 'dollars'

# union in CashAccountHoldings
cd = pd.concat([ca, th], sort=False).reset_index(drop=True)

# remove any columns with zero in Qty
cd = cd[cd['Qty'] != 0]

# subtract cash amounts in index and speculative accounts from Commbank accounts
cd.loc[(cd['Name'] =='Commbank accounts'),'Qty'] = cd.loc[(cd['Name'] =='Commbank accounts'),'Qty'] - cd[((cd['AccountClass'] == 'index') | (cd['AccountClass'] == 'speculative')) & (cd['Name'] == 'cash')].sum()['Qty']

# add amount column
cd['Amount($AU)'] = cd['Qty'] * cd['UnitPrice($AU)']

cd = cd.sort_values('Amount($AU)', ascending=False)

### Create a table of every holding on every date
# group Transactions table by only the relevent columns
t1 = Transactions.groupby(['Date', 'Name', 'AccountClass', 'UnitType']).sum().reset_index()

# create a cumulative sum of Qty column
t1['QtyCum'] = t1.groupby(['Name', 'AccountClass', 'UnitType'])['Qty'].cumsum()

# pivot from long to wide
t2 = t1.pivot_table(index='Date', columns=['Name', 'AccountClass', 'UnitType'], values='QtyCum')

# create df with all relevent dates, from 2018-08-03 to most recent date in AssetValues
today = datetime.datetime.today() 
df = pd.DataFrame(pd.date_range(start='2018-08-03', end=date, dtype='datetime64[ns]', freq='D'))
df.rename(columns={0:'Date'}, inplace=True)
df.set_index('Date', inplace=True)

# union in all dates to t2 and ffill to show holdings on each date
t3 = pd.concat([t2, df])
t3 = t3.groupby('Date').mean()
t3.ffill(inplace=True)

# unstack from wide to long
t4 = t3.unstack().reset_index().sort_values(['Date', 'AccountClass', 'Name', 'UnitType'])
t4.dropna(inplace=True)
t4.rename(columns={0:'QtyCum'}, inplace=True)
t4.reset_index(inplace=True, drop=True)

### Create a table of every market value for all AssetValues entered
# join t5 and AssetValues
t5 = t4.merge(AssetValues, on=['Date', 'Name'], how='left')
t5['MktVal'] = t5['QtyCum'] * t5['UnitPrice($AU)']
t5.dropna(inplace=True)

# format columns to $
pd.options.display.float_format = '{:.2f}'.format

# reset index
t5pvt = t5.pivot_table(index='Date', columns='Name' ,values='MktVal').reset_index()

### Plot MktVal against time
# create plot dataframe
t5plt = t5.groupby(['Date','AccountClass'])['MktVal'].sum().unstack().reset_index()

# add in compound interest scenarios
t5plt['10% compound interest'] = 50000*(1+0.1)**((t5plt['Date'] - t5plt['Date'].min()).dt.days /365)
t5plt['5% compound interest'] = 50000*(1+0.05)**((t5plt['Date'] - t5plt['Date'].min()).dt.days /365)

# make date the index
t5plt.index = t5plt['Date']
t5plt.drop('Date', axis=1, inplace=True)

# plot
#t5plt.plot(color=['tab:blue', 'tab:orange', '0.75', '0.75'], figsize=(15,8))

### Create a table and plot cumulative savings by date
trn1 = Transactions[Transactions['TransactionType'].isin(['buy', 'sell', 'proceeds from sale'])]
trn2 = trn1.merge(AssetValues, on=['Date', 'Name'], how='left')
trn2['InjectAmount($AU)'] = trn2['Qty'] * trn2['UnitPrice($AU)']
trn3 = trn2.groupby('Date')[['InjectAmount($AU)']].sum().cumsum()
cumsav = CashAccountHoldings.groupby('Date').sum()
cumsav1 = cumsav.merge(trn3, on='Date', how='outer')
cumsav1.ffill(inplace=True)
cumsav1.fillna(0, inplace=True)

# subtract out what belongs to the index and speculative accounts
t6 = t5[t5['Name'] == 'cash'].groupby('Date')[['MktVal']].sum()
cumsav2 = cumsav1.merge(t6, how='outer', on='Date')
cumsav2.rename(columns={'MktVal':'OwedToIndex&Spec($AU)', 'Amount($AU)':'CashAccounts($AU)'}, inplace=True)
cumsav2['SavingsTotal($AU)'] = cumsav2['CashAccounts($AU)'] + cumsav2['InjectAmount($AU)'] - cumsav2['OwedToIndex&Spec($AU)']
cumsav2['SavingsTotalZeroed($AU)'] = cumsav2['CashAccounts($AU)'] + cumsav2['InjectAmount($AU)'] - cumsav2['OwedToIndex&Spec($AU)'] - 4451

# add in a savings target line
cumsav2.reset_index(inplace=True)
cumsav2['SavingsTarget($AU)'] = 2000*((cumsav2['Date'] - cumsav2['Date'].min()).dt.days *12/365)
cumsav2.set_index('Date', inplace=True)
#cumsav2[['SavingsTotalZeroed($AU)', 'SavingsTarget($AU)']].plot(figsize=(15,8), xlim=None)

### Create a table and plot net worth by date
nw = cumsav2[['CashAccounts($AU)', 'OwedToIndex&Spec($AU)']].merge(t5plt[['index', 'speculative']], how='outer', on='Date')
nw['Total($AU)'] = nw['CashAccounts($AU)'] - nw['OwedToIndex&Spec($AU)'] + nw['index'] + nw['speculative']
#nw['Total($AU)'].plot(figsize=(15,8))
nw.drop(['CashAccounts($AU)', 'OwedToIndex&Spec($AU)'], axis=1, inplace=True)
df = nw.merge(cumsav2, how='left', on='Date')
df['TotalZeroed($AU)'] = df['Total($AU)'] - df['Total($AU)'][0]
df['CapitalGainTotalZeroed($AU)'] = df['TotalZeroed($AU)'] - df['SavingsTotalZeroed($AU)']

### Write file to excel to be read by Tableau
df.to_csv('C:\\Users\\user\\Google Drive\\MyBalanceSheetFiles\\df.csv')
cd.to_csv('C:\\Users\\user\\Google Drive\\MyBalanceSheetFiles\\cd.csv')
