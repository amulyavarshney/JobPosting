from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BrandProfile
from app.schemas import BrandProfileRead, BrandProfileUpdate
from app.seed import seed_brand_profile

router = APIRouter(prefix="/brand", tags=["brand"])


def _ensure_brand(db: Session) -> BrandProfile:
    brand = db.query(BrandProfile).order_by(BrandProfile.id.asc()).first()
    if brand:
        return brand
    seed_brand_profile(db)
    return db.query(BrandProfile).order_by(BrandProfile.id.asc()).first()


@router.get("", response_model=BrandProfileRead)
def get_brand(db: Session = Depends(get_db)):
    return _ensure_brand(db)


@router.patch("", response_model=BrandProfileRead)
def update_brand(payload: BrandProfileUpdate, db: Session = Depends(get_db)):
    brand = _ensure_brand(db)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(brand, key, value)
    db.commit()
    db.refresh(brand)
    return brand
