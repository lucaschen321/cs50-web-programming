import os

from flask import (
    Flask,
    flash,
    Markup,
    render_template,
    redirect,
    request,
    session,
    url_for,
)
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=["GET", "POST"])
def index():
    # Handle logouts
    if request.method == "POST":
        # TODO: Handle searches
        try:
            if request.form.get("action") == "logout":
                session["user_id"] = request.form.get("username")
            else:
                raise Exception
        except:
            return render_template("error.html")

    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register for an account"""
    error = None
    username = request.form.get("username")
    password = request.form.get("password")
    password_confirmation = request.form.get("password_confirmation")

    # Validate username and passwords and create account
    if request.method == "POST":
        if not username or not password or not password_confirmation:
            flash("Please enter username and password", "error")
        elif password != password_confirmation:
            flash("Passwords do not match!", "error")
        elif (
            db.execute(
                "SELECT * FROM users WHERE username = :username", {"username": username}
            ).rowcount
            > 0
        ):
            flash(
                Markup(
                    'User already exists. Please <a href="/login" class="alert-link">sign in</a>!'
                ),
                "error",
            )
        else:
            db.execute(
                "INSERT INTO users (username, password) VALUES (:username, :password)",
                {"username": username, "password": password},
            )
            db.commit()
            session["user_id"] = request.form.get("username")
            flash("Account created!", "message")
            return redirect(url_for("index"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login to account"""
    error = None
    username = request.form.get("username")
    password = request.form.get("password")

    # Validate username and passwords and login to account
    if request.method == "POST":
        if not username or not password:
            flash("Please enter username and password", "error")
        elif (
            db.execute(
                "SELECT * FROM users WHERE username = :username AND password = :password",
                {"username": username, "password": password},
            ).rowcount
            == 0
        ):
            flash("Invalid credentials!", "error")
        else:
            session["user_id"] = request.form.get("username")
            flash("Logged In!", "message")
            return redirect(url_for("index"))

    return render_template("login.html")
