import os
import numpy as np
import pandas as pd
import time

class ETFiNavSimulator():
    def __init__(self, initial_nav, prices, holdings_matrix, out_shares, calc_method='full', std=2):
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
        self.holdings_matrix = holdings_matrix
        self.calc_method = calc_method
        self.historical_nav = [initial_nav]
        self.std = std
        
    def price_change(self, p=0.1):
        self.old_prices = self.prices.copy()
        n = len(self.prices)
        random_indices = np.random.permutation(range(1, n))[:int(np.floor(n * p))]
        self.prices[random_indices] = self.prices[random_indices] + (np.random.randn((random_indices.shape[0])) * self.std) + 0.01
        self.calc_inav(self.calc_method)
        self.historical_nav.append(self.inav)
        
    def calc_inav(self, method='full'):
        """
        Calculate the iNav. The first method calculates the dot product with all
        values the second calculates using only some values
        """
        price_diff = self.prices - self.old_prices
        if method == 'full':
            self.inav += np.matmul(price_diff.T, self.holdings_matrix) / self.out_shares
        # Partial is currently slower. Probably due to dot product of non-contigious array
        elif method == 'partial':
            altered_indices = np.nonzero(price_diff)
            y = np.zeros(len(altered_indices))
            x = np.zeros(len(altered_indices))
            y = price_diff[altered_indices]
            x = self.shares[altered_indices]
            self.inav += np.matmul(price_diff[altered_indices].T, self.holdings_matrix[altered_indices]) / self.out_shares
    
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

