
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models.complaint import Complaint
from app.models.complaint_status_history import ComplaintStatusHistory
from app.models.department import Department
from app.models.user import User
from app.schemas.complaint import ComplaintCreate, ComplaintResponse
from app.services.duplicate_service import find_possible_duplicate
from app.services.ml_service import predict_department
from app.services.priority_service import assign_priority


router = APIRouter(
    prefix="/api/complaints",
    tags=["Complaints"],
)


@router.post(
    "/",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_complaint(
    request: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    description = " ".join(request.description.split())

    if len(description) < 10:
        raise HTTPException(
            status_code=422,
            detail="Complaint description must contain at least 10 characters.",
        )

    locality = (
        " ".join(request.locality.split())
        if request.locality
        else None
    )

    try:
        # 1. Predict the responsible municipal department.
        prediction = predict_department(description)
        department_name = prediction["department"]

        department = (
            db.query(Department)
            .filter(Department.name == department_name)
            .first()
        )

        if department is None:
            department = Department(name=department_name)
            db.add(department)
            db.flush()

        # 2. Assign priority using transparent rules.
        priority_result = assign_priority(description)

        # 3. Find a possible duplicate among existing complaints.
        duplicate = find_possible_duplicate(
            description=description,
            locality=locality,
            db=db,
        )

        # 4. Store the complaint and the processing results.
        complaint = Complaint(
            citizen_id=current_user.id,
            department_id=department.id,
            description=description,
            locality=locality,
            priority=priority_result["priority"],
            priority_reason=priority_result["priority_reason"],
            model_score=prediction.get("model_score"),
            duplicate_of_complaint_id=(
                duplicate["complaint_id"] if duplicate else None
            ),
            duplicate_similarity=(
                duplicate["similarity"] if duplicate else None
            ),
            status="SUBMITTED",
        )

        db.add(complaint)
        db.flush()

        # 5. Record the initial status in the history table.
        history = ComplaintStatusHistory(
            complaint_id=complaint.id,
            changed_by_user_id=current_user.id,
            status="SUBMITTED",
            comment="Complaint submitted by citizen.",
        )
        db.add(history)

        db.commit()
        db.refresh(complaint)

        return complaint

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Complaint could not be processed. Check the server logs.",
        )


@router.get("/", response_model=List[ComplaintResponse])
def list_my_complaints(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Complaint)
        .filter(Complaint.citizen_id == current_user.id)
        .order_by(Complaint.created_at.desc())
        .all()
    )


@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse,
)
def get_my_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    complaint = (
        db.query(Complaint)
        .filter(
            Complaint.id == complaint_id,
            Complaint.citizen_id == current_user.id,
        )
        .first()
    )

    if complaint is None:
        # Do not disclose whether another citizen's complaint exists.
        raise HTTPException(
            status_code=404,
            detail="Complaint not found.",
        )

    return complaint
