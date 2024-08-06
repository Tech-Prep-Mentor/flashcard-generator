from typing import List
from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter, UploadFile, File
from .. import models, schema, utils
from sqlalchemy.orm import Session
from ..database import get_db
from io import BytesIO

router = APIRouter(
    prefix="/deck",
    tags=['Deck']
)


#DECK CREATION
@router.get("/", response_model=List[schema.Deck])
def get_decks(db: Session = Depends(get_db)):

    decks = db.query(models.Deck).all()

    return decks

@router.post("/", response_model=schema.Deck, status_code=status.HTTP_201_CREATED)
def create_deck(deck: schema.DeckCreate, db: Session = Depends(get_db)):
    
    new_deck = models.Deck(owner_id = 1, **deck.dict())    #default owner_id = 1 , must change later when implement login

    db.add(new_deck)
    db.commit()
    db.refresh(new_deck)

    return new_deck

@router.get("/{id}", response_model=schema.Deck)            #can be used to show detailed descriptions of each deck
def get_deck(id: int, db: Session = Depends(get_db)):
    
    deck = db.query(models.Deck).filter(models.Deck.id == id).first()

    if not deck:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Deck with {id} not found")
    print(deck)
    return deck

@router.put("/{id}", response_model=schema.Deck)
def update_deck(id: int, updated_deck: schema.DeckCreate, db: Session = Depends(get_db)):
    
    deck_query = db.query(models.Deck).filter(models.Deck.id == id)
    deck = deck_query.first()

    if deck == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Deck with {id} not found")
    
    deck_query.update(updated_deck.dict(), synchronize_session=False)
    db.commit()

    return deck_query.first()

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deck(id: int, db: Session = Depends(get_db)):
    deck_query = db.query(models.Deck).filter(models.Deck.id == id)
    deck = deck_query.first()

    if deck == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Deck with {id} not found")
    
    deck_query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

#CARD CREATION (BASED ON DECK_ID)
@router.get("/{id}/cards", response_model=List[schema.CardBase])
def get_cards_by_deck(id: int, db: Session = Depends(get_db)):
    cards = db.query(models.Card).filter(models.Card.owner_id==id).all()

    return cards


@router.post("/{id}/cards", response_model=List[schema.Card])
def create_cards_by_deck(id: int, db: Session = Depends(get_db), file: UploadFile = File(...)):

    pdf_content = file.file.read()
    pdf_file = BytesIO(pdf_content)

    generated_cards = utils.generate_flashcards_from_pdf(pdf_file)
    output = []
    for card in generated_cards:
        new_card = models.Card(owner_id = id, question=card["question"], answer=card["answer"])
        output.append(new_card)
        db.add(new_card)
        db.commit()
        db.refresh(new_card)

    return output