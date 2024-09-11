from typing import List
from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter, WebSocket, WebSocketDisconnect
from .. import models, schema, utils, oauth2
from sqlalchemy.orm import Session
from ..database import get_db
from pydantic import BaseModel

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

manager = ConnectionManager()

@router.websocket("/ws/{deck_id}")
async def websocket_endpoint(websocket: WebSocket, deck_id: int, db: Session = Depends(get_db)):
    await manager.connect(websocket, deck_id, db)
    try:
        while True:
            # Receive updated flashcard data
            data = await websocket.receive_json()

            # Convert the incoming data to FlashcardUpdate objects
            updated_flashcards = [FlashcardUpdate(**flashcard) for flashcard in data]
            await manager.broadcast(deck_id, updated_flashcards)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.post("/save/{deck_id}")
async def save_flashcards(deck_id: int, db: Session = Depends(get_db)):
    # Save the in-memory flashcard content back into the database
    flashcards = manager.flashcards.get(deck_id, [])
    for flashcard_data in flashcards:
        flashcard = db.query(models.Card).filter(models.Card.id == flashcard_data["id"]).first()
        if flashcard:
            flashcard.question = flashcard_data["question"]
            flashcard.answer = flashcard_data["answer"]

    db.commit()
    return {"status": "Flashcards saved successfully"}