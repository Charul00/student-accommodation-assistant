from fastapi import FastAPI
from app.routes import chat

app = FastAPI(title="Student Accommodation Assistant")

app.include_router(chat.router)

@app.get("/")
def health_check():
    return {"status": "Backend is running "}