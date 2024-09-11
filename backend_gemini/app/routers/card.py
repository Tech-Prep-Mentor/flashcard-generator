from typing import List
from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter, UploadFile, File
from .. import models, schema, utils
from sqlalchemy.orm import Session
from ..database import get_db
from io import BytesIO


router = APIRouter(
    prefix="/card",
    tags=['Card']
)

@router.post("/", response_model=List[schema.Card])
def create_cards(db: Session = Depends(get_db), file: UploadFile = File(...)):

    pdf_content = file.file.read()
    pdf_file = BytesIO(pdf_content)

    generated_cards = utils.generate_flashcards_from_pdf(pdf_file)
    output = []
    for card in generated_cards:
        new_card = models.Card(owner_id = 3, question=card["question"], answer=card["answer"])      #logic for deck_owner_id added later
        output.append(new_card)
        db.add(new_card)
        db.commit()
        db.refresh(new_card)

    return output


@router.get("/", response_model=List[schema.CardBase])
def get_cards_by_deck(db: Session = Depends(get_db)):   #logic for deck_id added later
    cards = db.query(models.Card).filter(models.Card.owner_id==3).all()

    return cards


