import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3


# ============================================================
# PROJECT SETTINGS
# ============================================================

BASE_URL = "https://books.toscrape.com/"
DATABASE_PATH = "data_pipeline/books.db"

# Required fixed conversion rate for this project
GBP_TO_INR = 105.50

# Convert text ratings into numbers
RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5
}


# ============================================================
# STEP 1: SCRAPE BOOK DATA
# ============================================================

def scrape_books():

    books = []

    # First 5 pages = 100 books
    for page in range(1, 6):

        url = f"{BASE_URL}catalogue/page-{page}.html"

        print(f"Scraping page {page}...")

        try:
            response = requests.get(
                url,
                timeout=10
            )

            # Stop if HTTP request failed
            response.raise_for_status()

        except requests.RequestException as error:

            print(f"Error while scraping page {page}: {error}")
            continue

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # Find all book cards
        book_items = soup.select(
            "article.product_pod"
        )

        print(
            f"Books found on page {page}: "
            f"{len(book_items)}"
        )

        for book in book_items:

            # ------------------------------------------------
            # TITLE
            # ------------------------------------------------

            title_tag = book.select_one(
                "h3 a"
            )

            if title_tag:
                title = title_tag.get(
                    "title",
                    ""
                ).strip()
            else:
                title = ""


            # ------------------------------------------------
            # PRICE
            # ------------------------------------------------

            price_tag = book.select_one(
                ".price_color"
            )

            if price_tag:
                price = price_tag.get_text(
                    strip=True
                )
            else:
                price = ""


            # ------------------------------------------------
            # STAR RATING
            # ------------------------------------------------

            rating_tag = book.select_one(
                "p.star-rating"
            )

            if rating_tag:

                rating_classes = rating_tag.get(
                    "class",
                    []
                )

                star_rating = ""

                for rating_word in RATING_MAP:

                    if rating_word in rating_classes:

                        star_rating = rating_word
                        break

            else:
                star_rating = ""


            # ------------------------------------------------
            # AVAILABILITY
            # ------------------------------------------------

            availability_tag = book.select_one(
                ".availability"
            )

            if availability_tag:

                availability = availability_tag.get_text(
                    " ",
                    strip=True
                )

            else:
                availability = ""


            # ------------------------------------------------
            # CATEGORY
            # ------------------------------------------------

            category = "Unknown"

            if title_tag:

                book_link = title_tag.get(
                    "href",
                    ""
                )

                # Convert relative link into full URL
                book_url = (
                    BASE_URL
                    + "catalogue/"
                    + book_link.replace("../", "")
                )

                try:

                    book_response = requests.get(
                        book_url,
                        timeout=10
                    )

                    book_response.raise_for_status()

                    book_soup = BeautifulSoup(
                        book_response.text,
                        "html.parser"
                    )

                    # Category is available in breadcrumb
                    breadcrumb = book_soup.select(
                        "ul.breadcrumb li a"
                    )

                    if len(breadcrumb) >= 3:

                        category = breadcrumb[-1].get_text(
                            strip=True
                        )

                except requests.RequestException:

                    # If category request fails,
                    # keep Unknown instead of crashing
                    category = "Unknown"


            # ------------------------------------------------
            # SAVE RAW BOOK DATA
            # ------------------------------------------------

            books.append(
                {
                    "title": title,
                    "price": price,
                    "star_rating": star_rating,
                    "availability": availability,
                    "category": category
                }
            )

    return books


# ============================================================
# STEP 2: CLEAN AND TRANSFORM DATA
# ============================================================

def clean_data(books):

    print("\nCleaning data...")

    # Convert list of dictionaries into DataFrame
    df = pd.DataFrame(books)

    # --------------------------------------------------------
    # CLEAN PRICE
    # --------------------------------------------------------

    # Remove currency symbols and keep numeric characters
    df["price_gbp"] = (
        df["price"]
        .astype(str)
        .str.replace("£", "", regex=False)
        .str.replace("Â", "", regex=False)
        .str.strip()
    )

    # Convert to numeric
    # Invalid values become NaN
    df["price_gbp"] = pd.to_numeric(
        df["price_gbp"],
        errors="coerce"
    )


    # --------------------------------------------------------
    # CLEAN RATING
    # --------------------------------------------------------

    df["rating"] = df["star_rating"].map(
        RATING_MAP
    )

    # Convert to numeric
    df["rating"] = pd.to_numeric(
        df["rating"],
        errors="coerce"
    )


    # --------------------------------------------------------
    # CLEAN AVAILABILITY
    # --------------------------------------------------------

    df["in_stock"] = (
        df["availability"]
        .astype(str)
        .str.contains(
            "In stock",
            case=False,
            na=False
        )
    )


    # --------------------------------------------------------
    # HANDLE INVALID NUMERIC VALUES
    # --------------------------------------------------------

    # Price:
    # Replace missing/invalid prices with median price
    if df["price_gbp"].isna().any():

        median_price = df["price_gbp"].median()

        df["price_gbp"] = df["price_gbp"].fillna(
            median_price
        )


    # Rating:
    # Replace missing/invalid ratings with median rating
    if df["rating"].isna().any():

        median_rating = df["rating"].median()

        df["rating"] = df["rating"].fillna(
            median_rating
        )


    # Rating must be an integer
    df["rating"] = df["rating"].round().astype(int)


    # --------------------------------------------------------
    # GBP TO INR CONVERSION
    # --------------------------------------------------------

    df["price_inr"] = (
        df["price_gbp"] * GBP_TO_INR
    )


    # --------------------------------------------------------
    # REMOVE UNNECESSARY RAW COLUMNS
    # --------------------------------------------------------

    # Keep both raw and cleaned columns because
    # the assignment asks us to capture the original fields.
    df = df[
        [
            "title",
            "price",
            "star_rating",
            "availability",
            "category",
            "price_gbp",
            "rating",
            "in_stock",
            "price_inr"
        ]
    ]


    return df


