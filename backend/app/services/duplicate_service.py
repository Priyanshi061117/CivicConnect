
from typing import Optional, Dict, Any

from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.services.ml_service import load_ml_artifacts


def normalize_locality(locality: Optional[str]) -> Optional[str]:
    if not locality:
        return None

    normalized = " ".join(locality.casefold().split())
    return normalized or None


def find_possible_duplicate(
    description: str,
    locality: Optional[str],
    db: Session,
) -> Optional[Dict[str, Any]]:
    """
    Return the best existing complaint that passes the
    similarity threshold, or None if no candidate is found.

    Known, different localities are not treated as duplicates.
    """

    existing_complaints = db.query(Complaint).all()

    if not existing_complaints:
        return None

    classifier, vectorizer = load_ml_artifacts()

    new_vector = vectorizer.transform([description])

    existing_vectors = vectorizer.transform(
        [complaint.description for complaint in existing_complaints]
    )

    similarities = cosine_similarity(
        new_vector, existing_vectors
    ).flatten()

    new_locality = normalize_locality(locality)
    best_match = None
    best_similarity = -1.0

    for complaint, similarity in zip(
        existing_complaints, similarities
    ):
        existing_locality = normalize_locality(
            complaint.locality
        )

        similarity = float(similarity)

        # If both locations are known and differ, skip the match.
        if (
            new_locality
            and existing_locality
            and new_locality != existing_locality
        ):
            continue

        # Matching locality permits a lower text threshold.
        if new_locality and existing_locality:
            threshold = 0.65
        else:
            threshold = 0.82

        if (
            similarity >= threshold
            and similarity > best_similarity
        ):
            best_similarity = similarity
            best_match = {
                "complaint_id": complaint.id,
                "similarity": round(similarity, 4),
            }

    return best_match
