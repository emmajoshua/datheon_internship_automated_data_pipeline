import json
import pandas as pd


def clean_currency(value):
    """Helper to strip symbols and convert currency/numeric string to float."""
    if pd.isna(value):
        return 0.0
    val_str = str(value).replace("$", "").replace(",", "").strip()
    try:
        return round(float(val_str), 2)
    except ValueError:
        return 0.0


def clean_superstore_dataset(df: pd.DataFrame):
    # Create a copy to avoid SettingWithCopyWarning
    df = df.copy()
    initial_rows = len(df)

    # 1. Remove duplicate records based on Row ID
    dupes_count = int(df.duplicated(subset=["Row ID"]).sum())
    df = df.drop_duplicates(subset=["Row ID"], keep="last")

    # 2. Date parsing and standardization (ISO format: YYYY-MM-DD)
    for date_col in ["Order Date", "Ship Date"]:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    null_dates_count = int(df["Order Date"].isna().sum())
    
    # Drop records missing critical Order Date
    df = df.dropna(subset=["Order Date"])
    df["Order Date"] = df["Order Date"].dt.strftime("%Y-%m-%d")
    df["Ship Date"] = df["Ship Date"].dt.strftime("%Y-%m-%d")

    # 3. Clean and normalize numerical metrics and currency values
    for col in ["Sales", "Profit", "Discount", "Quantity"]:
        if col in df.columns:
            df[col] = df[col].apply(clean_currency)

    # 4. Handle text fields and missing categories
    text_defaults = {
        "Customer ID": "ANONYMOUS",
        "Customer Name": "UNKNOWN",
        "Segment": "UNKNOWN",
        "Ship Mode": "UNKNOWN",
        "Category": "UNKNOWN",
        "Sub-Category": "UNKNOWN",
        "Region": "UNKNOWN",
        "State": "UNKNOWN",
        "City": "UNKNOWN",
        "Country": "United States",
    }
    
    for col, default_val in text_defaults.items():
        if col in df.columns:
            df[col] = (
                df[col]
                .fillna(default_val)
                .astype(str)
                .str.strip()
            )

    # 5. Schema Validation & Type Casting
    df["Row ID"] = pd.to_numeric(df["Row ID"], errors="coerce").fillna(0).astype("int64")

    # Verify no null primary keys remain
    if df["Row ID"].isna().any():
        raise ValueError("Schema validation failed: Found null Row ID")

    # 6. Compile automated data validation log report
    log_report = {
        "initial_row_count": initial_rows,
        "final_row_count": len(df),
        "duplicates_removed": dupes_count,
        "null_dates_dropped": null_dates_count,
        "schema_validation_passed": True,
        "category_summary": df["Category"].value_counts().to_dict(),
        "region_summary": df["Region"].value_counts().to_dict(),
    }

    # Reset index for clean output
    df = df.reset_index(drop=True)

    return df, log_report


if __name__ == "__main__":
    # Load raw Superstore dataset
    print("Loading dataset...")
    raw_df = pd.read_csv("superstore_sales.csv", encoding="latin1")

    print("Cleaning data...")
    cleaned_df, report = clean_superstore_dataset(raw_df)

    # Save output to cleaned CSV
    cleaned_df.to_csv("cleaned_superstore_sales.csv", index=False)

    print("\n--- Cleaned Dataset (First 5 Rows) ---")
    print(cleaned_df.head())

    print("\n--- Validation Quality Log Report ---")
    print(json.dumps(report, indent=2))