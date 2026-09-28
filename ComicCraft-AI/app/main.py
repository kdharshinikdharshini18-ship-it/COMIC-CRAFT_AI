from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="ComicCraft-AI")

app.include_router(router)

@app.get("/")
def home():
    return {"message": "ComicCraft-AI is running!"}