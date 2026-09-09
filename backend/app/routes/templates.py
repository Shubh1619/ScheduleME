from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_business_for_user
from ..models.business import Business
from ..models.template import Template
from ..schemas.template import TemplateCreate, TemplateOut

router = APIRouter(prefix="/businesses/{business_id}/templates", tags=["templates"])


@router.post("", response_model=TemplateOut, status_code=status.HTTP_201_CREATED)
def create_template(
    business_id: int,
    payload: TemplateCreate,
    business: Business = Depends(get_business_for_user),
    db: Session = Depends(get_db),
):
    template = Template(business_id=business_id, **payload.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("", response_model=list[TemplateOut])
def list_templates(
    business_id: int,
    business: Business = Depends(get_business_for_user),
    db: Session = Depends(get_db),
):
    templates = db.scalars(select(Template).where(Template.business_id == business_id)).all()
    return templates


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    business_id: int,
    template_id: int,
    business: Business = Depends(get_business_for_user),
    db: Session = Depends(get_db),
):
    template = db.scalar(
        select(Template).where(Template.id == template_id, Template.business_id == business_id)
    )
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    db.delete(template)
    db.commit()