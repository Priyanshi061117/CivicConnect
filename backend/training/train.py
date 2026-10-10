from pathlib import Path
import json
import sys

import joblib
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)


# ============================================================
# IMPORT PREPROCESSING FUNCTIONS
# ============================================================

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent

sys.path.append(str(BACKEND_DIR))

from training.preprocessing import (
    clean_dataframe,
    normalize_department,
)


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = BACKEND_DIR.parent

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "municipal_training_set_1100.csv"
)

MODEL_DIR = BACKEND_DIR / "ml_models"

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# ML CONFIGURATION
# ============================================================

RANDOM_STATE = 42

TEST_SIZE = 0.20

# A department needs at least this many examples
# after normalization to be considered learnable.
MIN_CLASS_SAMPLES = 5

# Columns used for the ML task.
TEXT_COLUMN = "issue_description"

TARGET_COLUMN = "municipal_department"


# ============================================================
# DATASET INSPECTION
# ============================================================

def inspect_dataset(df: pd.DataFrame):
    """
    Print basic information about the original dataset.
    """

    print("\n" + "=" * 70)
    print("DATASET INSPECTION")
    print("=" * 70)

    print(f"\nRows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    print("\nColumn names:")

    for column in df.columns:
        print(f"  - {column}")

    print("\nMissing values:")

    missing = df.isnull().sum()

    for column, count in missing.items():
        print(f"  - {column}: {count}")

    duplicate_count = df.duplicated().sum()

    print(f"\nDuplicate rows: {duplicate_count}")


# ============================================================
# ISSUE TYPE → DEPARTMENT INSPECTION
# ============================================================

def inspect_issue_type_department_relationship(
    df: pd.DataFrame
):
    """
    Show how issue types are distributed across departments.

    This is useful for validating the structure of the dataset
    before training.
    """

    print("\n" + "=" * 70)
    print("ISSUE TYPE → MUNICIPAL DEPARTMENT")
    print("=" * 70)

    if "issue_type" not in df.columns:
        print("\nColumn 'issue_type' was not found.")
        return

    mapping = (
        df
        .groupby(TARGET_COLUMN)["issue_type"]
        .value_counts()
    )

    print(mapping)


# ============================================================
# RARE CLASS HANDLING
# ============================================================

def remove_rare_departments(
    df: pd.DataFrame,
    target_column: str,
    minimum_samples: int
):
    """
    Remove target classes with fewer than the minimum number
    of examples.

    This is done AFTER department normalization.

    The original CSV is never modified.
    """

    counts = (
        df[target_column]
        .value_counts()
    )

    rare_departments = (
        counts[counts < minimum_samples]
        .sort_values()
    )

    print("\n" + "=" * 70)
    print("RARE DEPARTMENT HANDLING")
    print("=" * 70)

    if rare_departments.empty:

        print(
            f"\nNo departments have fewer than "
            f"{minimum_samples} examples."
        )

        return df, {}

    print(
        f"\nDepartments with fewer than "
        f"{minimum_samples} examples will be excluded:"
    )

    for department, count in rare_departments.items():

        print(
            f"  - {department}: {count} example(s)"
        )

    rare_names = set(
        rare_departments.index
    )

    filtered_df = df[
        ~df[target_column].isin(rare_names)
    ].copy()

    filtered_df.reset_index(
        drop=True,
        inplace=True
    )

    return filtered_df, {
        str(department): int(count)
        for department, count
        in rare_departments.items()
    }


# ============================================================
# MODEL EVALUATION
# ============================================================

def evaluate_model(
    model_name,
    model,
    X_train,
    X_test,
    y_train,
    y_test
):
    """
    Train and evaluate one classifier.
    """

    print("\n" + "-" * 70)
    print(f"Training: {model_name}")
    print("-" * 70)

    model.fit(
        X_train,
        y_train
    )

    predictions = model.predict(
        X_test
    )

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    precision = precision_score(
        y_test,
        predictions,
        average="weighted",
        zero_division=0
    )

    recall = recall_score(
        y_test,
        predictions,
        average="weighted",
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        predictions,
        average="weighted",
        zero_division=0
    )

    print(
        f"Accuracy : {accuracy:.4f}"
    )

    print(
        f"Precision: {precision:.4f}"
    )

    print(
        f"Recall   : {recall:.4f}"
    )

    print(
        f"F1 Score : {f1:.4f}"
    )

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0
        )
    )

    labels = sorted(
        set(y_test).union(
            set(predictions)
        )
    )

    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=labels
    )

    result = {
        "model": model_name,
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "confusion_matrix": matrix.tolist(),
        "labels": labels,
    }

    return result, model


