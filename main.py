import uuid
import time
from collections import defaultdict
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

ALLOWED_ORIGINS = ["https://app-07cips.example.com", "sanand.workers.dev"] 
RATE_LIMIT_B = 11
RATE_LIMIT_WINDOW = 10 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    # allow_origins=ALLOWED_ORIGINS,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    # allow_headers=["X-Request-ID", "X-Client-Id"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

rate_limit_store = defaultdict(list)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_id = request.headers.get("X-Client-Id")
    if client_id:
        now = time.time()
        rate_limit_store[client_id] = [ts for ts in rate_limit_store[client_id] if now - ts < RATE_LIMIT_WINDOW]
        
        if len(rate_limit_store[client_id]) >= RATE_LIMIT_B:
            return Response(content="Too many requests", status_code=429)
        
        rate_limit_store[client_id].append(now)
        
    return await call_next(request)

@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    
    response = await call_next(request)
    
    response.headers["X-Request-ID"] = request_id
    return response

@app.middleware("http")
async def debug_headers(request: Request, call_next):
    print(f"DEBUG: Origin: {request.headers.get('origin')}")
    print(f"DEBUG: Headers: {dict(request.headers)}")
    return await call_next(request)

@app.get("/ping", include_in_schema=False)
@app.get("/ping")
def ping(request: Request):
    return {
        "email": "24f2005537@ds.study.iitm.ac.in", 
        "request_id": request.state.request_id
    }
