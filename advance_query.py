import mysql.connector
import pandas as pd


def run_advanced_analytics():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="global_budget_db"
    )

    cursor = conn.cursor()

    # 1. Anasysis: Year-over-Year (YoY) Growth & 5-Year Rolling Moving Average
    moving_avg_query = """
    SELECT
        c.country_name,
        b.year,
        b.total_budget_billions_usd,
        AVG(b.total_budget_billions_usd) OVER (
            PARTITION BY c.country_name
            ORDER BY b.year
            ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
        ) AS rolling_5yr_avg
    FROM budgets b
    JOIN countries c
        ON b.country_id = c.country_id;
    """

    df_moving = pd.read_sql(moving_avg_query, conn)

    print("\n--- 1. 5-Year Rolling Budget Trends ---\n")
    print(df_moving.head())

    # 2.ANALYSIS: Historic Sector Dominance Matrix (Isolating the #1 funded sector per year)
    dominance_query = """
    WITH RankedSectors AS (
        SELECT
            c.country_name,
            b.year,
            sa.sector_name,
            sa.allocated_percentage,
            DENSE_RANK() OVER (
                PARTITION BY c.country_name, b.year
                ORDER BY sa.allocated_percentage DESC
            ) AS rnk
        FROM sector_allocations sa
        JOIN budgets b
            ON sa.budget_id = b.budget_id
        JOIN countries c
            ON b.country_id = c.country_id
    )
    SELECT
        country_name,
        year,
        sector_name,
        allocated_percentage
    FROM RankedSectors
    WHERE rnk = 1;
    """

    df_dom = pd.read_sql(dominance_query, conn)

    print("\n--- 2. Historic #1 Budget Priorities ---\n")
    print(df_dom.head())

    conn.close()


if __name__ == "__main__":
    run_advanced_analytics()