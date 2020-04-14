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
            user_id BIGSERIAL PRIMARY KEY,
            username VARCHAR NOT NULL,
            password VARCHAR NOT NULL)""",
        """CREATE TABLE books (
            book_id BIGSERIAL PRIMARY KEY,
            isbn VARCHAR(13) NOT NULL,
            author VARCHAR NOT NULL,title VARCHAR NOT NULL,
            publication_year INTEGER NOT NULL,
            review_count INTEGER NOT NULL)""",
        """CREATE TABLE reviews (
            review_id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            FOREIGN KEY ("user_id") REFERENCES "users" ("user_id") ON DELETE RESTRICT ON UPDATE CASCADE,
            book_id BIGINT NOT NULL,
            FOREIGN KEY ("book_id") REFERENCES "books" ("book_id") ON DELETE RESTRICT ON UPDATE CASCADE,
            review_rating INT NOT NULL,
            review_text VARCHAR(10000),
            time_created TIMESTAMP NOT NULL,
            CHECK (review_rating > 0),
            CHECK (review_rating <= 5))""",
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
