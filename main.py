import uuid
import time
from collections import defaultdict
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

# Configuration
ALLOWED_ORIGIN = "https://app-07cips.example.com"
# Note: You should add your specific exam grader domain to this list
ALLOWED_ORIGINS = [ALLOWED_ORIGIN, "http://localhost:8001"] 
RATE_LIMIT_B = 11
RATE_LIMIT_WINDOW = 10 

# State stores
rate_limit_store = defaultdict(list)

# --- Middleware 1: Request Context (Added last, executes first) ---
@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    # Set ID in response header
    response.headers["X-Request-ID"] = request_id
    return response

# --- Middleware 2: Rate Limiting ---
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_id = request.headers.get("X-Client-Id")
    if client_id:
        now = time.time()
        # Clean expired window
        rate_limit_store[client_id] = [ts for ts in rate_limit_store[client_id] if now - ts < RATE_LIMIT_WINDOW]
        
        if len(rate_limit_store[client_id]) >= RATE_LIMIT_B:
            return Response(content="Too many requests", status_code=429)
        
        rate_limit_store[client_id].append(now)
        
    return await call_next(request)

# --- Middleware 3: CORS (Added first, executes last) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Endpoint ---
@app.get("/ping")
def ping(request: Request):
    return {
        "email": "24f2005537@ds.study.iitm.ac.in", 
        "request_id": request.state.request_id
    }
