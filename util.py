import re
import htmlentitydefs
import requests
from settings import CHANNEL, SHORTENER
from xml.dom import minidom as dom


# Utility functions

def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text
    return re.sub("&#?\w+;", fixup, text)


# instead of presuming to predict what
# will be colored, make it easy to prep
# string elements
def colorize(text, color):
    colors = {
        "white": 0,
        "black": 1,
        "blue": 2,
        "green": 3,
        "red": 4,
        "brown": 5,
        "purple": 6,
        "orange": 7,
        "yellow": 8,
        "lightgreen": 9,
        "teal": 10,
        "lightcyan": 11,
        "lightblue": 12,
        "pink": 13,
        "grey": 14,
        "lightgrey": 15,
    }
    if isinstance(color, str):
        color = colors[color]

    return "\x03" + str(color) + text + "\x03"



def pageopen(url, params={}):
    try:
        headers = {'User-agent': '(Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.17 Safari/537.36'}
        urlbase = requests.get(url, headers=headers, params=params)
    except:
        return False

    return urlbase

def shorten(url):
    try:
        short_url = requests.get(SHORTENER, params={'roast': url}).text
    except:
        return ''

    return short_url

# Utility classes

class Stock(object):

    def __init__(self, symbol):

        self.stock = None
        self.symbol = symbol
        self.price = 0

        if not symbol:
            return

        # google specific
        singlestock = "http://query.yahooapis.com/v1/public/yql?env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys&q=select%20*%20from%20yahoo.finance.quotes%20where%20symbol%20%3D%20'"
        url = singlestock + symbol + "'"

        try:
            raw = dom.parse(pageopen(url))
        except:
            return

        self.stock = self.extract(raw)

    def __nonzero__(self):
        return self.stock is not None

    # Extracts from google api
    def extract(self, raw):

        elements = [e for e in raw.childNodes[0].childNodes[0].childNodes[0].childNodes if e.firstChild != None]

        # in the future, can just change translation
        # point is to end up with an object that won't
        # change when the api changes.

        translation = {
            "Symbol": "symbol",
            #"pretty_symbol": "pretty_symbol",
            #"symbol_lookup_url": "symbol_lookup_url",
            "Name": "company",
            "StockExchange": "exchange",
            #"exchange_timezone": "exchange_timezone",
            #"exchange_utc_offset": "exchange_utc_offset",
            #"exchange_closing": "exchange_closing",
            #"divisor": "divisor",
            #"currency": "currency",
            "LastTradePriceOnly": "_last",
            "AskRealtime" : "_ask_realtime",
            "BidRealtime" : "_bid_realtime",
            "DaysHigh": "high",
            "DaysLow": "low",
            "Volume": "volume",
            "AverageDailyVolume": "avg_volume",
            "MarketCapitalization": "market_cap",
            "Opeb": "open",
            "PreviousClose": "y_close",
            "Change": "_change",
            "ChangeinPercent": "_perc_change",
            #"delay": "delay",
            #"trade_timestamp": "trade_timestamp",
            "LastTradeDate": "trade_date_utc",  #May not actually be UTC
            "LastTradeTime": "trade_time_utc", #May not actually be UTC
            #"current_date_utc": "current_date_utc",
            #"current_time_utc": "current_time_utc",
            #"symbol_url": "symbol_url",
            #"chart_url": "chart_url",
            #"disclaimer_url": "disclaimer_url",
            #"ecn_url": "ecn_url",
            #"isld_last": "isld_last",
            #"isld_trade_date_utc": "isld_trade_date_utc",
            #"isld_trade_time_utc": "isld_trade_time_utc",
            #"brut_last": "brut_last",
            #"brut_trade_date_utc": "brut_trade_date_utc",
            #"brut_trade_time_utc": "brut_trade_time_utc",
            #"daylight_savings": "daylight_savings",
        }
        extracted = {}

        for e in elements:
            data = e.firstChild.nodeValue
            if translation.has_key(e.tagName):
                extracted[translation[e.tagName]] = data
                setattr(self, translation[e.tagName], data)

        if not self.company:
            return None

        if self._ask_realtime != None:
            self.price = float(self._ask_realtime)
        elif self._bid_realtime != None:
            self.price = float(self._bid_realtime)
        else:
            self.price = float(self._last)

        try:
            self.change = float(self._change)
            self.perc_change = float(self._perc_change[0:-1]) #trim % off
        except:
            self.change = 0
            self.perc_change = 0

        return extracted

    def showquote(self, context):
        if not self.stock:
            return False

        name = "%s (%s)" % (self.company, self.symbol)
        changestring = str(self.change) + " (" + ("%.2f" % self.perc_change) + "%)"

        if self.change < 0:
            color = "4"
        else:
            color = "3"

        changestring = "\x03" + color + " " + changestring + "\x03"

        message = [
            name,
            str(self.price),
            changestring,
        ]

        otherinfo = [
            # ("pretty title", "dataname")
            ("Exchange", "exchange"),
            ("Trading volume", "volume"),
            ("Market cap", "market_cap"),
        ]

        if context != CHANNEL:
            for item in otherinfo:
                pretty, id = item
                addon = pretty + ": " + self.stock[id]
                message.append(addon)

        link = "http://www.google.com/finance?client=ig&q=" + self.stock["symbol"]
        try:
            roasted = shorten(link)
            message.append(roasted)
        except:
            message.append("Can't link")


        output = ', '.join(message)

        return output
