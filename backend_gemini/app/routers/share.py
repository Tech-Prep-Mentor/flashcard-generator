from typing import List
from fastapi import Response, status, HTTPException, Depends, APIRouter, UploadFile, File
from .. import models, schema, oauth2, utils
from sqlalchemy.orm import Session
from ..database import get_db
from io import BytesIO

router = APIRouter(
    prefix="/share",
    tags=['Share']
)
'''
share.py file is used to perform operations by users who have access to other decks rather than theirs
'''

#Share access to other users
@router.post("/{deck_id}")
def share_request(form: schema.Share, db: Session = Depends(get_db)):

    deck = db.query(models.Deck).filter(models.Deck.id == form.deck_id).first()
    if deck == None:
        raise HTTPException(status_code=404, detail="Deck not found")

    user = db.query(models.User).filter(models.User.email == form.user_name).first()
    if user == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with {form.user_name} not found")

    new_share = models.UserDeck(user_id=user.id, deck_id=deck.id)
    db.add(new_share)
    db.commit()
    db.refresh(new_share)
    

    return "Deck is shared succesfully"

#get all shared decks 
@router.get("/", response_model=List[schema.Deck])
def get_shared_decks(current_user: int = Depends(oauth2.get_current_user), db: Session = Depends(get_db)):

    decks = db.query(models.Deck).join(models.UserDeck).filter(models.UserDeck.user_id == current_user.id).all()
    if decks == None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You don't have any shared decks")

    return decks

#get all cards in one deck with id
@router.get("/{deck_id}/cards", response_model=List[schema.CardBase])
def get_cards_by_deck(deck_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    deck = db.query(models.Deck).filter(models.Deck.id == deck_id).join(models.UserDeck).filter(models.UserDeck.user_id == current_user.id).first()
    if deck == None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not allow to view this deck")
    
    cards = db.query(models.Card).filter(models.Card.owner_id==deck_id).all()

    if cards == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No flashcards in this deck")

    return cards


#create cards from input flashcards
@router.post("/{deck_id}/cards", response_model=List[schema.Card], status_code=status.HTTP_201_CREATED) 
def create_cards_by_deck(deck_id: int, db: Session = Depends(get_db), file: UploadFile = File(...), 
                         current_user: int = Depends(oauth2.get_current_user)):
    
    deck = db.query(models.Deck).filter(models.Deck.id == deck_id).join(models.UserDeck).filter(models.UserDeck.user_id == current_user.id).first()
    if deck == None:
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
@router.post("/{deck_id}/card", response_model=schema.Card, status_code=status.HTTP_201_CREATED)
def create_card_manually(deck_id: int, card: schema.CardBase, db: Session = Depends(get_db), 
                         current_user: int = Depends(oauth2.get_current_user)):

    deck = db.query(models.Deck).filter(models.Deck.id == deck_id).join(models.UserDeck).filter(models.UserDeck.user_id == current_user.id).first()
    if deck == None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not allow to create flashcards in this deck")
    
    new_card = models.Card(owner_id = deck_id, **card.dict())

    db.add(new_card)
    db.commit()
    db.refresh(new_card)

    return new_card

#edit mode for all cards in a deck
@router.put("/{deck_id}/cards", response_model=List[schema.Card])
def update_cards(deck_id: int, updated_cards: List[schema.CardUpdate], db: Session = Depends(get_db),
                 current_user: int = Depends(oauth2.get_current_user)):
    
    deck = db.query(models.Deck).filter(models.Deck.id == deck_id).join(models.UserDeck).filter(models.UserDeck.user_id == current_user.id).first()
    if deck == None:
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
@router.delete("/{deck_id}/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(deck_id: int, card_id: int, db: Session = Depends(get_db),
                current_user: int = Depends(oauth2.get_current_user)):
    
    deck = db.query(models.Deck).filter(models.Deck.id == deck_id).join(models.UserDeck).filter(models.UserDeck.user_id == current_user.id).first()
    if deck == None:
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





