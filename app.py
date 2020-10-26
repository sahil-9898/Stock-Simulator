from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session,url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["rs"] = rs

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

@app.route("/")
@login_required
def index():
    symbol=list()
    share=list()
    price=list()
    total=list()
    # total=[]
    sy = db.execute("SELECT symbol FROM portfolio WHERE id = :id", id= session['user_id'])
    sh = db.execute("SELECT shares FROM portfolio WHERE id = :id", id= session['user_id'])
    pr = db.execute("SELECT price FROM portfolio WHERE id = :id", id= session['user_id'])
    for i in range (len(sy)):
        symbol.append(sy[i]["symbol"].upper())
    for i in range (len(sh)):
        share.append(sh[i]["shares"])  
    for i in range (len(pr)):
        price.append(pr[i]["price"])
    # templates=dict(symbols=symbol,shares=share,prices=price)
    for i in range(len(symbol)):
        total.append(price[i]*share[i])
    data = zip(symbol,share,price,total)
    sum = 0.0
    for i in range(len(total)):
        sum+=total[i]
    for i in range(len(total)):
        total[i]=str(total[i])
    cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    # cash = float("{:.2f}".format(rows[0]["cash"]))
    sum+=cash[0]["cash"]
    user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    return render_template("index.html", data=data, sum=sum, cash=cash[0]["cash"], user=user[0]["username"])
    
