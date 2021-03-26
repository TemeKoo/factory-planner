from flask import Flask
from flask import request, render_template
from flask_sqlalchemy import SQLAlchemy
from os import getenv

app = Flask(__name__)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
db = SQLAlchemy(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/items")
def items():
    sql = "SELECT display_name FROM items ORDER BY display_name"
    items_list = db.session.execute(sql).fetchall()
    return render_template("items.html", items_list=items_list)


@app.route("/calculator")
def calculator_start():
    sql = """SELECT id, display_name
             FROM items
             WHERE id IN (SELECT DISTINCT item_id 
                          FROM item_or_machine 
                          WHERE item_id IS NOT NULL)
             AND stack_size > 0
             ORDER BY display_name"""
    items_list = db.session.execute(sql).fetchall()
    return render_template("calculator.html", items_list=items_list)


@app.route("/calculator/result", methods=["GET"])
def calculator_result():
    item_id = request.args["item"]
    amount = request.args["amount"]
    item_name = db.session.execute("SELECT display_name FROM items WHERE id = :item_id", {"item_id": item_id}).fetchone()[0]
    return render_template("calculator_result.html", item_name=item_name, amount=amount)


@app.route("/production_lines")
def production_lines():
    return render_template("production_lines.html")

@app.route("/factory")
def factory():
    return render_template("factory.html")