# ============================================================
# MAIN TRAINING PIPELINE
# ============================================================

def main():

    print("=" * 70)
    print("AI CIVIC COMPLAINT ROUTER - PHASE 1")
    print("=" * 70)

    # --------------------------------------------------------
    # 1. LOAD DATASET
    # --------------------------------------------------------

    if not DATA_PATH.exists():

        raise FileNotFoundError(
            f"\nDataset not found:\n"
            f"{DATA_PATH}\n\n"
            f"Place the CSV inside the data/ folder."
        )

    print("\nLoading dataset:")
    print(DATA_PATH)

    df = pd.read_csv(
        DATA_PATH
    )

    # --------------------------------------------------------
    # 2. INSPECT DATASET
    # --------------------------------------------------------

    inspect_dataset(df)

    # --------------------------------------------------------
    # 3. VALIDATE REQUIRED COLUMNS
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("ML TASK CONFIGURATION")
    print("=" * 70)

    print(
        f"\nText column  : {TEXT_COLUMN}"
    )

    print(
        f"Target column: {TARGET_COLUMN}"
    )

    if TEXT_COLUMN not in df.columns:

        raise ValueError(
            f"\nRequired text column "
            f"'{TEXT_COLUMN}' was not found."
        )

    if TARGET_COLUMN not in df.columns:

        raise ValueError(
            f"\nRequired target column "
            f"'{TARGET_COLUMN}' was not found."
        )

    # --------------------------------------------------------
    # 4. INSPECT ISSUE TYPE / DEPARTMENT RELATIONSHIP
    # --------------------------------------------------------

    inspect_issue_type_department_relationship(
        df
    )

    # --------------------------------------------------------
    # 5. ORIGINAL DEPARTMENT DISTRIBUTION
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("ORIGINAL DEPARTMENT DISTRIBUTION")
    print("=" * 70)

    print(
        df[TARGET_COLUMN]
        .value_counts(
            dropna=False
        )
    )

    # --------------------------------------------------------
    # 6. CLEAN DATA
    # --------------------------------------------------------

    cleaned_df = clean_dataframe(
        df,
        TEXT_COLUMN,
        TARGET_COLUMN
    )

    # --------------------------------------------------------
    # 7. NORMALIZE DEPARTMENT LABELS
    # --------------------------------------------------------

    cleaned_df[TARGET_COLUMN] = (
        cleaned_df[TARGET_COLUMN]
        .apply(normalize_department)
    )

    print("\n" + "=" * 70)
    print("AFTER CLEANING + DEPARTMENT NORMALIZATION")
    print("=" * 70)

    print(
        f"\nRows remaining: "
        f"{len(cleaned_df)}"
    )

    print("\nNormalized department distribution:")

    print(
        cleaned_df[TARGET_COLUMN]
        .value_counts()
    )

    # --------------------------------------------------------
    # 8. REMOVE RARE DEPARTMENTS
    # --------------------------------------------------------

    cleaned_df, excluded_departments = (
        remove_rare_departments(
            cleaned_df,
            TARGET_COLUMN,
            MIN_CLASS_SAMPLES
        )
    )

    print("\n" + "=" * 70)
    print("FINAL ML DATASET")
    print("=" * 70)

    print(
        f"\nRows used for ML: "
        f"{len(cleaned_df)}"
    )

    print(
        f"Minimum examples per department: "
        f"{MIN_CLASS_SAMPLES}"
    )

    categories = sorted(
        cleaned_df[TARGET_COLUMN]
        .unique()
    )

    print(
        f"\nNumber of departments used for ML: "
        f"{len(categories)}"
    )

    print("\nDepartments used:")

    for category in categories:

        count = (
            cleaned_df[TARGET_COLUMN]
            .value_counts()
            .get(category, 0)
        )

        print(
            f"  - {category}: {count}"
        )

    # --------------------------------------------------------
    # 9. FINAL SAFETY CHECK
    # --------------------------------------------------------

    final_counts = (
        cleaned_df[TARGET_COLUMN]
        .value_counts()
    )

    if (
        final_counts < MIN_CLASS_SAMPLES
    ).any():

        raise ValueError(
            "Rare-class filtering failed. "
            "At least one department still has "
            "fewer than the required number of examples."
        )

    if len(categories) < 2:

        raise ValueError(
            "At least two departments are required "
            "for classification."
        )

    # --------------------------------------------------------
    # 10. PREPARE X AND Y
    # --------------------------------------------------------

    X = cleaned_df[
        TEXT_COLUMN
    ]

    y = cleaned_df[
        TARGET_COLUMN
    ]

    # --------------------------------------------------------
    # 11. TRAIN / TEST SPLIT
    # --------------------------------------------------------

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=TEST_SIZE,
            random_state=RANDOM_STATE,
            stratify=y
        )
    )

    print("\n" + "=" * 70)
    print("TRAIN / TEST SPLIT")
    print("=" * 70)

    print(
        f"\nTraining samples: "
        f"{len(X_train)}"
    )

    print(
        f"Testing samples : "
        f"{len(X_test)}"
    )

    # --------------------------------------------------------
    # 12. TF-IDF
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TF-IDF")
    print("=" * 70)

    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1,
        max_df=0.95,
        sublinear_tf=True
    )

    # IMPORTANT:
    # Fit TF-IDF ONLY on training data.
    X_train_tfidf = (
        vectorizer.fit_transform(
            X_train
        )
    )

    # Transform test data using the fitted vectorizer.
    X_test_tfidf = (
        vectorizer.transform(
            X_test
        )
    )

    print(
        f"\nTF-IDF training matrix: "
        f"{X_train_tfidf.shape}"
    )

    print(
        f"TF-IDF testing matrix : "
        f"{X_test_tfidf.shape}"
    )

    # --------------------------------------------------------
    # 13. DEFINE CLASSIFIERS
    # --------------------------------------------------------

    models = {

        "Logistic Regression": LogisticRegression(
            max_iter=2000,
            random_state=RANDOM_STATE
        ),

        "Linear SVM": LinearSVC(
            random_state=RANDOM_STATE
        ),

        "Multinomial Naive Bayes": MultinomialNB()
    }

    # --------------------------------------------------------
    # 14. TRAIN + EVALUATE ALL MODELS
    # --------------------------------------------------------

    results = []

    trained_models = {}

    for model_name, model in models.items():

        result, trained_model = (
            evaluate_model(
                model_name,
                model,
                X_train_tfidf,
                X_test_tfidf,
                y_train,
                y_test
            )
        )

        results.append(
            result
        )

        trained_models[
            model_name
        ] = trained_model

    # --------------------------------------------------------
    # 15. MODEL COMPARISON
    # --------------------------------------------------------

    comparison = pd.DataFrame(
        [
            {
                "Model": result["model"],
                "Accuracy": result["accuracy"],
                "Precision": result["precision"],
                "Recall": result["recall"],
                "F1 Score": result["f1_score"],
            }
            for result in results
        ]
    )

    comparison = comparison.sort_values(
        by="F1 Score",
        ascending=False
    )

    print("\n" + "=" * 70)
    print("MODEL COMPARISON")
    print("=" * 70)

    print(
        comparison.to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}"
        )
    )

    # --------------------------------------------------------
    # 16. SELECT BEST MODEL
    # --------------------------------------------------------

    best_model_name = (
        comparison.iloc[0]["Model"]
    )

    best_model = (
        trained_models[
            best_model_name
        ]
    )

    best_result = next(
        result
        for result in results
        if result["model"]
        == best_model_name
    )

    print("\n" + "=" * 70)
    print("BEST MODEL")
    print("=" * 70)

    print(
        f"\nSelected model: "
        f"{best_model_name}"
    )

    print(
        f"Accuracy: "
        f"{best_result['accuracy']:.4f}"
    )

    print(
        f"Precision: "
        f"{best_result['precision']:.4f}"
    )

    print(
        f"Recall: "
        f"{best_result['recall']:.4f}"
    )

    print(
        f"F1 Score: "
        f"{best_result['f1_score']:.4f}"
    )

    # --------------------------------------------------------
    # 17. SAVE BEST CLASSIFIER
    # --------------------------------------------------------

    classifier_path = (
        MODEL_DIR
        / "classifier.joblib"
    )

    joblib.dump(
        best_model,
        classifier_path
    )

    # --------------------------------------------------------
    # 18. SAVE TF-IDF VECTORIZER
    # --------------------------------------------------------

    vectorizer_path = (
        MODEL_DIR
        / "tfidf_vectorizer.joblib"
    )

    joblib.dump(
        vectorizer,
        vectorizer_path
    )

    # --------------------------------------------------------
    # 19. SAVE METADATA
    # --------------------------------------------------------

    metadata = {

        "text_column": TEXT_COLUMN,

        "target_column": TARGET_COLUMN,

        "original_row_count": int(
            len(df)
        ),

        "cleaned_row_count": int(
            len(cleaned_df)
        ),

        "training_samples": int(
            len(X_train)
        ),

        "testing_samples": int(
            len(X_test)
        ),

        "random_state": RANDOM_STATE,

        "test_size": TEST_SIZE,

        "minimum_class_samples":
            MIN_CLASS_SAMPLES,

        "excluded_rare_departments":
            excluded_departments,

        "categories": categories,

        "best_model": best_model_name,

        "metrics": best_result,

        "all_model_results": results,

        "tfidf_configuration": {
            "ngram_range": [1, 2],
            "min_df": 1,
            "max_df": 0.95,
            "sublinear_tf": True
        }
    }

    metadata_path = (
        MODEL_DIR
        / "model_metadata.json"
    )

    with open(
        metadata_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            metadata,
            file,
            indent=4
        )

    # --------------------------------------------------------
    # 20. SAVE MODEL COMPARISON
    # --------------------------------------------------------

    comparison_path = (
        MODEL_DIR
        / "model_comparison.csv"
    )

    comparison.to_csv(
        comparison_path,
        index=False
    )

    # --------------------------------------------------------
    # 21. FINAL SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("FILES SAVED")
    print("=" * 70)

    print(
        f"\nClassifier:"
        f"\n{classifier_path}"
    )

    print(
        f"\nTF-IDF vectorizer:"
        f"\n{vectorizer_path}"
    )

    print(
        f"\nMetadata:"
        f"\n{metadata_path}"
    )

    print(
        f"\nModel comparison:"
        f"\n{comparison_path}"
    )

    print("\n" + "=" * 70)
    print("PHASE 1 COMPLETED SUCCESSFULLY")
    print("=" * 70)

    print(
        "\nThe trained model predicts:"
    )

    print(
        "issue_description → municipal_department"
    )

    print(
        "\nPriority prediction is NOT part of this ML model."
    )

    print(
        "Priority will be handled separately using "
        "an explainable rule-based engine."
    )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()