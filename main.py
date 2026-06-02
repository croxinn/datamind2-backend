from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class QuestionRequest(BaseModel):
    question: str
    store_data: Optional[dict] = None

class SignupRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

@app.get("/")
def root():
    return {"status": "DataMind API running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/ai/question")
async def ask_question(req: QuestionRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="API key not configured")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{
                    "parts": [{
                        "text": f"You are a Shopify analytics expert. Answer concisely and practically.\n\n{req.question}"
                    }]
                }]
            },
            timeout=60.0
        )
    
    data = response.json()
    print("Gemini response:", data)
    
    if "candidates" not in data:
        error_msg = data.get("error", {}).get("message", str(data))
        raise HTTPException(status_code=500, detail=f"Gemini error: {error_msg}")
    
    answer = data["candidates"][0]["content"]["parts"][0]["text"]
    return {"answer": answer}

@app.post("/api/auth/signup")
async def signup(req: SignupRequest):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SUPABASE_URL}/auth/v1/signup",
            headers={
                "apikey": SUPABASE_KEY,
                "Content-Type": "application/json"
            },
            json={"email": req.email, "password": req.password}
        )
    data = response.json()
    if "error" in data:
        raise HTTPException(status_code=400, detail=data["error"]["message"])
    return {"message": "Account created successfully", "user": data.get("user")}

@app.post("/api/auth/login")
async def login(req: LoginRequest):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
            headers={
                "apikey": SUPABASE_KEY,
                "Content-Type": "application/json"
            },
            json={"email": req.email, "password": req.password}
        )
    data = response.json()
    if "error" in data:
        raise HTTPException(status_code=400, detail=data["error"]["message"])
    return {
        "access_token": data.get("access_token"),
        "user": data.get("user")
    }

@app.get("/api/shopify/data")
async def get_shopify_data():
    return {
        "revenue": 194900,
        "orders": 1485,
        "aov": 131,
        "return_rate": 4.2,
        "conversion_rate": 11.98
    }