import requests #python fetches data from internet
import yfinance as yf # pulls share price data from Yahoo finance
import numpy as np # used for correlation calc
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer # the sentiment scorer

API_KEY = "53e1a66f0a674b438f5eac2206d3ca19"

analyzer = SentimentIntensityAnalyzer() # create the sentiment scorer once, ready to use

companies = {                     # bank name (for news search) -> stock ticker (for the price)
    "UBS": "UBS",
    "Goldman Sachs": "GS",
    "Deutsche Bank": "DB",
    "Barclays": "BCS",
    "HSBC": "HSBC",
    "JPMorgan": "JPM",
}

def get_average_sentiment(company):          # reusable function: give it a company, get back its average sentiment
    url = "https://newsapi.org/v2/everything"
    params = {
        "qInTitle": company,     # the name must be in the HEADLINE - keeps articles actually about the bank
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 20,          # up to 20 articles, for a more reliable average
        "apiKey": API_KEY,
    }
    data = requests.get(url, params = params).json()
    if data.get("status") != "ok":            # request failed
        print("  Error for", company, ":", data.get("message"))
        return None, 0
    articles = data["articles"]
    if len(articles) == 0:        # no articles found
        return None, 0

    scores = [] # an array to collect each headlines socre
    for article in articles:
        scores.append(analyzer.polarity_scores(article["title"])["compound"])
    return sum(scores) / len(scores), len(articles)

def get_price_change(ticker):                    # give it a ticker, get back its share price % move over ~1 month
    stock = yf.Ticker(ticker)                    # look the compnay up on Yahoo Finance
    history = stock.history(period = "1mo")     # get ~1 month of daily prices
    if history.empty:                            # nothing came back
        return None
    start_price = history["Close"].iloc[0] # price ~1 month ago
    end_price = history["Close"].iloc[-1]  # most recent price
    return (end_price / start_price) -1    # fractional change: 0.05 means +5%

sentiment_values = []  # collect each banks sentiment here
price_values = []      # collect each banks price move here


print(f"{'Bank':15}{'Sentiment':>12}{'1M Price':>12}\n")
for company, ticker in companies.items():    # loop over each name AND its ticker together
    sentiment, count = get_average_sentiment(company)
    price_change = get_price_change(ticker)

    sentiment_text = f"{sentiment:+.2f}" if sentiment is not None else "n/a"   # format, or "n/a" if missing
    price_text = f"{price_change:+.1%}" if price_change is not None else "n/a"
    print(f"{company:15}{sentiment_text:>12}{price_text:>12}")

    if sentiment is not None and price_change is not None: # only keep banks where we have both numbers
        sentiment_values.append(sentiment)
        price_values.append(price_change)

# after the loop, measure how closely the two columsn move together
correlation = np.corrcoef(sentiment_values, price_values)[0, 1]
print(f"\nCorrelation between sentiment and 1-month price move: {correlation:+.2f}")
        
