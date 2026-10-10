from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.department import Department
from app.models.complaint import Complaint
from app.models.complaint_status_history import ComplaintStatusHistory
from app.models.duplicate_review import DuplicateReview


router = APIRouter(tags=["Phase 5"])


STATUSES = {
    "SUBMITTED",
    "CLASSIFIED",
    "ASSIGNED",
    "IN_PROGRESS",
    "RESOLVED",
    "CLOSED",
    "REJECTED",
}

TRANSITIONS = {
    "SUBMITTED": {"CLASSIFIED", "ASSIGNED", "IN_PROGRESS", "REJECTED"},
    "CLASSIFIED": {"ASSIGNED", "IN_PROGRESS", "REJECTED"},
    "ASSIGNED": {"IN_PROGRESS", "REJECTED"},
    "IN_PROGRESS": {"RESOLVED", "REJECTED"},
    "RESOLVED": {"CLOSED", "IN_PROGRESS"},
    "CLOSED": set(),
    "REJECTED": set(),
}


class StatusUpdate(BaseModel):
    status: str
    comment: str | None = Field(default=None, max_length=2000)


class DuplicateReviewRequest(BaseModel):
    decision: str
    comment: str | None = Field(default=None, max_length=2000)


class UserUpdate(BaseModel):
    role: str | None = None
    department_id: int | None = None
    is_active: bool | None = None


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)


def require_roles(*roles):
    def dependency(user: User = Depends(get_current_user)):
        if user.role.lower() not in roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to perform this action.",
            )
        return user

    return dependency


def visible_complaint(
    complaint_id: int,
    user: User,
    db: Session,
) -> Complaint:
    complaint = (
        db.query(Complaint)
        .filter(Complaint.id == complaint_id)
        .first()
    )

    if complaint is None:
        raise HTTPException(status_code=404, detail="Complaint not found.")

    role = user.role.lower()

    if role == "admin":
        return complaint

    if role == "official":
        if (
            user.department_id is None
            or complaint.department_id != user.department_id
        ):
            raise HTTPException(status_code=404, detail="Complaint not found.")
        return complaint

    if role == "citizen" and complaint.citizen_id == user.id:
        return complaint

    raise HTTPException(status_code=404, detail="Complaint not found.")


def official_or_admin(user: User):
    role = user.role.lower()

    if role not in {"official", "admin"}:
        raise HTTPException(status_code=403, detail="Officials only.")

    if role == "official" and user.department_id is None:
        raise HTTPException(
            status_code=403,
            detail="Your account has no assigned department.",
        )


def complaint_query_for_staff(db: Session, user: User):
    query = db.query(Complaint)

    if user.role.lower() == "official":
        if user.department_id is None:
            raise HTTPException(
                status_code=403,
                detail="Your account has no assigned department.",
            )
        query = query.filter(
            Complaint.department_id == user.department_id
        )

    return query


