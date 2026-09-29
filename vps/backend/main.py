from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import Optional
import asyncpg
import bcrypt
import jwt
import os

# ─────────────────────────────────────────────────────────────────────────────
SECRET_KEY   = os.getenv("SECRET_KEY", "changeme_32_chars_secret_key_!!")
ALGORITHM    = "HS256"
TOKEN_EXPIRE = 60  # minutes
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://argos:argos@db:5432/argos"
)

app = FastAPI(title="Argos API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── DB helper ─────────────────────────────────────────────────────────────────
async def get_db():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        await conn.close()


# ── JWT helpers ───────────────────────────────────────────────────────────────
def create_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    return decode_token(token)


# ── Auth ──────────────────────────────────────────────────────────────────────
@app.post("/auth/login")
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db=Depends(get_db)
):
    user = await db.fetchrow(
        "SELECT * FROM users WHERE username = $1", form.username
    )
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not bcrypt.checkpw(form.password.encode(), user["password"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({
        "sub":       user["username"],
        "role":      user["role"],
        "tenant_id": user["tenant_id"]
    })

    return {
        "access_token": token,
        "token_type":   "bearer",
        "role":         user["role"],
        "tenant_id":    user["tenant_id"]
    }


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# ── Devices ───────────────────────────────────────────────────────────────────
@app.get("/devices")
async def list_devices(
    user=Depends(get_current_user),
    db=Depends(get_db)
):
    if user["role"] == "admin":
        rows = await db.fetch("SELECT * FROM devices ORDER BY id")
    else:
        rows = await db.fetch(
            "SELECT * FROM devices WHERE tenant_id = $1 ORDER BY id",
            user["tenant_id"]
        )
    return [dict(r) for r in rows]


# ── Executions ────────────────────────────────────────────────────────────────
@app.get("/executions")
async def list_executions(
    user=Depends(get_current_user),
    db=Depends(get_db)
):
    if user["role"] == "admin":
        rows = await db.fetch(
            "SELECT * FROM executions ORDER BY created_at DESC LIMIT 50"
        )
    else:
        rows = await db.fetch(
            "SELECT * FROM executions WHERE tenant_id = $1 "
            "ORDER BY created_at DESC LIMIT 50",
            user["tenant_id"]
        )
    return [dict(r) for r in rows]
