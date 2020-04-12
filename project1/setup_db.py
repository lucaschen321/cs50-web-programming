import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


def main():

    print("Setting up database")

    # Set up database
    engine = create_engine(os.getenv("DATABASE_URL"))
    db = scoped_session(sessionmaker(bind=engine))

    commands = [
        # Install extensions
        """CREATE EXTENSION IF NOT EXISTS PG_TRGM;""",
        # Set up tables
        """CREATE TABLE users (
            userid BIGSERIAL PRIMARY KEY,
            username VARCHAR NOT NULL,
            password VARCHAR NOT NULL)""",
        """CREATE TABLE books (
            bookid BIGSERIAL PRIMARY KEY,
            isbn VARCHAR(13) NOT NULL,
            author VARCHAR NOT NULL,title VARCHAR NOT NULL,
            publication_year INTEGER NOT NULL,
            review_count INTEGER NOT NULL)""",
        """CREATE TABLE reviews (
            reviewid BIGSERIAL PRIMARY KEY,
            userid BIGINT NOT NULL,
            FOREIGN KEY ("userid") REFERENCES "users" ("userid") ON DELETE RESTRICT ON UPDATE CASCADE,
            bookid BIGINT NOT NULL,
            FOREIGN KEY ("bookid") REFERENCES "books" ("bookid") ON DELETE RESTRICT ON UPDATE CASCADE,
            rating_num INT NOT NULL,
            rating_text VARCHAR(10000),
            time_created TIMESTAMP NOT NULL,
            CHECK (rating_num > 0),
            CHECK (rating_num <= 5))""",
    ]

    # Execute Commands
    try:
        for command in commands:
            db.execute(command)

        db.commit()
    except Exception as e:
        print(str(e))

    print("Done")


if __name__ == "__main__":
    main()
