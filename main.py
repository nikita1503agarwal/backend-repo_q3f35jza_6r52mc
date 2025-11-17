import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from database import create_document, get_documents, db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SignupPayload(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    avatar_url: Optional[str] = None

class LoginPayload(BaseModel):
    email: EmailStr

class ProfileUpdate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    avatar_url: Optional[str] = None

class RequestPayload(BaseModel):
    email: EmailStr
    text: Optional[str] = None
    photo_data_url: Optional[str] = None
    audio_data_url: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

@app.get("/")
def read_root():
    return {"message": "Messaging API running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response

@app.post("/auth/signup")
def signup(payload: SignupPayload):
    # Upsert-like behavior: if user exists, return it; else create
    existing = db["appuser"].find_one({"email": payload.email}) if db else None
    if existing:
        return {"status": "ok", "user": {"email": existing.get("email"), "name": existing.get("name"), "avatar_url": existing.get("avatar_url")}}
    user_doc = {
        "email": str(payload.email),
        "name": payload.name,
        "avatar_url": payload.avatar_url,
    }
    _id = create_document("appuser", user_doc)
    return {"status": "ok", "user": {"email": payload.email, "name": payload.name, "avatar_url": payload.avatar_url}, "id": _id}

@app.post("/auth/login")
def login(payload: LoginPayload):
    existing = db["appuser"].find_one({"email": payload.email}) if db else None
    if not existing:
        raise HTTPException(status_code=404, detail="User not found. Please sign up first.")
    return {"status": "ok", "user": {"email": existing.get("email"), "name": existing.get("name"), "avatar_url": existing.get("avatar_url")}}

@app.get("/profile")
def get_profile(email: EmailStr):
    existing = db["appuser"].find_one({"email": str(email)}) if db else None
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    return {"email": existing.get("email"), "name": existing.get("name"), "avatar_url": existing.get("avatar_url")}

@app.put("/profile")
def update_profile(update: ProfileUpdate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    db["appuser"].update_one({"email": str(update.email)}, {"$set": {"name": update.name, "avatar_url": update.avatar_url, "updated_at": __import__('datetime').datetime.utcnow()}}, upsert=True)
    doc = db["appuser"].find_one({"email": str(update.email)})
    return {"status": "ok", "user": {"email": doc.get("email"), "name": doc.get("name"), "avatar_url": doc.get("avatar_url")}}

@app.post("/request")
def create_request(payload: RequestPayload):
    data = {
        "email": str(payload.email),
        "text": payload.text,
        "photo_url": payload.photo_data_url,  # store as data URL
        "audio_url": payload.audio_data_url,  # store as data URL
        "contact_name": payload.contact_name,
        "contact_phone": payload.contact_phone,
        "lat": payload.lat,
        "lng": payload.lng,
        "status": "sent",
    }
    req_id = create_document("request", data)
    return {"status": "ok", "id": req_id}

@app.get("/requests")
def list_requests(email: EmailStr, limit: int = 20):
    docs = get_documents("request", {"email": str(email)}, limit)
    # Transform _id to str and remove large data URLs to avoid heavy payloads
    items = []
    for d in docs:
        d["id"] = str(d.get("_id"))
        d.pop("_id", None)
        preview = d.copy()
        if preview.get("photo_url"):
            preview["photo_url"] = "data:image/*;base64,[truncated]"
        if preview.get("audio_url"):
            preview["audio_url"] = "data:audio/*;base64,[truncated]"
        items.append(preview)
    return {"items": items}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
