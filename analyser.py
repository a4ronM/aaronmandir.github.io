import openpyxl 
import yfinance as yf #loads finance library 
import pandas as pd
import numpy as np
import os



holdings_file = "holdings.xlsx"
pie_files = []
for file in os.listdir():
    if file.startswith("pie_") and file.endswith(".xlsx") and not file.startswith("~$"):
        pie_files.append(file)

# build the menu options
options = [holdings_file] + pie_files + ["EVERYTHING"]

# show the menu
print("\nWhich would you like to analyse?")
for number, option in enumerate(options, start=1):
    print(f"  {number}. {option}")

# get the user's choice
choice = int(input("Enter a number: "))
chosen = options[choice - 1]

print("You chose:", chosen)

# figure out which files to read based on the choice
if chosen == "EVERYTHING": # holding file plus all the pie files
    files_to_read = [holdings_file] + pie_files
else:
    files_to_read = [chosen] # just one file chosen 

# read holdings from all chosen files into one list
holdings = []
for filename in files_to_read: # loops through each file we need to read
    wb = openpyxl.load_workbook(filename) # load file and grab sheet
    ws = wb.active
    for row in ws.iter_rows(min_row=2, values_only=True): # inner loops reads the holdings
        name = row[0]
        ticker = row[1]
        amount = row[2]
        if ticker is not None:          # skip blank rows
            holdings.append({"name": name, "ticker": ticker, "amount": amount})

print(f"Analysing {len(holdings)} holdings") # prints holdings found 
print(holdings)


#test
# test = yf.Ticker("VWRL.L") 
# data = test.history(period = "1y")
# print(data[["Open", "Close", "Volume"]])

## understanding calculation for one harcoded ticker

# #fetch one ticker and get its closing price 
# stock = yf.Ticker("VWRL.L")
# prices = stock.history(period ="1y")["Close"].dropna()

# #Calculate return: how much it grew over the year
# start_price = prices.iloc[0]
# end_price = prices.iloc[-1]
# total_return = (end_price / start_price) -1

# print("Start price:", start_price)
# print("End price:", end_price)
# print("Retrun:", total_return)

# # calculate volatility: how much price bounced around (risk)
# daily_returns = prices.pct_change().dropna() # calculates % change form one dat to next 
# volatility = daily_returns.std() # standard deviation, spread 
# print("Volatility (daily):", volatility)

# # annulaise the volatility (scale daily to yearly)
# annual_volatility = volatility * (252 ** 0.5) # 252 = num of trading days a year 
# print("Volatility (annual):", annual_volatility)

# analyse every holding 
for holding in holdings:
    ticker = holding["ticker"]
    print ("Fetching:", ticker)

    # fetch prices for this holding 
    stock = yf.Ticker(ticker)
    prices = stock.history (period ="1y")["Close"].dropna()

    # return 
    total_return = (prices.iloc[-1] / prices.iloc[0]) -1

    # volatility (annualised)
    daily_returns = prices.pct_change().dropna()
    annual_volatility = daily_returns.std() * (252 ** 0.5)

    # stpre the result back into this holding's dictionary
    holding["return"] = total_return
    holding["volatility"] = annual_volatility

    # print a summary line for this holding 
    print(f"{holding['name']}: return {total_return:.1%}, volatility {annual_volatility:.1%}")

# total amount invested across all holdings 
total_invested = 0 #starts running total at zero
for holding in holdings: # loop through every holding 
    total_invested = total_invested + holding["amount"]

print("Total invested: £", total_invested)

# calculate each holding's % of the portfolio
for holding in holdings:
    weight = holding["amount"] / total_invested
    holding["weight"] = weight
    print(f"{holding['name']}: {weight:.1%} of portfolio")

# portfolio return = weaighted average of each holding's return
portfolio_return = 0 # running total starting at 0 
for holding in holdings: # each loop adds weight x return - each holdings return scaled by its share of the portfolio
    portfolio_return = portfolio_return + (holding["weight"] * holding["return"])

print(f"Portfolio return: {portfolio_return:.1%}")

# naive portfolio risk = weighted average of volatilities
# (this OVERSTATES risk - it ignores diversification)
naive_risk = 0
for holding in holdings: 
    naive_risk = naive_risk + (holding["weight"] * holding["volatility"])

print(f"Naive portfolio risk (ignored diversification): {naive_risk:.1%}")

# gather daily returns for all holdings into one table 
returns_table = pd.DataFrame() # creates empty data frame
for holding in holdings: # fetches prices for each holdings
    stock = yf.Ticker(holding["ticker"])
    prices = stock.history(period ="1y")["Close"].dropna()
    prices.index = prices.index.tz_localize(None).normalize()
    returns_table[holding["ticker"]] = prices.pct_change()

returns_table = returns_table.dropna()
print(returns_table.head())

# correlation matrix: how the holdings move relative to each other
correlation = returns_table.corr()
print(correlation)

