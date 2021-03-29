from flask import Flask
from flask import request, render_template
from flask_sqlalchemy import SQLAlchemy
from os import getenv
from calculator import calculator

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


@app.route("/calculator", methods=["GET"])
def calculator_page():
    return calculator(db, render_template, **request.args)


@app.route("/production_lines")
def production_lines():
    return render_template("production_lines.html")

@app.route("/factory")
def factory():
    return render_template("factory.html")