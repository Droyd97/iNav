import os
import numpy as np
from bs4 import BeautifulSoup as bs
import pandas as pd
import time

class ETFiNavSimulator():
    def __init__(self, initial_nav, prices, market_value, out_shares, calc_method='full', std=3):
        """ETF iNav Simulator

        This class calculates the iNav of an iShares etf by the following:
        iNav = old_nav + (asset_shares * returns) / shares_outstanding

        initial_nav (float) -- initial NAV of the ETF at the beginning of the day
        prices ([float]) -- prices of the holdings of the ETF
        market_value ([float]) -- market value of each holding. Used to calculate number of shares
        out_shares ([int]) -- number of outstanding shares of the ETF
        calc_method (string) -- method used to calculate iNav
        std (float) -- sets the standard deviation of the returns 
        """
        self.initial_nav = initial_nav
        self.inav = initial_nav
        self.out_shares = out_shares
        self.prices = prices
        self.old_prices = prices
        self.market_values = market_value
        self.shares = market_value / prices
        self.calc_method = calc_method
        self.historical_nav = [initial_nav]
        self.std = std
        
    def price_change(self, p=0.1):
        self.old_prices = self.prices.copy()
        n = len(self.prices)
        random_indices = np.random.permutation(range(1, n))[:int(np.floor(n * p))]
        self.prices[random_indices] = self.prices[random_indices] + (np.random.randn((random_indices.shape[0])) * self.std)
        self.calc_inav(self.calc_method)
        self.historical_nav.append(self.inav)
        
    def calc_inav(self, method='full'):
        """
        Calculate the iNav. The first method calculates the dot product with all
        values the second calculates using only some values
        """
        price_diff = self.prices - self.old_prices
        if method == 'full':
            self.inav += (np.dot(price_diff, self.shares) / self.out_shares)
        # Partial is currently slower. Probably due to dot product of non-contigious array
        elif method == 'partial':
            altered_indices = np.nonzero(price_diff)
            y = np.zeros(len(altered_indices))
            x = np.zeros(len(altered_indices))
            y = price_diff[altered_indices]
            x = self.shares[altered_indices]
            self.inav += (np.dot(y, x) / self.out_shares)
    
    def run_simulation(self, iters=1000, method='full'):
        """ simulates the iNav

        """
        self.historical_nav = [self.initial_nav]
        self.calc_method = method
        tic = time.time()
        for x in range(iters):
            self.price_change()
        toc = time.time()
        return toc - tic

def ishares_parser(file):
    """
    Parser for the iShares excell files for their ETFs
    """
    f = open(file, 'r', encoding='utf-8-sig')
    s = ''
    while True:
        t = f.readline()
        if not t:
            break
        s = s + t
    s = bs(s, 'lxml')
    worksheets = s.find_all('ss:worksheet')
    
    df_list = []
    # Overview
    overview_columns = ['Parameter', 'Value']
    df_list.append(sheet_parser(worksheets[0], overview_columns, 5, 0))
    
    # Holdings
    holdings_columns = ['Issuer Ticker', 'Name', 'Asset Class', 'Weight', 'Price', 'Nominal', 'Market Value', 'Notional Value', 'Sector', 'ISIN', 'Coupon', 'Maturity', 'Exchange', 'Location', 'Market Currency', 'Duration']
    df_list.append(sheet_parser(worksheets[1], holdings_columns, 4, 0))
    
    # Historical
    historical_columns = ['As Of', 'Currency', 'NAV', 'Securities in Issue', 'Net Assets', 'Fund Return', 'Benchmark']
    df_list.append(sheet_parser(worksheets[2], historical_columns, 1, 0))
    
    # Performance
    performance_columns = ['Month End Date', 'Monthly Total']
    df_list.append(sheet_parser(worksheets[3], performance_columns, 5, 0))
    
    # Distributions
    distributions_columns = ['Announcement Date', 'ExDate', 'Payable Date', 'Total Distribution', 'Record Date']
    df_list.append(sheet_parser(worksheets[4], distributions_columns, 1, 0))
    
    return df_list

def find_values(df_overview, params):
    output_values = []
    for param in params:
        output_values.append(float(df_overview.loc[df_overview['Parameter'] == param].iloc[0, 1].replace(',', '').split(' ')[-1]))
    return output_values

def load_data(file_dir, folder=True, parser=ishares_parser):
    if folder:
        files = os.listdir(file_dir)
        worksheets = parser(files[0])
    else:
        worksheets = parser(file_dir)
    if parser == ishares_parser:
        vals = find_values(worksheets[0], ['Net Assets', 'Shares Outstanding', 'Net Assets of Fund'])
        initial_nav = calc_nav(vals[0], vals[1])
        etfs = ETFiNavSimulator(
            initial_nav,
            worksheets[1]['Price'].to_numpy(),
            worksheets[1]['Market Value'].to_numpy(),
            vals[1],
        )
        return etfs, worksheets

def calc_nav(asset_values, out_shares):
    return asset_values / out_shares


def sheet_parser(sheet, columns, header_skip=0, footer_skip=0):
    """
    Parser for excell sheets formatted in xml
    """
    rows = sheet.find_all('ss:row')
    data = []
    for row in rows[header_skip:]:
        row_list = []
        if row is not None:
            cell = row.find_all('ss:data')
            for values in cell:
                row_list.append(values.get_text())
            data.append(row_list)
    df = pd.DataFrame(data, columns=columns).infer_objects()
    to_numeric(df)
    return df

def to_numeric(df):
    for c in df.columns:
        try:
            df[c] = pd.to_numeric(df[c])
        except:
            pass

