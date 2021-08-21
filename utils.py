import os
from bs4 import BeautifulSoup as bs
import pandas as pd
import requests
import numpy as np


def generate_price_list(worksheet_dict):
    df = pd.DataFrame(columns=['Issuer Ticker', 'Price', 'ISIN'])
    initial_nav = []
    shares_outstanding = []
    for etf, worksheets in worksheet_dict.items():
        subset = worksheets[1][['Issuer Ticker', 'Price', 'ISIN']]
        df = df.append(subset, ignore_index=True)
        df = df.drop_duplicates(subset=['Issuer Ticker', 'ISIN'], ignore_index=True)
        vals = find_values(worksheets[0], ['Net Assets', 'Shares Outstanding', 'Net Assets of Fund'])
        initial_nav.append(calc_nav(vals[0], vals[1]))
        shares_outstanding.append(vals[1])
    return df, initial_nav, shares_outstanding

def generate_holdings_matrix(price_list, worksheet_dict):
    holdings_matrix = np.zeros((len(price_list), len(worksheet_dict)))
    for idx, (etf, worksheets) in enumerate(worksheet_dict.items()):
        temp_price = price_list.reset_index()
        temp_worksheet = worksheets[1][worksheets[1]['Price'] > 0 ]
        result = pd.merge(temp_price, temp_worksheet, on=['Issuer Ticker', 'ISIN']).set_index('index')
        # index = price_list.index[price_list[['Issuer Ticker']].isin(worksheets[1]['Issuer Ticker'])].tolist()
        # print(len(index), (worksheets[1]['Market Value']/worksheets[1]['Price']))
        holdings_matrix[result.index.tolist(), idx] = (temp_worksheet['Market Value']/temp_worksheet['Price'])
    return holdings_matrix


def get_files(etf_dict, website):
    for etf, etf_id in etf_dict.items():
        download_file(etf, etf_id, website)

def download_file(etf, etf_id, website):
    if not os.path.isfile('ishare_etfs/{}.xls'.format(etf)):
        if website == 'ishares':
            r = requests.get('https://www.ishares.com/uk/individual/en/products/{}/?switchLocale=y&siteEntryPassthrough=true'.format(etf_id))
            soup = bs(r.content, 'lxml')
            link = soup.find('a', {'class': 'icon-xls-export', 'data-link-event':'fund download:common'}, href=True)['href']
            r_download = requests.get('https://www.ishares.com' + link)

        with open('ishare_etfs/{}.xls'.format(etf), 'wb') as f:
            f.write(r_download.content)

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
    
    # # Historical
    # historical_columns = ['As Of', 'Currency', 'NAV', 'Securities in Issue', 'Net Assets', 'Fund Return', 'Benchmark']
    # df_list.append(sheet_parser(worksheets[2], historical_columns, 1, 0))
    
    # # Performance
    # performance_columns = ['Month End Date', 'Monthly Total']
    # df_list.append(sheet_parser(worksheets[3], performance_columns, 5, 0))
    
    # # Distributions
    # if len(worksheets) > 4:
    #     distributions_columns = ['Announcement Date', 'ExDate', 'Payable Date', 'Total Distribution', 'Record Date']
    #     df_list.append(sheet_parser(worksheets[4], distributions_columns, 1, 0))
    
    return df_list

def load_sheets(file_dir, etf_dict, parser=ishares_parser):
    worksheet_dict = {}
    for etf in etf_dict.keys():
        print(etf)
        worksheet_dict[etf] = parser('{}{}.xls'.format(file_dir, etf))[:2]
    return worksheet_dict

    # if parser == ishares_parser:
    #     vals = find_values(worksheets[0], ['Net Assets', 'Shares Outstanding', 'Net Assets of Fund'])
    #     initial_nav = calc_nav(vals[0], vals[1])
    #     etfs = ETFiNavSimulator(
    #         initial_nav,
    #         worksheets[1]['Price'].to_numpy(),
    #         worksheets[1]['Market Value'].to_numpy(),
    #         vals[1],
    #     )

def find_values(df_overview, params):
    output_values = []
    for param in params:
        output_values.append(float(df_overview.loc[df_overview['Parameter'] == param].iloc[0, 1].replace(',', '').split(' ')[-1]))
    return output_values



def calc_nav(asset_values, out_shares):
    return asset_values / out_shares


