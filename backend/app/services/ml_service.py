
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import joblib


# Resolve the backend directory from this file's location.
BACKEND_DIR = Path(__file__).resolve().parents[2]
MODEL_DIR = BACKEND_DIR / "ml_models"

CLASSIFIER_PATH = MODEL_DIR / "classifier.joblib"
VECTORIZER_PATH = MODEL_DIR / "tfidf_vectorizer.joblib"


@lru_cache(maxsize=1)
def load_ml_artifacts():
    """Load the trained classifier and vectorizer once."""

    if not CLASSIFIER_PATH.exists():
        raise FileNotFoundError(
            "Classifier not found: {}".format(CLASSIFIER_PATH)
        )

    if not VECTORIZER_PATH.exists():
        raise FileNotFoundError(
            "TF-IDF vectorizer not found: {}".format(VECTORIZER_PATH)
        )

    classifier = joblib.load(CLASSIFIER_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)

    return classifier, vectorizer


def predict_department(description: str) -> Dict[str, Any]:
    """Predict the municipal department for a complaint."""

    if not isinstance(description, str):
        raise ValueError("Complaint description must be text.")

    cleaned_description = " ".join(description.split())

    if not cleaned_description:
        raise ValueError("Complaint description cannot be empty.")

    classifier, vectorizer = load_ml_artifacts()

    # Use the same fitted TF-IDF vectorizer used during training.
    features = vectorizer.transform([cleaned_description])

    prediction = str(classifier.predict(features)[0])

    result = {
        "department": prediction,
        "model_score": None,
    }

    # Linear SVM decision scores are not calibrated probabilities.
    if hasattr(classifier, "decision_function"):
        scores = classifier.decision_function(features)
        classes = list(classifier.classes_)
        predicted_index = classes.index(prediction)

        if getattr(scores, "ndim", 1) == 1:
            # Handle binary classifiers correctly.
            raw_score = float(scores[0])
            if predicted_index == 1:
                result["model_score"] = raw_score
            else:
                result["model_score"] = -raw_score
        else:
            result["model_score"] = float(
                scores[0][predicted_index]
            )

    return result