@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock."""
    user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    if request.method == "POST":
        stock = lookup(request.form.get("symbol"))
        if stock is None:
            flash("Invalid Stock", "error")
            return redirect(url_for("buy"))
        amount = request.form.get("shares")
        if not amount.isdigit() or (int(amount))%1!=0 or (int(amount))<=0:
            flash("Invalid Shares!", "error")
            return redirect(url_for("buy"))
        
        if cash[0]["cash"] > float(amount)*stock["price"]:
            unique = db.execute("INSERT INTO portfolio (id, symbol, shares, price) VALUES(:id, :symbol, :shares, :price)", id= session['user_id'], symbol=request.form.get("symbol"), shares=request.form.get("shares"), price=stock["price"])
            db.execute("INSERT INTO history (id, symbol, shares, price) VALUES(:id, :symbol, :shares, :price)", id= session['user_id'], symbol=request.form.get("symbol"), shares=request.form.get("shares"), price=stock["price"])
            if not unique:
                temp = db.execute("SELECT shares FROM portfolio WHERE id=:id AND symbol=:symbol", id= session['user_id'], symbol=request.form.get("symbol"))
                db.execute("UPDATE 'portfolio' SET shares=:shares WHERE id=:id AND symbol=:symbol", shares=temp[0]["shares"]+int(request.form.get("shares")), id=session['user_id'], symbol=request.form.get("symbol"))
            db.execute("UPDATE 'users' SET cash=:cash WHERE id=:id", cash=(cash[0]["cash"])-(float(amount)*stock["price"]), id= session['user_id'])
        else:
            flash("Not Enough Balance", "error")
            return redirect(url_for("buy"))
        flash("Shares Bought", "success")
        return redirect(url_for("portfolio"))
        
    else:
        return render_template("buy.html",user=user[0]["username"], cash=cash[0]["cash"])

@app.route("/history")
@login_required
def history():
    user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    symbol=list()
    share=list()
    price=list()
    transacted=list()
    # total=[]
    sy = db.execute("SELECT symbol FROM history WHERE id = :id", id= session['user_id'])
    sh = db.execute("SELECT shares FROM history WHERE id = :id", id= session['user_id'])
    pr = db.execute("SELECT price FROM history WHERE id = :id", id= session['user_id'])
    tr = db.execute("SELECT transacted FROM history WHERE id = :id", id= session['user_id'])
    for i in range (len(sy)):
        symbol.append(sy[i]["symbol"].upper())
    for i in range (len(sh)):
        share.append(sh[i]["shares"])  
    for i in range (len(pr)):
        price.append(pr[i]["price"])
    for i in range (len(tr)):
        transacted.append(tr[i]["transacted"])
    data = zip(symbol,share,price,transacted)
    return render_template("history.html", data=data, user=user[0]["username"], cash=cash[0]["cash"])

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Invalid Username/Password", "error")
            return redirect(url_for("login"))

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        flash("success", "welcome")
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""
    
    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    if request.method == "POST":
        result = lookup(request.form.get("symbol"))
        if result is None:
            flash("invalid stock!!", "error")
            return render_template("quote.html")
        else:
            return render_template("quoted.html", name=result["name"], symbol=result["symbol"], price=result["price"], user=user[0]["username"], cash=cash[0]["cash"])
    else:
      return render_template("quote.html", user=user[0]["username"], cash=cash[0]["cash"])  

    

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username=request.form.get("username")
        password=request.form.get("password")
        password2=request.form.get("password2")

        # ensure username was submitted
        if not username:
            return apology("must provide username")

        # ensure password was submitted
        elif not password:
            return apology("must provide password")
            
        elif not password2:
            return apology("must re-enter password")
            
        if password!=password2:
             return apology("passwords do not match")
        
        hash = generate_password_hash(password)
        
        result = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)", username=username, hash=hash)
        if not result:
            flash("Username Already Exists", "error")
            return redirect(url_for("register"))
        flash("New user registered", "success")
        return render_template("login.html")

    else:    
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    """Sell shares of stock."""
    if request.method == "POST":
        stock = lookup(request.form.get("symbol"))
        if stock is None:
            flash("Invalid Stock", "error")
            return redirect(url_for("sell"))
        amount = request.form.get("shares")
        sy = db.execute("SELECT shares FROM portfolio WHERE id = :id AND symbol=:symbol", id= session['user_id'], symbol=request.form.get("symbol"))
        if not sy:
            flash("You dont own this Stock", "error")
            return redirect(url_for("sell"))
        if not amount.isdigit() or (int(amount))%1!=0 or (int(amount))<=0 or int(amount)>sy[0]["shares"]:
            flash("Invalid Shares", "error")
            return redirect(url_for("sell"))
        if (sy[0]["shares"]==int(amount)):
            db.execute("DELETE from 'portfolio' WHERE id = :id AND symbol=:symbol",id= session['user_id'], symbol=request.form.get("symbol") )
        else:
            db.execute("UPDATE 'portfolio' SET shares=:shares WHERE id=:id AND symbol=:symbol", shares=sy[0]["shares"]-int(request.form.get("shares")), id=session['user_id'], symbol=request.form.get("symbol"))
        db.execute("INSERT INTO history (id, symbol, shares, price) VALUES(:id, :symbol, :shares, :price)", id= session['user_id'], symbol=request.form.get("symbol"), shares=-int(request.form.get("shares")), price=stock["price"])
        profit = stock["price"]*int(amount)
        temp = db.execute("SELECT cash FROM users WHERE id=:id",id= session['user_id'])
        db.execute("UPDATE 'users' SET cash=:cash WHERE id=:id", cash=temp[0]["cash"]+profit, id= session['user_id'])
        flash("Shares Sold", "success")
        return redirect(url_for("portfolio"))
        
    else:
        return render_template("sell.html", user=user[0]["username"], cash=cash[0]["cash"])


@app.route("/changepass", methods=["GET", "POST"])
@login_required
def changepass():
    user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    """Change password."""
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("oldpass"):
            return apology("must provide current password")
        
        # ensure password was submitted
        elif not request.form.get("newpass"):
            return apology("must provide new password")
            
        elif not request.form.get("newpass2"):
            return apology("must re-enter new password")
        
        oldpasscheck = db.execute("SELECT hash FROM users WHERE id = :id", id= session['user_id'])
        
        if not check_password_hash(oldpasscheck[0]["hash"] ,request.form.get("oldpass")):
            flash("This is not your current password!", "error")
            return redirect(url_for("changepass"))
            
        if request.form.get("newpass")!=request.form.get("newpass2"):
            flash("New password do not match", "error")
            return redirect(url_for("changepass"))
        
        hashed = generate_password_hash(request.form.get("newpass"))
        
        db.execute("UPDATE 'users' SET hash=:hash WHERE id=:id", hash=hashed, id= session['user_id'])
        flash("Password Successfully Changed", "success")
        
        return redirect(url_for("index"))

    else:    
        return render_template("changepass.html", user=user[0]["username"], cash=cash[0]["cash"])

@app.route("/portfolio")
@login_required
def portfolio():
    user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    symbol=list()
    share=list()
    price=list()
    latest=list()
    cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    sy = db.execute("SELECT symbol FROM portfolio WHERE id = :id", id= session['user_id'])
    sh = db.execute("SELECT shares FROM portfolio WHERE id = :id", id= session['user_id'])
    pr = db.execute("SELECT price FROM portfolio WHERE id = :id", id= session['user_id'])
    if len(sy)!=0:
        for i in range (len(sy)):
            symbol.append(sy[i]["symbol"].upper())
            prc=lookup(sy[i]["symbol"])
            latest.append(prc["price"])
        for i in range (len(sh)):
            share.append(sh[i]["shares"])  
        for i in range (len(pr)):
            price.append(pr[i]["price"])
        # templates=dict(symbols=symbol,shares=share,prices=price)
        data = zip(symbol,share,price,latest)
        inv_amt=list()
        gl=list()
        for i in range (len(sy)):
            gl.append((latest[i]-price[i])*share[i])
            inv_amt.append(price[i]*share[i])
        lat_value=sum(inv_amt)+sum(gl)
        top_gain_index=gl.index(max(gl))
        top_loss_index=gl.index(min(gl))
        top_gain_symbol=symbol[top_gain_index]
        top_loss_symbol=symbol[top_loss_index]
        overall_gl=sum(gl)
        return render_template("portfolio.html",data=data,lat_value=lat_value,top_gain=top_gain_symbol,top_loss=top_loss_symbol,overall_gl=overall_gl,cash=cash[0]["cash"], user=user[0]["username"])
    else:
        return render_template("portfolio.html",lat_value=0,top_gain='-',top_loss='-',overall_gl=0,cash=cash[0]["cash"], user=user[0]["username"])

@app.route("/wallet", methods = ['GET', 'POST'])
@login_required
def wallet():
    user = db.execute("SELECT username FROM users WHERE id = :id", id= session['user_id'])
    cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
    if request.method=='POST':
        amount=request.form.get("amount")
        if not amount.isdigit() or int(amount)<=0:
            flash("Invalid Amount", "error")
            return redirect(url_for("wallet"))
        else:
            db.execute("UPDATE users SET cash=cash+ :amount WHERE id=:x",amount=amount,x=session["user_id"])
            cash = db.execute("SELECT cash FROM users WHERE id=:id", id= session['user_id'])
            flash("amount added", "success")
            return render_template("wallet.html",cash=cash[0]["cash"], user=user[0]["username"])
    else:
        return render_template("wallet.html",cash=cash[0]["cash"], user=user[0]["username"])
