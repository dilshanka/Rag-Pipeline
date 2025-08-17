# rag_api.py

from fastapi import FastAPI
from pydantic import BaseModel
from rag_pipeline import rag_pipeline 
from fastapi.responses import PlainTextResponse

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(request: ChatRequest):
    response = rag_pipeline(request.message)
    return {"response": response} 
