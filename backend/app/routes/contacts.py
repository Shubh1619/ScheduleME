import csv
import io
import json
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_business_for_user
from ..models.business import Business
from ..models.contact import Contact
from ..schemas import contact as contact_schemas

router = APIRouter(prefix="/businesses/{business_id}/contacts", tags=["contacts"])


@router.post("", response_model=contact_schemas.ContactOut, status_code=status.HTTP_201_CREATED)
def create_contact(
    business_id: int,
    payload: contact_schemas.ContactCreate,
    business: Business = Depends(get_business_for_user),
    db: Session = Depends(get_db),
):
    contact = Contact(business_id=business_id, **payload.model_dump())
    db.add(contact)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A contact with this phone number already exists",
        )
    db.refresh(contact)
    return contact


@router.post("/upload", response_model=contact_schemas.BulkContactResult)
async def upload_contacts(
    business_id: int,
    file: UploadFile = File(...),
    business: Business = Depends(get_business_for_user),
    db: Session = Depends(get_db),
):
    payload = await file.read()
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = payload.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or "name" not in reader.fieldnames or "phone" not in reader.fieldnames:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CSV must have a header row with at least 'name' and 'phone' columns",
        )

    existing = set(
        db.scalars(select(Contact.phone).where(Contact.business_id == business_id)).all()
    )
    seen = set()
    created = 0
    skipped = 0
    errors: list[str] = []

    for index, row in enumerate(reader, start=2):
        try:
            name = (row.get("name") or "").strip()
            phone = (row.get("phone") or "").strip()
            if not name:
                raise ValueError("missing name")
            phone = contact_schemas._normalize_phone(phone)
            if phone in seen or phone in existing:
                skipped += 1
                continue

            parsed: dict = {}
            raw_attrs = (row.get("attributes") or "").strip()
            if raw_attrs:
                parsed = json.loads(raw_attrs)
            opted_in = (row.get("opted_in") or "").strip().lower() in ("", "1", "true", "yes", "y")
            db.add(Contact(business_id=business_id, name=name, phone=phone, attributes=parsed, opted_in=opted_in))
            seen.add(phone)
            created += 1
        except Exception as exc:  # noqa: BLE001 - collect per-row errors
            errors.append(f"row {index}: {exc}")

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One or more phone numbers already exist and could not be inserted",
        )

    return contact_schemas.BulkContactResult(created=created, skipped=skipped, errors=errors)


@router.get("", response_model=list[contact_schemas.ContactOut])
def list_contacts(
    business_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    q: Optional[str] = Query(None),
    business: Business = Depends(get_business_for_user),
    db: Session = Depends(get_db),
):
    stmt = select(Contact).where(Contact.business_id == business_id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Contact.name.ilike(like), Contact.phone.ilike(like)))
    contacts = db.scalars(stmt.order_by(Contact.created_at.desc()).offset(skip).limit(limit)).all()
    return contacts


@router.get("/{contact_id}", response_model=contact_schemas.ContactOut)
def get_contact(
    business_id: int,
    contact_id: int,
    business: Business = Depends(get_business_for_user),
    db: Session = Depends(get_db),
):
    contact = db.scalar(
        select(Contact).where(Contact.id == contact_id, Contact.business_id == business_id)
    )
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.patch("/{contact_id}", response_model=contact_schemas.ContactOut)
def update_contact(
    business_id: int,
    contact_id: int,
    payload: contact_schemas.ContactUpdate,
    business: Business = Depends(get_business_for_user),
    db: Session = Depends(get_db),
):
    contact = db.scalar(
        select(Contact).where(Contact.id == contact_id, Contact.business_id == business_id)
    )
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A contact with this phone number already exists",
        )
    db.refresh(contact)
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    business_id: int,
    contact_id: int,
    business: Business = Depends(get_business_for_user),
    db: Session = Depends(get_db),
):
    contact = db.scalar(
        select(Contact).where(Contact.id == contact_id, Contact.business_id == business_id)
    )
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    db.delete(contact)
    db.commit()