import os
from ETFiNavSimulator import *

# Load excel spreadsheet
etfs, worksheets = load_data('iShares--Corp-Bond-UCITS-ETF-USD-Dist-USD-Distributing_fund.xls', folder=False)


# Run simulation
time = etfs.run_simulation()
inav = etfs.inav

print("Time: {}".format(time))
print("initial Nav: {}".format(etfs.initial_nav))
print("iNav: {}".format(inav))