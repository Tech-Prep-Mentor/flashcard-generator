from typing import List
from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter, UploadFile, File
from .. import models, schema, utils, oauth2
from sqlalchemy.orm import Session
from ..database import get_db
from io import BytesIO

router = APIRouter(
    prefix="/deck",
    tags=['Deck']
)

'''
deck.py file is used to perform operations by the owner of the decks
If a user wants to access shared decks, the code is in share.py
'''

#DECK CREATION
#get all available decks, belong to current user
@router.get("/", response_model=List[schema.Deck])
def get_decks(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    decks = db.query(models.Deck).filter(models.Deck.owner_id == current_user.id).all()

    return decks

#create a new deck
@router.post("/", response_model=schema.Deck, status_code=status.HTTP_201_CREATED)
def create_deck(deck: schema.DeckCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    
    new_deck = models.Deck(owner_id = current_user.id, **deck.dict())    

    db.add(new_deck)
    db.commit()
    db.refresh(new_deck)

    return new_deck

#get one specific deck by id (NO NEED this endpoint at the moment)
@router.get("/{id}", response_model=schema.Deck)            #can be used to show detailed descriptions of each deck
def get_deck(id: int, db: Session = Depends(get_db)):
    
    deck = db.query(models.Deck).filter(models.Deck.id == id).first()

    if not deck:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Deck with {id} not found")
    print(deck)
    return deck

#edit one specific deck by id
@router.put("/{deck_id}", response_model=schema.Deck) 
def update_deck(deck_id: int, updated_deck: schema.DeckCreate, db: Session = Depends(get_db), 
                current_user: int = Depends(oauth2.get_current_user)):
    
    deck_query = db.query(models.Deck).filter(models.Deck.id == deck_id)
    deck = deck_query.first()

    if deck == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Deck with {id} not found")
    
    if deck.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only the owner can edit this")
    
    
    deck_query.update(updated_deck.dict(), synchronize_session=False)
    db.commit()

    return deck_query.first()

#delete a deck by id
@router.delete("/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deck(deck_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    deck_query = db.query(models.Deck).filter(models.Deck.id == deck_id)
    deck = deck_query.first()

    if deck == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Deck with {id} not found")
    
    if deck.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this deck")
    
    deck_query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)



#CARD CREATION (BASED ON DECK_ID)
#get all cards in one deck with id
@router.get("/{deck_id}/cards", response_model=List[schema.CardBase])
def get_cards_by_deck(deck_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    deck = db.query(models.Deck).filter(models.Deck.id == deck_id).first()
    if deck.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not allow to view this deck")
    
    cards = db.query(models.Card).filter(models.Card.owner_id==deck_id).all()

    if cards == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No flashcards in this deck")

    return cards

#create cards from input pdf
@router.post("/{deck_id}/cards", response_model=List[schema.Card], status_code=status.HTTP_201_CREATED) 
def create_cards_by_deck(deck_id: int, db: Session = Depends(get_db), file: UploadFile = File(...), 
                         current_user: int = Depends(oauth2.get_current_user)):
    
    deck = db.query(models.Deck).filter(models.Deck.id == deck_id).first()
    if deck.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not allow to create flashcards in this deck")

    pdf_content = file.file.read()
    pdf_file = BytesIO(pdf_content)

    generated_cards = utils.generate_flashcards_from_pdf(pdf_file)
    output = []
    for card in generated_cards:
        new_card = models.Card(owner_id = deck_id, question=card["question"], answer=card["answer"])
        output.append(new_card)
        db.add(new_card)
        db.commit()
        db.refresh(new_card)

    return output

#create card manually
@router.post("/{id}/card", response_model=schema.Card, status_code=status.HTTP_201_CREATED)
def create_card_manually(deck_id: int, card: schema.CardBase, db: Session = Depends(get_db), 
                         current_user: int = Depends(oauth2.get_current_user)):

    deck = db.query(models.Deck).filter(models.Deck.id == deck_id).first()
    if deck.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not allow to create flashcards in this deck")
    
    new_card = models.Card(owner_id = deck_id, **card.dict())

    db.add(new_card)
    db.commit()
    db.refresh(new_card)

    return new_card

#edit mode for all cards in a deck
@router.put("/{id}/cards", response_model=List[schema.Card])
def update_cards(deck_id: int, updated_cards: List[schema.CardUpdate], db: Session = Depends(get_db),
                 current_user: int = Depends(oauth2.get_current_user)):
    
    deck = db.query(models.Deck).filter(models.Deck.id == deck_id).first()
    if deck.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not allow to change flashcards in this deck")
    
    cards = db.query(models.Card).filter(models.Card.owner_id == deck_id).all()
    
    if cards == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="No cards in this deck")
    
    card_lookup = {card.id: card for card in cards}

    for card_update in updated_cards:
        if card_update.id in card_lookup:
            card = card_lookup[card_update.id]
            if card_update.question is not None:
                card.question = card_update.question
            if card_update.answer is not None:
                card.answer = card_update.answer

    db.commit()

    updated_cards = db.query(models.Card).filter(models.Card.owner_id == deck_id).all()
    return updated_cards


#delete card in a deck
@router.delete("/{id}/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(deck_id: int, card_id: int, db: Session = Depends(get_db),
                current_user: int = Depends(oauth2.get_current_user)):
    
    deck = db.query(models.Deck).filter(models.Deck.id == deck_id).first()
    if deck.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not allow to delete flashcards in this deck")
    
    card_query = db.query(models.Card).filter(models.Card.owner_id == deck_id,
                                        models.Card.id == card_id)
    card = card_query.first()

    if card == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Card with {id} not found")
    
    card_query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


    
#User authentication: done
#Card creation done