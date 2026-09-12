import sqlite3
import pandas as pd


DATABASE_PATH = "data_pipeline/books.db"
OUTPUT_FILE = "data_pipeline/query_outputs.txt"


def run_queries():
    conn = sqlite3.connect(DATABASE_PATH)

    print("=" * 60)
    print("ZEPTO DATA PIPELINE - SQL QUERIES")
    print("=" * 60)

    # ---------------------------------------------------------
    # QUERY 1: SELECT + WHERE
    # ---------------------------------------------------------
    query1 = """
    SELECT title, price_gbp, rating, in_stock
    FROM books
    WHERE rating >= 4
    """

    result1 = pd.read_sql(query1, conn)

    print("\nQUERY 1 - Books with rating >= 4")
    print(result1.head(10).to_string(index=False))

    # ---------------------------------------------------------
    # QUERY 2: ORDER BY + LIMIT
    # ---------------------------------------------------------
    query2 = """
    SELECT title, price_gbp, rating
    FROM books
    ORDER BY price_gbp DESC
    LIMIT 10
    """

    result2 = pd.read_sql(query2, conn)

    print("\nQUERY 2 - 10 Most Expensive Books")
    print(result2.to_string(index=False))

    # ---------------------------------------------------------
    # QUERY 3: DISTINCT
    # ---------------------------------------------------------
    query3 = """
    SELECT DISTINCT category_name
    FROM categories
    ORDER BY category_name
    """

    result3 = pd.read_sql(query3, conn)

    print("\nQUERY 3 - Distinct Categories")
    print(result3.to_string(index=False))

    # ---------------------------------------------------------
    # QUERY 4: BETWEEN
    # ---------------------------------------------------------
    query4 = """
    SELECT title, price_gbp, rating
    FROM books
    WHERE price_gbp BETWEEN 20 AND 40
    ORDER BY price_gbp
    """

    result4 = pd.read_sql(query4, conn)

    print("\nQUERY 4 - Books priced between £20 and £40")
    print(result4.head(10).to_string(index=False))

    # ---------------------------------------------------------
    # QUERY 5: IN
    # ---------------------------------------------------------
    query5 = """
    SELECT title, price_gbp, rating
    FROM books
    WHERE rating IN (4, 5)
    ORDER BY rating DESC, price_gbp DESC
    """

    result5 = pd.read_sql(query5, conn)

    print("\nQUERY 5 - Books with rating 4 or 5")
    print(result5.head(10).to_string(index=False))

    # ---------------------------------------------------------
    # QUERY 6: JOIN
    # ---------------------------------------------------------
    join_query = """
    SELECT
        b.title,
        b.price_gbp,
        b.price_inr,
        b.rating,
        c.category_name
    FROM books b
    JOIN categories c
        ON b.category_id = c.category_id
    ORDER BY b.rating DESC, b.title ASC
    LIMIT 10
    """

    sql_join_result = pd.read_sql(join_query, conn)

    print("\nQUERY 6 - JOIN Books with Categories")
    print(sql_join_result.to_string(index=False))

    # ---------------------------------------------------------
    # LOAD TABLES INTO PANDAS
    # ---------------------------------------------------------
    books_df = pd.read_sql(
        "SELECT * FROM books",
        conn
    )

    categories_df = pd.read_sql(
        "SELECT * FROM categories",
        conn
    )

    # ---------------------------------------------------------
    # REPRODUCE JOIN USING pd.merge()
    # ---------------------------------------------------------
    merge_result = pd.merge(
        books_df,
        categories_df,
        on="category_id",
        how="inner"
    )

    merge_result = merge_result[
        [
            "title",
            "price_gbp",
            "price_inr",
            "rating",
            "category_name"
        ]
    ]

    merge_result = merge_result.sort_values(
        by=["rating", "title"],
        ascending=[False, True]
    ).head(10).reset_index(drop=True)

    sql_join_result = sql_join_result.reset_index(drop=True)

    # ---------------------------------------------------------
    # CHECK WHETHER SQL JOIN AND pd.merge() ARE EQUIVALENT
    # ---------------------------------------------------------
    results_match = sql_join_result.equals(merge_result)

    print("\n" + "=" * 60)
    print("JOIN RESULT USING pd.merge()")
    print("=" * 60)

    print(merge_result.to_string(index=False))

    print("\nSQL JOIN and pd.merge() results match:", results_match)

    # ---------------------------------------------------------
    # SAVE QUERY OUTPUTS
    # ---------------------------------------------------------
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:

        file.write("ZEPTO DATA PIPELINE - SQL QUERY OUTPUTS\n")
        file.write("=" * 60 + "\n\n")

        file.write("QUERY 1 - SELECT + WHERE\n")
        file.write(query1.strip() + "\n\n")
        file.write(result1.to_string(index=False))
        file.write("\n\n")

        file.write("QUERY 2 - ORDER BY + LIMIT\n")
        file.write(query2.strip() + "\n\n")
        file.write(result2.to_string(index=False))
        file.write("\n\n")

        file.write("QUERY 3 - DISTINCT\n")
        file.write(query3.strip() + "\n\n")
        file.write(result3.to_string(index=False))
        file.write("\n\n")

        file.write("QUERY 4 - BETWEEN\n")
        file.write(query4.strip() + "\n\n")
        file.write(result4.to_string(index=False))
        file.write("\n\n")

        file.write("QUERY 5 - IN\n")
        file.write(query5.strip() + "\n\n")
        file.write(result5.to_string(index=False))
        file.write("\n\n")

        file.write("QUERY 6 - JOIN\n")
        file.write(join_query.strip() + "\n\n")
        file.write(sql_join_result.to_string(index=False))
        file.write("\n\n")

        file.write("JOIN RESULT USING pd.merge()\n")
        file.write("-" * 60 + "\n")
        file.write(merge_result.to_string(index=False))
        file.write("\n\n")

        file.write(
            f"SQL JOIN and pd.merge() results match: {results_match}\n"
        )

    conn.close()

    print("\n" + "=" * 60)
    print("QUERY EXECUTION COMPLETED")
    print("=" * 60)
    print(f"Query outputs saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    run_queries()