# ============================================================
# STEP 3: CREATE SQLITE DATABASE
# ============================================================

def create_database(df):

    print("\nCreating SQLite database...")

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()


    # --------------------------------------------------------
    # ENABLE FOREIGN KEYS
    # --------------------------------------------------------

    cursor.execute(
        "PRAGMA foreign_keys = ON"
    )


    # --------------------------------------------------------
    # CREATE CATEGORIES TABLE
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE NOT NULL
        )
        """
    )


    # --------------------------------------------------------
    # CREATE BOOKS TABLE
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            book_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price_gbp REAL,
            price_inr REAL,
            rating INTEGER,
            in_stock INTEGER,
            category_id INTEGER,

            FOREIGN KEY (category_id)
                REFERENCES categories(category_id)
        )
        """
    )


    # --------------------------------------------------------
    # CLEAR OLD DATA
    # --------------------------------------------------------

    # This makes the script reproducible.
    # Running it again will not duplicate books.

    cursor.execute(
        "DELETE FROM books"
    )

    cursor.execute(
        "DELETE FROM categories"
    )


    # --------------------------------------------------------
    # INSERT CATEGORIES
    # --------------------------------------------------------

    unique_categories = (
        df["category"]
        .dropna()
        .unique()
    )

    for category in unique_categories:

        cursor.execute(
            """
            INSERT OR IGNORE INTO categories
            (category_name)
            VALUES (?)
            """,
            (category,)
        )


    # --------------------------------------------------------
    # INSERT BOOKS
    # --------------------------------------------------------

    for _, row in df.iterrows():

        # Find category ID
        cursor.execute(
            """
            SELECT category_id
            FROM categories
            WHERE category_name = ?
            """,
            (row["category"],)
        )

        category_result = cursor.fetchone()

        if category_result is None:
            continue

        category_id = category_result[0]


        # Insert book
        cursor.execute(
            """
            INSERT INTO books
            (
                title,
                price_gbp,
                price_inr,
                rating,
                in_stock,
                category_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                row["title"],
                float(row["price_gbp"]),
                float(row["price_inr"]),
                int(row["rating"]),
                int(row["in_stock"]),
                category_id
            )
        )


    # --------------------------------------------------------
    # SAVE CHANGES
    # --------------------------------------------------------

    connection.commit()


    # --------------------------------------------------------
    # VALIDATE DATABASE
    # --------------------------------------------------------

    cursor.execute(
        "SELECT COUNT(*) FROM books"
    )

    book_count = cursor.fetchone()[0]


    cursor.execute(
        "SELECT COUNT(*) FROM categories"
    )

    category_count = cursor.fetchone()[0]


    print(
        f"Books stored in database: {book_count}"
    )

    print(
        f"Categories stored in database: {category_count}"
    )


    connection.close()


# ============================================================
# STEP 4: MAIN PROGRAM
# ============================================================

def main():

    print("=" * 60)
    print("ZEPTO DATA PIPELINE")
    print("=" * 60)


    # --------------------------------------------------------
    # SCRAPE
    # --------------------------------------------------------

    books = scrape_books()

    print(
        f"\nTotal books scraped: {len(books)}"
    )


    # --------------------------------------------------------
    # CLEAN
    # --------------------------------------------------------

    df = clean_data(books)


    # --------------------------------------------------------
    # DISPLAY DATA
    # --------------------------------------------------------

    print("\nFirst 5 cleaned records:")
    print(
        df.head().to_string(index=False)
    )


    # --------------------------------------------------------
    # DISPLAY DATA TYPES
    # --------------------------------------------------------

    print("\nData types:")
    print(df.dtypes)


    # --------------------------------------------------------
    # CHECK CATEGORIES
    # --------------------------------------------------------

    print("\nCategories found:")

    print(
        df["category"]
        .value_counts()
        .head(10)
    )


    print(
        f"\nNumber of unique categories: "
        f"{df['category'].nunique()}"
    )


    # --------------------------------------------------------
    # CHECK REQUIRED COLUMNS
    # --------------------------------------------------------

    required_columns = [
        "title",
        "price_gbp",
        "rating",
        "in_stock",
        "price_inr",
        "category"
    ]

    print("\nRequired columns check:")

    for column in required_columns:

        if column in df.columns:
            print(f"✓ {column}")
        else:
            print(f"✗ {column}")


    # --------------------------------------------------------
    # CREATE DATABASE
    # --------------------------------------------------------

    create_database(df)


    print("\n" + "=" * 60)
    print("DATA PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 60)


    print(
        f"\nFixed conversion rate used: "
        f"1 GBP = {GBP_TO_INR} INR"
    )

    print(
        f"Database location: {DATABASE_PATH}"
    )


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()