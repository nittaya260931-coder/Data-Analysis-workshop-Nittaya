from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).parent
RAW_PATH = BASE_DIR / "data" / "retail_sales_dirty.csv"
CLEAN_PATH = BASE_DIR / "data" / "retail_sales_cleaned.csv"
LOG_PATH = BASE_DIR / "data" / "retail_sales_quality_log.csv"


data = pd.read_csv(RAW_PATH)
quality_log = []

# Standardize labels where the intended value is unambiguous.
data["Region"] = data["Region"].str.strip().str.title()
data["Category"] = data["Category"].replace({"Electronic": "Electronics"})

quality_log.extend(
    [
        {
            "issue": "Region formatting",
            "rows": "5, 19",
            "action": "corrected",
            "reason": "Normalized south and SOUTH to South.",
        },
        {
            "issue": "Category label",
            "rows": "24",
            "action": "corrected",
            "reason": "Electronic is treated as the spelling variant of Electronics.",
        },
    ]
)

# Remove only a fully identical duplicate; retain the first occurrence.
duplicate_mask = data.duplicated(keep="first")
if duplicate_mask.any():
    duplicate_rows = ", ".join(str(index + 2) for index in data.index[duplicate_mask])
    data = data.loc[~duplicate_mask].copy()
    quality_log.append(
        {
            "issue": "Exact duplicate",
            "rows": duplicate_rows,
            "action": "removed duplicate occurrence",
            "reason": "The complete row was identical; the first occurrence was retained.",
        }
    )

# Preserve ambiguous values and record them for business review.
review_checks = {
    "Missing Sales": data["Sales"].isna(),
    "Missing Profit": data["Profit"].isna(),
    "Negative Quantity": data["Quantity"] < 0,
    "Discount outside 0-1": (data["Discount"] < 0) | (data["Discount"] > 1),
    "Negative Profit": data["Profit"] < 0,
}
for issue, mask in review_checks.items():
    if mask.any():
        rows = ", ".join(str(index + 2) for index in data.index[mask])
        quality_log.append(
            {
                "issue": issue,
                "rows": rows,
                "action": "flagged for review",
                "reason": "No business rule was available to infer a replacement value.",
            }
        )

data.to_csv(CLEAN_PATH, index=False)
pd.DataFrame(quality_log).to_csv(LOG_PATH, index=False)
print(f"Wrote {CLEAN_PATH}")
print(f"Wrote {LOG_PATH}")