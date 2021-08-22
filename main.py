import os
from ETFiNavSimulator import *
import utils
import etf_lists
import pandas as pd

# Load excel spreadsheet
# etfs, worksheets = load_data('iShares--Corp-Bond-UCITS-ETF-USD-Dist-USD-Distributing_fund.xls', folder=False)
if not os.path.isdir('ishare_etfs'):
    os.mkdir('ishare_etfs')

# Download all xls files from etf provider
utils.get_files(etf_lists.ishares_etf_list, 'ishares')

# Load sheets
etf_worksheets = utils.load_sheets('ishare_etfs/', etf_lists.ishares_etf_list)

# Generate Price list
prices, initial_nav, shares_outstanding = utils.generate_price_list(etf_worksheets)

# Generate holdings matrix
holdings_matrix = utils.generate_holdings_matrix(prices, etf_worksheets)



# Run simulation
etfs = ETFiNavSimulator(initial_nav, prices['Price'].to_numpy(), holdings_matrix, shares_outstanding, calc_method='full')
sim_time = etfs.run_simulation()

df = pd.DataFrame([etf_lists.ishares_etf_list.keys(), etfs.initial_nav, etfs.inav]).transpose()
df.columns = ['ETF', 'Initial Nav', 'Final Nav']
df = df.set_index('ETF')
print(df)

print("Time for full calc: {}".format(sim_time))
# print("initial Nav: {}".format(etfs.initial_nav))
# print("iNav: {}".format(wtfs.))



etfs = ETFiNavSimulator(initial_nav, prices['Price'].to_numpy(), holdings_matrix, shares_outstanding, calc_method='partial')
sim_time = etfs.run_simulation()

print("Time for partial calc: {}".format(sim_time))
# print("initial Nav: {}".format(etfs.initial_nav))
# print("iNav: {}".format(wtfs.))
