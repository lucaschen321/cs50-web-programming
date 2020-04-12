#!/usr/bin/env python3

import argparse
import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from tqdm import tqdm


def main():

    # Optionally specify target import file using command-line arguments
    parser = argparse.ArgumentParser(
        description="Write books from target file into PostgreSQL database at $DATABASE_URL."
    )
    parser.add_argument(
        "--target-file", "-t", help="increase output verbosity", default="books.csv"
    )
    args = parser.parse_args()

    FILE = args.target_file

    try:
        with open(FILE, newline="") as books_file:
            num_lines = sum(1 for line in open("books.csv")) - 1
            booksreader = csv.DictReader(books_file)

            print("Importing into database")

            # Set up database
            engine = create_engine(os.getenv("DATABASE_URL"))
            db = scoped_session(sessionmaker(bind=engine))

            # Read in each line from file into database
            for row in tqdm(booksreader, total=num_lines):
                isbn, title, author, publication_year = row.values()
                command = f"INSERT INTO books (isbn, title, author, publication_year, review_count) VALUES (:isbn, :title, :author, :publication_year, :review_count)"
                db.execute(
                    command,
                    # Sanitize inputs (e.g. cases with quotes in title)
                    {
                        "isbn": isbn,
                        "title": title,
                        "author": author,
                        "publication_year": publication_year,
                        "review_count": 0,
                    },
                )

            db.commit()
            print("Done")
    except Exception as e:
        print(str(e))


if __name__ == "__main__":
    main()
