import pandas as pd
import mysql.connector
from mysql.connector import Error 

def run_robust_etl(csv_path):

    df = pd.read_csv(csv_path)
    # Handle any potential global missing data issues
    df = df.fillna(0)

    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="yourusername",
            password="yourpassward",
            database="global_budget_db"
        )
        cursor = conn.cursor()

        print("🚀 Step 1: Seeding Country Dimensiors...")
        unique_countries = df['Country'].unique()
        for country in unique_countries:
            cursor.execute("INSERT IGNORE INTO countries (country_name) VALUES (%s)", (country.strip(),))
        
        # Explicitly commit the demension table first
        conn.commit()

        # Build an in-memory dictionary to look up IDs instantly
        cursor.execute("SELECT country_name, country_id FROM countries")
        country_lookup = dict(cursor.fetchall())

        # The exact text prefixes from the CSV columns
        sectors = ['Defense','Education','Health','Interest_Payments',
                   'Infrastructure','Agriculture','State_Transfers','Social_Welfare','Administration_and_Others']
        
        print(f"🚀 Step 2: Ingesting {len(df)} Fact Records...")
        success_count = 0

        for idx, row in df.iterrows():
            try:
                country_name = row['Country'].strip()
                country_id = country_lookup[country_name]
                year = int(row['Year'])
                total_budget = float(row['Total_Budget_Billions_USD'])

                # Insert core budget header record
                cursor.execute(
                    "INSERT INTO budgets (country_id,year,total_budget_billions_usd) VALUES (%s,%s,%s)",
                    (country_id,year,total_budget)
                )
                budget_id = cursor.lastrowid

                # Unpivot and map individual sector metrics
                for sector in sectors:
                    pct_col = f"{sector}_Percentage"
                    amt_col = f"{sector}_Amount_Billions_USD"

                    cursor.execute(
                        """INSERT INTO sector_allocations
                        (budget_id, sector_name, allocated_percentage, allocated_amount_billions_usd)
                        VALUES (%s,%s,%s,%s)""",
                        (budget_id, sector, float(row[pct_col]), float(row[amt_col]))
                    )
                success_count += 1

            except Error as row_err:
                print(f"⚠️ Error processing row {idx} ({country_name}-{year}): {row_err}")
                continue

        # CRITICAL: Final block save verification
        conn.commit()
        print(f"🏁 ETL Complete! Successfully committed {success_count} structural records into MYSQL.")

    except Error as db_err:
        print(f"❌ Structural datbase connection failure: {db_err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    run_robust_etl("Master_Global_Budgets_Historical.csv")
