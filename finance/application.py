import os

# from cs50 import SQL
import sqlalchemy
from sqlalchemy import create_engine
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True



# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
# db = SQL("sqlite:///finance.db")
db = create_engine("sqlite:///finance.db")


# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    row = db.execute("SELECT * FROM stock WHERE stock_id = :id", id=session["user_id"])
    cash = db.execute("SELECT cash FROM users WHERE id= :id", id = session["user_id"])


    row = row.fetchall()
    cash = cash.fetchall()
    cash = cash[0][0]

    # Деньги пользователя, с учётом средств, которые он может получить с продажи акции
    current_cash = cash


    # Обновляем данные о ценнах акций
    for i in range(len(row)):
        element = list(row[i])
        info = lookup(element[1])
        # Созраняем символ акции
        element.append(element[1])
        element[0] = info["price"]
        element[1] = info["name"]
        # Сохраняем количество акций
        element.append(element[2])
        # Общая стоимость покупки
        element[2] = element[0] * element[2]
        current_cash += element[2]
        row[i] = element

    return render_template("index.html", rows = row, cashs = current_cash, current = cash)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        # Получаем данные из формы
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))

        # Проверяем, ввёл ли пользователь символ

        if not symbol:
            return apology("missing symbol", 400)

        # Проверяем, ввёл ли пользователь количество акций
        elif not shares:
            return apology("missing shares", 400)

        # Получаем данные об акциях
        info = {}
        info = lookup(symbol)
        if not info:
            return apology("invalid symbol", 400)
        else:
            # Получаем данные о кошелке пользователя
            cash = db.execute("SELECT cash FROM users WHERE id =:user_id", user_id=session["user_id"])
             #Выясняем, сможет ли пользователь себе это позволить
            cost = info["price"] * int(shares)
            cash = cash.fetchall()
            cash = cash[0][0]

            if cost > cash:
                return apology("can't afford", 400)
            else:

                # !!!Мне кажется cash менять не нужно (Оказалось, что нужно)
                cash -= cost

                db.execute("UPDATE users SET CASH = :cash WHERE id = :id", id = session["user_id"], cash = cash)

                db.execute("INSERT INTO stock (stock_id, stock_name, count) VALUES (:stock_id, :name, :count)", stock_id = session["user_id"], name = symbol, count = shares)
                flash("Bought!")

                return redirect("/")


    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        rows = rows.fetchall()
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "POST":
        symbol = request.form.get("symbol")
        info = {}
        info = lookup(symbol)
        if info:
            return render_template("quoted.html", name=info["name"], symbol=info["symbol"], price=info["price"])
        else:
            return apology("invalid symbol", 400)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    # Пользователь достиг пути через POST-запрос
    if request.method == "POST":
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        # Проверяем, получено ли имя пользователя
        if not password:
            return apology("Missing password", 400)
        elif password != confirmation:
            return apology("Passwords do not match", 403)
        name = request.form.get("username")
        password = generate_password_hash(password)
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=name, hash=password)
        id = db.execute("SELECT id from users WHERE username = :username", name)
        id = id.fetchall()

        # Запоминаем пользователя, который только что зарегистрировался
        session["user_id"] = id[0][0]

        flash("Registered!")
        return redirect("/")
    else:
        return render_template("register.html")

    """Register user"""



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    if request.method == "POST":
        # Получаем информацию об акции
        info = {}
        symbol = request.form.get("symbol")

        if not symbol:
            return apology("missing symbol", 400)

        info = lookup(symbol)
        price = info["price"]


        # Получаем количесво денег у пользователя
        cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id = session["user_id"])
        cash = cash.fetchall()
        cash = cash[0][0]

        #Получаем количество акций
        shares = request.form.get("shares")

        if not shares:
            return apology("MISSING SHARES", 400)

        shares = int(shares)

        share_old = db.execute("SELECT count FROM stock WHERE stock_id = :id", id = session["user_id"])
        share_old = share_old.fetchall()
        share_old = share_old[0][0]



        if share_old < shares :
            return apology("TOO MANY SHARES", 400)



        # Вычисляем стоимость
        cost = price * shares



        # Прибавляем стоимость к деньгам пользователя
        cash += cost

        # Обновляем данные о деньгах
        db.execute("UPDATE users SET cash = :cash WHERE id = :id", id = session["user_id"], cash = cash)

        # Обновляем данные об акциях пользователя
        share_old -= shares

        db.execute("UPDATE stock SET count = :share WHERE stock_id = :id", id = session["user_id"], share = share_old)
        db.execute("DELETE FROM stock WHERE count = 0")

        return redirect("/")

    else:
        symbols = db.execute("SELECT stock_name FROM stock WHERE stock_id = :id", id = session["user_id"])
        symbols = symbols.fetchall()

        return render_template("sell.html", stock = symbols)

@app.route("/check", methods=["GET"])
def check():
    """Возвращает Истина, если такое имя доступно, иначе возвращает Ложь"""
    username=request.args.get("q")
    rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)
    rows = rows.fetchall()
    if len(rows) >=1 or len(username) < 1:
        return jsonify(False)
    else:
        return jsonify(True)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
