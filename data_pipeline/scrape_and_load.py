import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
from pathlib import Path


# ============================================================
# PROJECT SETTINGS
# ============================================================

# Website to scrape
BASE_URL = "https://books.toscrape.com/"

# Get the folder where this Python file is located
BASE_DIR = Path(__file__).resolve().parent

# Database will be created inside data_pipeline
DATABASE_PATH = BASE_DIR / "books.db"

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

    # First 5 pages = approximately 100 books
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

            print(
                f"Error while scraping page {page}: {error}"
            )

            continue

        # Use response.content for better encoding handling
        soup = BeautifulSoup(
            response.content,
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

            star_rating = ""

            if rating_tag:

                rating_classes = rating_tag.get(
                    "class",
                    []
                )

                for rating_word in RATING_MAP:

                    if rating_word in rating_classes:

                        star_rating = rating_word
                        break


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

                    # Use response.content for better encoding handling
                    book_soup = BeautifulSoup(
                        book_response.content,
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

                except requests.RequestException as error:

                    # If category request fails,
                    # keep Unknown instead of crashing
                    print(
                        f"Could not retrieve category "
                        f"for '{title}': {error}"
                    )

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

    # Check whether any data was scraped
    if df.empty:

        raise ValueError(
            "No books were scraped. "
            "Please check the website connection."
        )


    # --------------------------------------------------------
    # CLEAN PRICE
    # --------------------------------------------------------

    # Remove currency symbols and convert to numeric
    df["price_gbp"] = (
        df["price"]
        .astype(str)
        .str.replace("£", "", regex=False)
        .str.replace("Â", "", regex=False)
        .str.strip()
    )

    # Convert invalid values into NaN
    df["price_gbp"] = pd.to_numeric(
        df["price_gbp"],
        errors="coerce"
    )


    # --------------------------------------------------------
    # CLEAN RATING
    # --------------------------------------------------------

    # Convert One/Two/Three/Four/Five into numbers
    df["rating"] = df["star_rating"].map(
        RATING_MAP
    )

    # Convert invalid values into NaN
    df["rating"] = pd.to_numeric(
        df["rating"],
        errors="coerce"
    )


    # --------------------------------------------------------
    # CLEAN AVAILABILITY
    # --------------------------------------------------------

    # True if availability contains "In stock"
    # False otherwise
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
    # HANDLE INVALID PRICE VALUES
    # --------------------------------------------------------

    if df["price_gbp"].isna().any():

        median_price = df["price_gbp"].median()

        print(
            "Invalid price values found. "
            f"Using median price: {median_price}"
        )

        df["price_gbp"] = df["price_gbp"].fillna(
            median_price
        )


    # --------------------------------------------------------
    # HANDLE INVALID RATING VALUES
    # --------------------------------------------------------

    if df["rating"].isna().any():

        median_rating = df["rating"].median()

        print(
            "Invalid rating values found. "
            f"Using median rating: {median_rating}"
        )

        df["rating"] = df["rating"].fillna(
            median_rating
        )


    # Rating must be an integer from 1 to 5
    df["rating"] = (
        df["rating"]
        .round()
        .clip(1, 5)
        .astype(int)
    )


    # --------------------------------------------------------
    # GBP TO INR CONVERSION
    # --------------------------------------------------------

    # Fixed project requirement:
    # 1 GBP = 105.50 INR
    df["price_inr"] = (
        df["price_gbp"] * GBP_TO_INR
    )


    # --------------------------------------------------------
    # VALIDATE REQUIRED DATA
    # --------------------------------------------------------

    # Remove rows without a title
    df = df[
        df["title"]
        .astype(str)
        .str.strip()
        != ""
    ].copy()


    # --------------------------------------------------------
    # KEEP REQUIRED COLUMNS
    # --------------------------------------------------------

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

    # This makes the pipeline reproducible.
    # Running the script again will not duplicate books.

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
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .replace("", "Unknown")
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
                int(bool(row["in_stock"])),
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


    cursor.execute(
        "SELECT COUNT(DISTINCT category_id) FROM books"
    )

    book_category_count = cursor.fetchone()[0]


    print(
        f"Books stored in database: {book_count}"
    )

    print(
        f"Categories stored in database: {category_count}"
    )

    print(
        f"Categories used by books: {book_category_count}"
    )


    # --------------------------------------------------------
    # VALIDATE MINIMUM REQUIREMENTS
    # --------------------------------------------------------

    if book_count < 60:

        print(
            "WARNING: Fewer than 60 books were stored."
        )

    else:

        print(
            "✓ Book count requirement satisfied."
        )


    if book_category_count >= 3:

        print(
            "✓ At least 3 categories requirement satisfied."
        )

    else:

        print(
            "WARNING: Fewer than 3 categories were found."
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
    # CHECK SCRAPED BOOK COUNT
    # --------------------------------------------------------

    if len(books) < 60:

        raise ValueError(
            "The pipeline scraped fewer than 60 books."
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
    # VALIDATE DATA VALUES
    # --------------------------------------------------------

    print("\nData validation:")

    print(
        "Minimum price GBP:",
        df["price_gbp"].min()
    )

    print(
        "Maximum price GBP:",
        df["price_gbp"].max()
    )

    print(
        "Minimum rating:",
        df["rating"].min()
    )

    print(
        "Maximum rating:",
        df["rating"].max()
    )

    print(
        "In-stock values:",
        df["in_stock"].unique()
    )

    print(
        "Missing price values:",
        df["price_gbp"].isna().sum()
    )

    print(
        "Missing rating values:",
        df["rating"].isna().sum()
    )

    print(
        "Missing price INR values:",
        df["price_inr"].isna().sum()
    )


    # --------------------------------------------------------
    # VALIDATE PRICE CONVERSION
    # --------------------------------------------------------

    conversion_check = (
        df["price_inr"]
        .round(2)
        ==
        (df["price_gbp"] * GBP_TO_INR).round(2)
    ).all()

    print(
        "GBP to INR conversion correct:",
        conversion_check
    )


    # --------------------------------------------------------
    # CREATE DATABASE
    # --------------------------------------------------------

    create_database(df)


    # --------------------------------------------------------
    # FINAL MESSAGE
    # --------------------------------------------------------

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