import pandas as pd

# Canonical gluten group
GLUTEN_CANONICAL = "Cereals containing gluten"
GLUTEN_ALIAS_COLS = {
    "wheat",
    "barley",
    "rye",
    "oats",
    "spelt",
    "kamut",
    "gluten",  # in case the column is literally called 'Gluten'
}

def convert_allergen_csv(input_path: str, output_path: str = "pl_aut_25_upload.csv") -> None:
    # 1. Load the CSV file
    df = pd.read_csv(input_path)

    # 2. Identify the allergen columns
    # Adjust these indices if the file structure changes
    allergen_cols = df.columns[4:25]

    # 3. Define the aggregation function
    def get_allergens(row):
        """Returns a comma-separated string of allergen names present in the row."""
        allergens = []
        has_gluten = False

        for col in allergen_cols:
            cell = str(row[col])
            if "**" in cell:  # marker for allergen present
                col_clean = col.strip()
                col_lower = col_clean.lower()

                # If this column is one of the gluten cereal aliases…
                if col_lower in GLUTEN_ALIAS_COLS:
                    has_gluten = True
                else:
                    allergens.append(col_clean)

        # If any gluten alias was present, add the canonical gluten allergen once
        if has_gluten and GLUTEN_CANONICAL not in allergens:
            allergens.append(GLUTEN_CANONICAL)

        return ", ".join(allergens) if allergens else ""

    # 4. Apply the function to each row and create the new 'allergens' column
    df["allergens"] = df.apply(
        lambda row: get_allergens(row) if pd.notna(row["name"]) and row["name"] != "" else "",
        axis=1,
    )

    # 5. Clean up: remove rows without dish names, drop raw allergen columns
    df_clean = df[df["name"].notna() & (df["name"] != "")]
    df_final = df_clean.drop(columns=allergen_cols, errors="ignore")

    # 6. Save the result to a new file (ready for Django import)
    df_final.to_csv(output_path, index=False)
    print(f"✅ Cleaned file saved as {output_path}")


if __name__ == "__main__":
    in_path = input("Enter path to allergen CSV: ").strip()
    if not in_path:
        raise SystemExit("❌ No input path provided.")

    out_path = input("Enter output filename (default: pl_aut_25_upload.csv): ").strip()
    if not out_path:
        out_path = "pl_aut_25_upload.csv"

    convert_allergen_csv(in_path, out_path)
    print("✅ All done!")