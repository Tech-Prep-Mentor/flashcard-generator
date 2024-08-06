from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


#User Schema
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int 
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


#Deck Schema
class DeckBase(BaseModel):
    title: str

class DeckCreate(DeckBase):
    pass

class Deck(DeckBase):
    id: int
    created_at: datetime
    owner_id: int
    owner: UserOut

    class Config:
        from_attributes = True

class DeckOut(BaseModel): #use later when implement flashcards
    Deck: Deck

    class Config:
        from_attributes = True


#Card Schema
class CardBase(BaseModel):
    question: str
    answer: str

class CardCreate(CardBase):
    pass

class Card(CardBase):
    id: int
    created_at: datetime
    owner_id: int
    #owner: UserOut         (will implement later after login)

    class Config:
        from_attributes = True