# weight and volatility lists in the same order as the correlation matrix
tickers = list(returns_table.columns) # gets the ticker order form correlation matrix, so weighst and vols line up in same order as matrix
weights = np.array([next(h["weight"] for h in holdings if h["ticker"] == t) for t in tickers]) # looks up each tickers weight from your holdings list
vols = np.array([next(h["volatility"] for h in  holdings if h["ticker"] == t) for t in tickers]) 

# convariance matrix = how each pair of holdings varies together
cov_matrix = correlation.values * np.outer(vols, vols) # builds the coveriance matrix = correlation scaled by 2 volatilities

# portfolio variance, then volatility (the proper, diversification-adjusted risk)
portfolio_variance = weights @ cov_matrix @ weights # martrix multiplication. Portfolio vairance formula
portfolio_risk = portfolio_variance ** 0.5 # sqaure root of variance = volatility = risk figrue

print(f"Proper portfolio risk (with diversification): {portfolio_risk:.1%}")

# claissfy the portfolios risk level 
if portfolio_risk < 0.08:
    risk_rating = "Low"
elif portfolio_risk < 0.15:
    risk_rating = "Moderate"
else:
    risk_rating = "High"

print(f"Risk rating: {risk_rating}")

# readability 
print("\n----- PORTFOLIO SUMMARY -----")
print(f"Total invested: £{total_invested:,.0f}")
print(f"Expected return: {portfolio_return:.1%}")
print(f"Risk (volatility): {portfolio_risk:.1%}")
print(f"Diversification benefit: {(naive_risk - portfolio_risk):.1%} risk reduced")
print("\nAllocation:")
for holding in holdings:
    print(f"   - {holding['name']}: {holding['weight']:.0%}")


# Excel report build

report = openpyxl.Workbook() # Creates new blank workbook
rs = report.active 
rs.title = "Portfolio Report" # get sheet + name portfolio report

# Summary section 
rs["A1"] = "PORTFOLIO ANALYSIS REPORT"
rs["A3"] = "Total Invested"
rs["B3"] = total_invested
rs["A4"] = "Expected Return"
rs["B4"] = portfolio_return
rs["A5"] = "Risk (Volatility)"
rs["B5"] = portfolio_risk
rs["A6"] = "Risk Rating"
rs["B6"] = risk_rating
rs["A7"] = "Diversification Benefit"
rs["B7"] = naive_risk - portfolio_risk

rs["A10"] = "Holding"
rs["B10"] = "Allocation"
rs["C10"] = "Return"
rs["D10"] = "Volatility"

row_num = 11
for holding in holdings:
    rs[f"A{row_num}"] = holding["name"]
    rs[f"B{row_num}"] = holding["weight"]
    rs[f"C{row_num}"] = holding["return"]
    rs[f"D{row_num}"] = holding["volatility"]
    row_num = row_num + 1


print("Report saved: portfolio_report.xlsx")

# Formatting 
# Percentage cells in the summary
rs["B4"].number_format = "0.0%"   # Expected Return
rs["B5"].number_format = "0.0%"   # Risk
rs["B7"].number_format = "0.0%"   # Diversification Benefit
rs["B3"].number_format = "£#,##0" # Total Invested

# Percentage cells in the per holding table
for r in range(11, 11 + len(holdings)):
    rs[f"B{r}"].number_format = "0.0%"   # Allocation
    rs[f"C{r}"].number_format = "0.0%"   # Return
    rs[f"D{r}"].number_format = "0.0%"   # Volatility

from openpyxl.styles import Font, PatternFill, Alignment

# --- title styling ---
rs["A1"].font = Font(size=14, bold=True, color="FFFFFF")
rs["A1"].fill = PatternFill("solid", fgColor="14304A")
rs.merge_cells("A1:D1")   # stretch title across columns A-D
rs["A1"].alignment = Alignment(horizontal="left", vertical="center")

# --- bold the summary labels ---
for r in range(3, 8):
    rs[f"A{r}"].font = Font(bold=True)

# --- style the holding-table header row ---
for col in ["A", "B", "C", "D"]:
    cell = rs[f"{col}10"]
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor="14304A")

# --- widen columns so nothing is cut off ---
rs.column_dimensions["A"].width = 22
rs.column_dimensions["B"].width = 14
rs.column_dimensions["C"].width = 12
rs.column_dimensions["D"].width = 12

from openpyxl.chart import PieChart, Reference

# --- allocation pie chart ---
pie = PieChart()
pie.title = "Portfolio Allocation"

# data = the allocation column (B), labels = the names column (A)
labels = Reference(rs, min_col=1, min_row=11, max_row=10 + len(holdings))
data = Reference(rs, min_col=2, min_row=10, max_row=10 + len(holdings))
pie.add_data(data, titles_from_data=True)
pie.set_categories(labels)

# place the chart on the sheet (anchor at cell F3)
rs.add_chart(pie, "F3")

report.save("portfolio_report.xlsx")