import re

import pandas as pd


# ============================================================
# DEPARTMENT NORMALIZATION
# ============================================================

DEPARTMENT_NORMALIZATION = {
    # Electrical
    "Electrical": "Electrical Department",
    "Electrical Services": "Electrical Department",
    "Electrical Department": "Electrical Department",

    # Water
    "Water Department": "Water Department",
    "Water Management": "Water Department",
    "Water Services": "Water Department",
    "Waterworks": "Water Department",

    # Roads
    "Roads & Highways": "Roads & Highways",
    "Road Maintenance": "Roads & Highways",
    "Roads": "Roads & Highways",

    # Parks
    "Parks & Recreation": "Parks & Recreation",
    "Parks Department": "Parks & Recreation",

    # Sanitation / waste
    "Sanitation": "Sanitation",
    "Waste Management": "Sanitation",
}


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text: str) -> str:
    """
    Basic text preprocessing for complaint descriptions.
    """

    if pd.isna(text):
        return ""

    text = str(text).lower()

    # Remove URLs
    text = re.sub(
        r"https?://\S+|www\.\S+",
        " ",
        text
    )

    # Remove email addresses
    text = re.sub(
        r"\S+@\S+",
        " ",
        text
    )

    # Keep letters, numbers and whitespace
    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    # Normalize whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


# ============================================================
# DATAFRAME CLEANING
# ============================================================

def clean_dataframe(
    df: pd.DataFrame,
    text_column: str,
    target_column: str
) -> pd.DataFrame:
    """
    Clean the dataset and remove unusable rows.
    """

    result = df.copy()

    # Remove rows where target is missing
    result = result.dropna(
        subset=[target_column]
    )

    # Convert target to string
    result[target_column] = (
        result[target_column]
        .astype(str)
        .str.strip()
    )

    # Clean complaint text
    result[text_column] = (
        result[text_column]
        .apply(clean_text)
    )

    # Remove rows with empty complaint text
    result = result[
        result[text_column].str.len() > 0
    ]

    # Remove exact duplicate rows
    result = result.drop_duplicates()

    # Reset index
    result = result.reset_index(
        drop=True
    )

    return result


# ============================================================
# DEPARTMENT NORMALIZATION FUNCTION
# ============================================================

def normalize_department(
    department: str
) -> str:
    """
    Normalize inconsistent department names
    into a smaller set of consistent routing
    departments.
    """

    department = str(
        department
    ).strip()

    return DEPARTMENT_NORMALIZATION.get(
        department,
        department
    )