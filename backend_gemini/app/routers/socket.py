from typing import List
from fastapi import Depends, APIRouter, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from .. import models, schema, utils, oauth2
from sqlalchemy.orm import Session
from ..database import get_db
from pydantic import BaseModel
import asyncio

router = APIRouter(
    prefix="/socket",
    tags=['Socket']
)
class FlashcardUpdate(BaseModel):
    id: int
    question: str
    answer: str

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.flashcards = {}  # To keep track of real-time flashcard data for each deck

    async def connect(self, websocket: WebSocket, deck_id: int, db: Session = Depends(get_db)):
        await websocket.accept()
        self.active_connections.append(websocket)

        # Fetch the flashcards from the database for the given deck_id
        flashcard = db.query(models.Card).filter(models.Card.owner_id == deck_id).all()
        flashcard_data = [{"id": f.id, "question": f.question, "answer": f.answer} for f in flashcard]
        self.flashcards[deck_id] = flashcard_data

        # Send current flashcard content to the client
        await websocket.send_json(flashcard_data)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, deck_id: int, message: List[FlashcardUpdate]):
        # Update the in-memory flashcards
        self.flashcards[deck_id] = message

        # Send the updated flashcards to all connected clients
        for connection in self.active_connections:
            await connection.send_json([f.dict() for f in message])
    '''
    async def save_to_database(self, deck_id: int, db: Session):
        # Save the in-memory flashcard content back into the database
        flashcards = self.flashcards.get(deck_id, [])
        for flashcard_data in flashcards:
            flashcard = db.query(models.Card).filter(models.Card.id == flashcard_data["id"]).first()
            if flashcard:
                flashcard.question = flashcard_data["question"]
                flashcard.answer = flashcard_data["answer"]

        db.commit()
    '''

manager = ConnectionManager()

@router.websocket("/ws/{deck_id}")
async def websocket_endpoint(websocket: WebSocket, deck_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    await manager.connect(websocket, deck_id, db)

    try:
        while True:
            # Receive updated flashcard data in real-time
            data = await websocket.receive_json()

            # Convert the incoming data to FlashcardUpdate objects
            updated_flashcards = [FlashcardUpdate(**flashcard) for flashcard in data]
            await manager.broadcast(deck_id, updated_flashcards)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    
@router.put("/save/{deck_id}")
async def save_flashcards(deck_id: int, flashcards: List[FlashcardUpdate], db: Session = Depends(get_db)):
    # Save the flashcard content to the database
    cards = db.query(models.Card).filter(models.Card.owner_id==deck_id).all()
    card_lookup = {card.id: card for card in cards}
    try:
        for flashcard_data in flashcards:
            if flashcard_data.id in card_lookup:
                card = card_lookup[flashcard_data.id]
                if flashcard_data.question is not None:
                    card.question = flashcard_data.question
                if flashcard_data.answer is not None:
                    card.answer = flashcard_data.answer
        db.commit()
        return {"message": "Flashcards updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error saving flashcards")