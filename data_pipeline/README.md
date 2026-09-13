# Data Pipeline

This module implements an end-to-end data pipeline for collecting book data from the public website `books.toscrape.com`, cleaning and transforming the data, converting prices from GBP to INR, storing the data in a normalized SQLite database, and performing SQL and pandas analysis.

## Objective

The data pipeline performs the following tasks:

1. Scrapes book data from `books.toscrape.com`
2. Collects books from the first 5 paginated listing pages
3. Extracts title, price, star rating, availability, and category
4. Cleans and validates the scraped data
5. Converts GBP prices to INR using a fixed conversion rate
6. Stores the cleaned data in a normalized SQLite database
7. Runs SQL queries for analysis
8. Reads SQL results into pandas using `pd.read_sql()`
9. Reproduces the SQL JOIN using `pd.merge()`
10. Verifies that the SQL JOIN and pandas merge produce equivalent results

## Data Source

Source website:

`https://books.toscrape.com/`

The pipeline uses the first 5 listing pages.

Each listing page contains approximately 20 books, resulting in:

* Books scraped: 100
* Unique categories found: 29

No login, API key, paid service, or external currency API is required.

## Data Fields

The scraper collects the following raw fields:

* `title` - Book title
* `price` - Original price text in GBP
* `star_rating` - Rating text such as One, Two, Three, Four, or Five
* `availability` - Availability text
* `category` - Book category

The cleaned dataset contains:

* `title`
* `price_gbp`
* `rating`
* `in_stock`
* `price_inr`
* `category`

## Data Cleaning and Transformation

### Price

The original price contains the GBP currency symbol.

The pipeline:

1. Removes the `£` currency symbol.
2. Removes the possible `Â` encoding character.
3. Converts the value to a numeric `float`.
4. Uses median imputation if a price cannot be parsed.

Example:

`£51.77` → `51.77`

### Rating

The website provides ratings as words.

The pipeline converts them using:

* One → 1
* Two → 2
* Three → 3
* Four → 4
* Five → 5

Invalid rating values are converted to missing values and median-imputed.

The final rating is rounded and restricted to the range 1–5.

### Availability

The availability text is converted to a Boolean value.

If the text contains `In stock`:

`True`

Otherwise:

`False`

### Missing Titles

Rows without a valid book title are removed because the title is required to identify a book.

### GBP to INR Conversion

The project requires the following fixed conversion rate:

`1 GBP = 105.50 INR`

The conversion is calculated as:

`price_inr = price_gbp * 105.50`

No external currency API is used.

## SQLite Database

The pipeline creates the following SQLite database:

`data_pipeline/books.db`

The database is normalized into two related tables.

### categories

| Column          | Type    | Description          |
| --------------- | ------- | -------------------- |
| `category_id`   | INTEGER | Primary key          |
| `category_name` | TEXT    | Unique category name |

### books

| Column        | Type    | Description                            |
| ------------- | ------- | -------------------------------------- |
| `book_id`     | INTEGER | Primary key                            |
| `title`       | TEXT    | Book title                             |
| `price_gbp`   | REAL    | Cleaned GBP price                      |
| `price_inr`   | REAL    | Converted INR price                    |
| `rating`      | INTEGER | Rating from 1 to 5                     |
| `in_stock`    | INTEGER | Boolean value stored as SQLite integer |
| `category_id` | INTEGER | Foreign key referencing `categories`   |

The relationship is:

`categories.category_id` → `books.category_id`

Foreign key enforcement is enabled using SQLite:

`PRAGMA foreign_keys = ON`

## SQL Analysis

The file `queries.py` performs six SQL queries.

### Query 1 — SELECT + WHERE

Finds books with a rating greater than or equal to 4.

### Query 2 — ORDER BY + LIMIT

Finds the 10 most expensive books.

### Query 3 — DISTINCT

Lists distinct book categories.

### Query 4 — BETWEEN

Finds books with prices between £20 and £40.

### Query 5 — IN

Finds books with ratings of 4 or 5.

### Query 6 — JOIN

Joins the `books` and `categories` tables using the foreign key relationship.

The SQL query output is saved in:

`data_pipeline/query_outputs.txt`

## Pandas Integration

The project uses `pd.read_sql()` to load SQL query results into pandas DataFrames.

The database tables are also loaded into pandas:

* `books`
* `categories`

The SQL JOIN is then reproduced without SQL using:

`pd.merge()`

The SQL JOIN result and pandas merge result are compared using pandas equality checking.

The final result was:

`SQL JOIN and pd.merge() results match: True`

## Validation Results

The pipeline was executed successfully.

Validation results:

* Total books scraped: 100
* Books stored in database: 100
* Categories stored in database: 29
* Categories used by books: 29
* Minimum rating: 1
* Maximum rating: 5
* Missing price values: 0
* Missing rating values: 0
* Missing INR values: 0
* GBP to INR conversion correct: True
* SQL JOIN and `pd.merge()` results match: True

The pipeline also verifies that at least 60 books and at least 3 categories are available.

## Files

### `scrape_and_load.py`

Scrapes, cleans, transforms, validates, and stores the book data.

### `queries.py`

Runs the required SQL queries and reproduces the SQL JOIN using pandas.

### `requirements.txt`

Contains the required external Python packages:

* requests
* beautifulsoup4
* pandas

SQLite is included with Python and does not need to be installed separately.

### `books.db`

SQLite database generated by the data pipeline.

### `query_outputs.txt`

Contains the SQL query strings, query results, pandas JOIN result, and JOIN comparison result.

## Installation

Make sure Python 3 is installed.

From the project root, run:

```bash
pip install -r data_pipeline/requirements.txt
```

## Running the Data Pipeline

From the project root:

```bash
py data_pipeline\scrape_and_load.py
```

This will:

1. Scrape 5 pages.
2. Collect approximately 100 books.
3. Clean and transform the data.
4. Validate the data.
5. Create/update `data_pipeline/books.db`.

## Running SQL Analysis

After running the data pipeline:

```bash
py data_pipeline\queries.py
```

This will:

1. Execute the required SQL queries.
2. Display query results.
3. Load data using `pd.read_sql()`.
4. Reproduce the JOIN using `pd.merge()`.
5. Compare both results.
6. Save the results to `data_pipeline/query_outputs.txt`.

## Reproducibility

The complete pipeline can be regenerated by running:

```bash
py data_pipeline\scrape_and_load.py
```

The SQLite database is recreated from the scraped data, so the process does not require manual copy-paste of data.

The fixed currency conversion rate is always:

`1 GBP = 105.50 INR`

## Module 1 Completion

The Data Pipeline module satisfies the required scraping, cleaning, transformation, database, SQL, and pandas integration requirements.

The implementation is fully reproducible from the provided Python scripts.
