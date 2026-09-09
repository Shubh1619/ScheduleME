from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_business_for_user, get_current_user
from ..models.business import Business
from ..models.user import User
from ..schemas.business import BusinessCreate, BusinessOut

router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.post("", response_model=BusinessOut, status_code=status.HTTP_201_CREATED)
def create_business(payload: BusinessCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    business = Business(user_id=user.id, business_name=payload.business_name)
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


@router.get("", response_model=list[BusinessOut])
def list_businesses(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    businesses = db.scalars(select(Business).where(Business.user_id == user.id)).all()
    return businesses


@router.get("/{business_id}", response_model=BusinessOut)
def get_business(business: Business = Depends(get_business_for_user)):
    return business