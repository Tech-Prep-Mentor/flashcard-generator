from .. import models, schema, utils
from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from ..database import get_db

router = APIRouter(
    prefix="/users",
    tags=['Users']
)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schema.UserOut)
def create_user(user: schema.UserCreate, db: Session=Depends(get_db)):

    all_users = [str(x[0]) for x in db.query(models.User.email).all()]

    if user.email in all_users:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exist")

    new_user = models.User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

