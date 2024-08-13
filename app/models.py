from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from .database import Base
 
class UserDeck(Base):
    __tablename__ = 'user_deck'

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    deck_id = Column(Integer, ForeignKey("decks.id"), primary_key=True)

    user = relationship("User", back_populates="shared_decks")
    deck = relationship("Deck", back_populates="shared_with_users")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    shared_decks = relationship("UserDeck", back_populates="user")


class Deck(Base):
    __tablename__ = 'decks'

    id = Column(Integer, primary_key = True, nullable=False)
    title = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    owner = relationship("User")
    shared_with_users = relationship("UserDeck", back_populates="deck")

class Card(Base):
    __tablename__ = 'cards'

    id = Column(Integer, primary_key = True, nullable=False)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    owner_id = Column(Integer, ForeignKey("decks.id", ondelete="CASCADE"), nullable=False)

    owner = relationship("Deck")