@router.get("/api/complaints/{complaint_id}/history")
def complaint_history(
    complaint_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    complaint = visible_complaint(complaint_id, user, db)

    records = (
        db.query(ComplaintStatusHistory)
        .filter(
            ComplaintStatusHistory.complaint_id == complaint.id
        )
        .order_by(ComplaintStatusHistory.created_at.asc())
        .all()
    )

    return [
        {
            "id": record.id,
            "complaint_id": record.complaint_id,
            "status": record.status,
            "comment": record.comment,
            "created_at": record.created_at,
            "changed_by": (
                record.changed_by.full_name
                if record.changed_by else None
            ),
        }
        for record in records
    ]


@router.get("/api/official/complaints")
def official_complaints(
    status_filter: str | None = None,
    priority: str | None = None,
    locality: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    official_or_admin(user)
    query = complaint_query_for_staff(db, user)

    if status_filter:
        query = query.filter(
            Complaint.status == status_filter.upper()
        )

    if priority:
        query = query.filter(
            Complaint.priority == priority.upper()
        )

    if locality:
        query = query.filter(
            Complaint.locality.ilike(f"%{locality.strip()}%")
        )

    if search:
        term = search.strip()
        if term.isdigit():
            query = query.filter(Complaint.id == int(term))
        else:
            query = query.filter(
                Complaint.description.ilike(f"%{term}%")
            )

    complaints = query.order_by(Complaint.created_at.desc()).all()

    return [
        {
            "id": c.id,
            "description": c.description,
            "locality": c.locality,
            "status": c.status,
            "priority": c.priority,
            "priority_reason": c.priority_reason,
            "department_id": c.department_id,
            "citizen_id": c.citizen_id,
            "duplicate_of_complaint_id": c.duplicate_of_complaint_id,
            "duplicate_similarity": c.duplicate_similarity,
            "created_at": c.created_at,
        }
        for c in complaints
    ]


@router.patch("/api/official/complaints/{complaint_id}/status")
def update_complaint_status(
    complaint_id: int,
    request: StatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    official_or_admin(user)

    complaint = visible_complaint(complaint_id, user, db)
    new_status = request.status.strip().upper()

    if new_status not in STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status. Allowed values: {sorted(STATUSES)}",
        )

    if new_status not in TRANSITIONS.get(complaint.status, set()):
        raise HTTPException(
            status_code=409,
            detail=f"Transition from {complaint.status} to {new_status} is not allowed.",
        )

    old_status = complaint.status

    try:
        complaint.status = new_status

        history = ComplaintStatusHistory(
            complaint_id=complaint.id,
            changed_by_user_id=user.id,
            status=new_status,
            comment=request.comment,
        )

        db.add(history)
        db.commit()
        db.refresh(complaint)

        return {
            "message": "Complaint status updated.",
            "complaint_id": complaint.id,
            "old_status": old_status,
            "new_status": complaint.status,
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not update complaint status.",
        )


@router.get("/api/official/duplicates")
def list_duplicate_candidates(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    official_or_admin(user)

    query = complaint_query_for_staff(db, user).filter(
        Complaint.duplicate_of_complaint_id.is_not(None)
    )

    candidates = query.order_by(Complaint.created_at.desc()).all()
    result = []

    for candidate in candidates:
        original = (
            db.query(Complaint)
            .filter(
                Complaint.id == candidate.duplicate_of_complaint_id
            )
            .first()
        )

        review = (
            db.query(DuplicateReview)
            .filter(DuplicateReview.complaint_id == candidate.id)
            .first()
        )

        result.append({
            "complaint_id": candidate.id,
            "description": candidate.description,
            "locality": candidate.locality,
            "priority": candidate.priority,
            "status": candidate.status,
            "duplicate_similarity": candidate.duplicate_similarity,
            "original_complaint_id": (
                original.id if original else None
            ),
            "original_description": (
                original.description if original else None
            ),
            "review_decision": review.decision if review else None,
            "review_comment": review.comment if review else None,
        })

    return result


@router.post("/api/official/duplicates/{complaint_id}/review")
def review_duplicate(
    complaint_id: int,
    request: DuplicateReviewRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    official_or_admin(user)

    complaint = visible_complaint(complaint_id, user, db)

    if complaint.duplicate_of_complaint_id is None:
        raise HTTPException(
            status_code=400,
            detail="This complaint has no duplicate candidate.",
        )

    decision = request.decision.strip().upper()

    if decision not in {"RELATED", "DISMISSED"}:
        raise HTTPException(
            status_code=422,
            detail="Decision must be RELATED or DISMISSED.",
        )

    review = (
        db.query(DuplicateReview)
        .filter(DuplicateReview.complaint_id == complaint.id)
        .first()
    )

    if review is None:
        review = DuplicateReview(
            complaint_id=complaint.id,
            reviewed_by_user_id=user.id,
            decision=decision,
            comment=request.comment,
        )
        db.add(review)
    else:
        review.reviewed_by_user_id = user.id
        review.decision = decision
        review.comment = request.comment

    db.commit()

    return {
        "message": "Duplicate review saved.",
        "complaint_id": complaint.id,
        "decision": decision,
    }


def analytics_for_query(query, db: Session):
    complaints = query.all()

    by_status = {}
    by_priority = {}
    by_department = {}

    for complaint in complaints:
        by_status[complaint.status] = (
            by_status.get(complaint.status, 0) + 1
        )
        by_priority[complaint.priority] = (
            by_priority.get(complaint.priority, 0) + 1
        )

        department = (
            db.query(Department)
            .filter(Department.id == complaint.department_id)
            .first()
            if complaint.department_id else None
        )

        department_name = department.name if department else "Unassigned"
        by_department[department_name] = (
            by_department.get(department_name, 0) + 1
        )

    resolved = sum(
        1 for c in complaints
        if c.status in {"RESOLVED", "CLOSED"}
    )

    return {
        "total": len(complaints),
        "pending": len(complaints) - resolved,
        "resolved": resolved,
        "by_status": by_status,
        "by_priority": by_priority,
        "by_department": by_department,
    }


@router.get("/api/official/analytics")
def official_analytics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    official_or_admin(user)
    query = complaint_query_for_staff(db, user)
    return analytics_for_query(query, db)


@router.get("/api/admin/analytics")
def admin_analytics(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    return analytics_for_query(db.query(Complaint), db)


@router.get("/api/admin/users")
def admin_list_users(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    users = db.query(User).order_by(User.id.asc()).all()

    return [
        {
            "id": item.id,
            "full_name": item.full_name,
            "email": item.email,
            "role": item.role,
            "is_active": item.is_active,
            "department_id": item.department_id,
            "department": (
                item.department.name if item.department else None
            ),
        }
        for item in users
    ]


@router.patch("/api/admin/users/{user_id}")
def admin_update_user(
    user_id: int,
    request: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles("admin")),
):
    target = db.query(User).filter(User.id == user_id).first()

    if target is None:
        raise HTTPException(status_code=404, detail="User not found.")

    changes = request.model_dump(exclude_unset=True)

    role = changes.get("role", target.role)
    role = role.lower() if role else target.role

    if role not in {"citizen", "official", "admin"}:
        raise HTTPException(
            status_code=422,
            detail="Role must be citizen, official, or admin.",
        )

    department_id = changes.get(
        "department_id", target.department_id
    )

    if role == "official":
        if department_id is None:
            raise HTTPException(
                status_code=422,
                detail="Officials must have a department.",
            )

        department = (
            db.query(Department)
            .filter(Department.id == department_id)
            .first()
        )

        if department is None:
            raise HTTPException(
                status_code=422,
                detail="Department not found.",
            )
    else:
        department_id = None

    if user_id == admin.id and changes.get("is_active") is False:
        raise HTTPException(
            status_code=400,
            detail="You cannot deactivate your own account.",
        )

    target.role = role
    target.department_id = department_id

    if "is_active" in changes:
        target.is_active = changes["is_active"]

    db.commit()
    db.refresh(target)

    return {
        "id": target.id,
        "full_name": target.full_name,
        "email": target.email,
        "role": target.role,
        "is_active": target.is_active,
        "department_id": target.department_id,
    }


@router.get("/api/admin/departments")
def admin_list_departments(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    return [
        {"id": d.id, "name": d.name}
        for d in db.query(Department).order_by(Department.name).all()
    ]


@router.post("/api/admin/departments", status_code=201)
def admin_create_department(
    request: DepartmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    name = " ".join(request.name.split())

    existing = (
        db.query(Department)
        .filter(func.lower(Department.name) == name.lower())
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Department already exists.",
        )

    department = Department(name=name)
    db.add(department)
    db.commit()
    db.refresh(department)

    return {"id": department.id, "name": department.name}