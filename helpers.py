from functools import wraps
from flask import redirect, render_template, request, session, url_for
import csv
import urllib.request
from nsetools import Nse
import json
import requests
nse = Nse()


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.11/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    valid = nse.is_valid_code(symbol)
    if valid == True:
        stockdetails = nse.get_quote(symbol)
        price = stockdetails['buyPrice1']
        if price == None:
            price = stockdetails['lastPrice']
        return {
            "name": stockdetails['companyName'],
            "price": price,
            "symbol": symbol.upper()
        }
    else:
        return None


def is_valid(symbol):
    valid = nse.is_valid_code(symbol)
    if valid == True:
        return {
            "symbol": symbol.upper()
        }
    else:
        return None


def lookup2(symbol):
    url = "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=" + \
        symbol+".BO&apikey=ZT190HZDN99BS851"
    res = requests.get(url)
    res2 = json.loads(res.text)
    result = res2['Global Quote']
    if len(result) == 0:
        return None
    else:
        x = float(result['05. price'])
        return x
