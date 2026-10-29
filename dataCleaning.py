"""
Task 2: Automated Data Cleaning & Schema Transformation
Cleans raw transaction data, standardizes formats, validates schema, 
and generates a quality summary report.
"""

import json
import pandas as pd


def clean_currency(value):
    """Helper to strip symbols and convert currency string to float."""
    if pd.isna(value):
        return 0.0
    val_str = str(value).replace("$", "").replace(",", "").strip()
    try:
        return round(float(val_str), 2)
    except ValueError:
        return 0.0


def clean_dataset(df: pd.DataFrame):
    # Track metrics for validation log
    initial_rows = len(df)
    log_report = {}

    # 1. Remove duplicate records based on transaction_id
    dupes_count = int(df.duplicated(subset=["transaction_id"]).sum())
    df = df.drop_duplicates(subset=["transaction_id"], keep="last")

    # 2. Date parsing and standardization (ISO format: YYYY-MM-DD)
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    null_dates_count = int(df["transaction_date"].isna().sum())
    
    # Drop records missing critical transaction dates
    df = df.dropna(subset=["transaction_date"])
    df["transaction_date"] = df["transaction_date"].dt.strftime("%Y-%m-%d")

    # 3. Clean and normalize currency values
    df["amount"] = df["amount"].apply(clean_currency)

    # 4. Handle text fields and missing categories
    df["status"] = (
        df["status"]
        .fillna("UNKNOWN")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["customer_id"] = (
        df["customer_id"]
        .fillna("ANONYMOUS")
        .astype(str)
        .str.strip()
    )

    # 5. Schema Validation & Type Casting
    schema = {
        "transaction_id": "int64",
        "customer_id": "object",
        "transaction_date": "object",
        "amount": "float64",
        "status": "object",
    }
    df = df.astype(schema)

    # Verify no null primary keys remain
    if df["transaction_id"].isna().any():
        raise ValueError("Schema validation failed: Found null transaction_id")

    # 6. Compile automated data validation log
    log_report = {
        "initial_row_count": initial_rows,
        "final_row_count": len(df),
        "duplicates_removed": dupes_count,
        "null_dates_dropped": null_dates_count,
        "schema_validation_passed": True,
        "status_summary": df["status"].value_counts().to_dict(),
    }

    # Reset index for clean output
    df = df.reset_index(drop=True)

    return df, log_report


if __name__ == "__main__":
    # Sample dirty dataset
    raw_data = {
        "transaction_id": [1001, 1002, 1003, 1002, 1004],
        "customer_id": [" C001 ", "C002", None, "C002", "C003"],
        "transaction_date": [
            "2023/11/01",
            "Nov 02, 2023",
            "not_a_date",
            "2023-11-02",
            "2023.11.04",
        ],
        "amount": ["$1,250.50", "340.00", "$99.99", "340.00", None],
        "status": [" completed ", "PENDING", "completed", "PENDING", None],
    }

    raw_df = pd.DataFrame(raw_data)

    print("Cleaning data...")
    cleaned_df, report = clean_dataset(raw_df)

    # Optionally save output to CSV
    cleaned_df.to_csv("cleaned_transactions.csv", index=False)

    print("\n--- Cleaned Dataset ---")
    print(cleaned_df)

    print("\n--- Validation Quality Log ---")
    print(json.dumps(report, indent=2))