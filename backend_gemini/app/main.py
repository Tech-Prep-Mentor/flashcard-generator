from fastapi import FastAPI, UploadFile
from app.database import engine, Base

from .routers import user, deck, card, login, share, socket
from fastapi.middleware.cors import CORSMiddleware



Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/files/")
def upload_file(file: UploadFile):
    return {"filename": file.filename}


@app.get("/")
def root():
    return {"message": "Hello World "}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify the allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(deck.router)
app.include_router(card.router)
app.include_router(login.router)
app.include_router(share.router)
app.include_router(socket.router)




