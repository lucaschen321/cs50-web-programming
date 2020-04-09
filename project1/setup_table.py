import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


def main():
    print("Setting up database")

    # Set up database
    engine = create_engine(os.getenv("DATABASE_URL"))
    db = scoped_session(sessionmaker(bind=engine))

    commands = [
        "CREATE TABLE users (userid SERIAL PRIMARY KEY, username VARCHAR NOT NULL, password VARCHAR NOT NULL)",
        "CREATE TABLE books (bookid SERIAL PRIMARY KEY,isbn INTEGER NOT NULL,author VARCHAR NOT NULL,title VARCHAR NOT NULL,publication_year INTEGER NOT NULL,review_count INTEGER NOT NULL)",
        "CREATE TABLE reviews (reviewid SERIAL PRIMARY KEY, userid INT REFERENCES users NOT NULL, bookid INT REFERENCES books NOT NULL, rating_num INT NOT NULL, rating_text VARCHAR(10000), time_created TIMESTAMP NOT NULL, CHECK (rating_num > 0), CHECK (rating_num <= 5))",
    ]

    for command in commands:
        db.execute(command)

    db.commit()

    print("Done")


if __name__ == "__main__":
    main()
