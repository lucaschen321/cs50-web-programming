import bcrypt
import datetime
import os
import requests

from flask import (
    Flask,
    flash,
    Markup,
    render_template,
    redirect,
    request,
    session,
    url_for,
    jsonify,
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

# Get Goodreads API key
with open("GOODREADS_API_KEY", "r") as f:
    API_KEY = f.read()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            # Handle logouts
            if "logout" in request.form:
                session["user_id"] = None
            else:
                raise Exception
        except:
            return render_template("error.html")

    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    search_text = request.form.get("search_text")
    search_results = []

    if request.method == "POST":
        try:
            if "search" in request.form:
                if request.form.get("search_type") == "title":
                    search_results = db.execute(
                        "SELECT *, similarity(books.title, :search_text) AS similarity FROM books WHERE books.title % :search_text ORDER BY similarity DESC",
                        {"search_text": search_text},
                    ).fetchall()
                elif request.form.get("search_type") == "author":
                    search_results = db.execute(
                        "SELECT *, similarity(books.author, :search_text) AS similarity FROM books WHERE books.author % :search_text ORDER BY similarity DESC",
                        {"search_text": search_text},
                    ).fetchall()
                elif request.form.get("search_type") == "isbn":
                    search_results = db.execute(
                        "SELECT *, similarity(books.isbn, :search_text) AS similarity FROM books WHERE books.isbn % :search_text ORDER BY similarity DESC",
                        {"search_text": search_text},
                    ).fetchall()
                else:
                    raise Exception
        except:
            return render_template("error.html")

    return render_template(
        "search.html", search_text=search_text, search_results=search_results
    )


@app.route("/book/<int:book_id>-<string:title>", methods=["GET", "POST"])
def book(book_id, title):
    """List details about a single book and accept review submissions."""

    # Make sure book exists.
    book = db.execute(
        "SELECT * from books WHERE book_id = :book_id", {"book_id": book_id}
    ).fetchone()
    if book is None:
        return render_template("error.html")

    # Submit review if posted
    if request.method == "POST":
        review_text = request.form.get("review_text")
        review_rating = request.form.get("review_rating")

        if not "review_text" in request.form:
            flash("Please submit a review", "error")
        elif not session["user_id"]:
            flash(
                Markup(
                    'Please <a href="/login" class="alert-link">sign in</a> to submit a review'
                ),
                "error",
            )
        else:
            user_id = (
                db.execute(
                    "SELECT * FROM users WHERE username = :username",
                    {"username": session["user_id"]},
                )
                .fetchone()
                .user_id
            )

            if (
                db.execute(
                    "SELECT * FROM reviews WHERE user_id = :user_id AND book_id = :book_id",
                    {"user_id": user_id, "book_id": book_id},
                ).rowcount
                > 0
            ):
                # User already submitted a review
                flash("Already submitted a review", "error")
            else:
                db.execute(
                    "INSERT INTO reviews (user_id, book_id, review_rating, review_text, time_created) VALUES (:user_id, :book_id, :review_rating, :review_text, :time_created)",
                    {
                        "user_id": user_id,
                        "book_id": book.book_id,
                        "review_rating": review_rating,
                        "review_text": review_text,
                        "time_created": datetime.datetime.now().strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                    },
                )
                db.commit()

    # Get all reviews.
    reviews = db.execute(
        "SELECT * FROM reviews WHERE book_id = :book_id", {"book_id": book_id}
    ).fetchall()

    # Get Goodreads review data
    request_json, goodreads_data = {}, {}
    try:
        request_json = requests.get(
            "https://www.goodreads.com/book/review_counts.json",
            params={"key": API_KEY, "isbns": book.isbn},
        ).json()
    except:
        # Handle case with invalid API key
        request_json["books"] = None

    # Handle cases with no matches or wrong matches
    if request_json["books"] and request_json["books"][0]:
        if (
            request_json["books"][0]["isbn"] == book.isbn
            or request_json["books"][0]["isbn13"] == book.isbn
        ):
            goodreads_data = request_json["books"][0]

    return render_template(
        "book.html", book=book, reviews=reviews, goodreads_data=goodreads_data
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register for an account"""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        password_confirmation = request.form.get("password_confirmation")

        if (
            not username or not password or not password_confirmation
        ):  # Incomplete field(s)
            flash("Please enter username and password", "error")
        elif password != password_confirmation:  # Password mismatch
            flash("Passwords do not match!", "error")
        elif (
            db.execute(
                "SELECT * FROM users WHERE username = :username", {"username": username}
            ).rowcount
            > 0
        ):  # User already exists
            flash(
                Markup(
                    'User already exists. Please <a href="/login" class="alert-link">sign in</a>!'
                ),
                "error",
            )
        else:  # Register user
            password = bytes(password, "utf-8")
            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
            hashed_password = hashed_password.decode("utf-8")
            db.execute(
                "INSERT INTO users (username, password) VALUES (:username, :password)",
                {"username": username, "password": hashed_password},
            )
            db.commit()

            session["user_id"] = request.form.get("username")
            flash("Account created!", "message")

            return redirect(url_for("index"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login to account"""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:  # Incomplete field(s)
            flash("Please enter username and password", "error")
        else:
            password = bytes(password, "utf-8")
            user = db.execute(
                "SELECT * FROM users WHERE username = :username",
                {"username": username},
            ).fetchone()

            if not user:  # User doesn't exist
                flash(
                    Markup(
                        'User does not exist. Please <a href="/register" class="alert-link">register</a> or <a href="/login" class="alert-link">sign in</a> under a different username!'
                    ),
                    "error",
                )
            elif not bcrypt.checkpw(
                password, user.password.encode("utf-8")
            ):  # Invalid credentials
                flash("Invalid credentials!", "error")
            else:  # 'Log in' user
                session["user_id"] = request.form.get("username")
                flash("Logged In!", "message")
                return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/api/<string:isbn>", methods=["GET"])
def api(isbn):
    """Handle API requests"""

    book = db.execute(
        "SELECT title, author, isbn, publication_year, COUNT(*), AVG(reviews.review_rating) from books LEFT JOIN reviews ON books.book_id = reviews.book_id WHERE isbn = :isbn GROUP BY books.book_id;",
        {"isbn": isbn},
    ).fetchone()

    # Make sure book with ISBN exists in database
    if not book:
        return jsonify({"error": "Requested ISBN not in database"}), 404

    return jsonify(
        {
            "title": book.title,
            "author": book.author,
            "year": book.publication_year,
            "isbn": book.isbn,
            "review_count": 0 if not book.avg else book.count,
            "average_score": book.avg,
        }
    )
