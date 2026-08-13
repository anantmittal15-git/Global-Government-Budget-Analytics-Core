import pandas as pd
from sqlalchemy import create_engine


def analyze_budget_volatility(country_name):
    engine = create_engine(
        "mysql+pymysql://root:root@localhost/global_budget_db"
    )

    # Extract historical spending sequence
    query = """
    SELECT b.year, b.total_budget_billions_usd
    FROM budgets b
    JOIN countries c ON b.country_id = c.country_id
    WHERE c.country_name = %s
    ORDER BY b.year ASC;
    """

    df = pd.read_sql(query, engine, params=(country_name,))

    if df.empty:
        return

    # Calculate 10-year rolling mean and standard deviation using pandas
    df['rolling_mean'] = (
        df['total_budget_billions_usd']
        .rolling(window=10)
        .mean()
    )

    df['rolling_std'] = (
        df['total_budget_billions_usd']
        .rolling(window=10)
        .std()
    )

    # Calculate Volatility Index (Coefficient of Variation)
    df['volatility_index'] = (
        (df['rolling_std'] / df['rolling_mean']) * 100
    )

    print(
        f"\n--- Volatility Index for {country_name} (Sample) ---"
    )
    print(df.dropna().head(10))

    return df
if __name__ == "__main__":
    analyze_budget_volatility("United States") # or your country name