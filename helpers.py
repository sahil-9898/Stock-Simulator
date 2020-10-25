import csv
import urllib.request
from nsetools import Nse
nse=Nse()

from flask import redirect, render_template, request, session, url_for
from functools import wraps

def apology(top="", bottom=""):
    """Renders message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
            ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=escape(top), bottom=escape(bottom))

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
        stockdetails=nse.get_quote(symbol)
        price = stockdetails['buyPrice1']
        if price==None:
            price = stockdetails['lastPrice']
        return {
            "name": stockdetails['companyName'],
            "price": price,
            "symbol": symbol.upper()
        }
    else:
        return None

def rs(value):
    """Formats value as RUPPEE."""
    return "₹{:,.2f}".format(value)