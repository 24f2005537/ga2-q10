import time
import uuid
from collections import defaultdict
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# --- CONFIGURATION ---
ALLOWED_ORIGINS = [
    "https://app-07cips.example.com",
    "https://exam.sanand.workers.dev"
]
BUCKET_SIZE = 11
WINDOW_SECONDS = 10
EMAIL_PLACEHOLDER = "user@example.com"

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        request.state.request_id = req_id
        
        response = await call_next(request)
        
        response.headers["X-Request-ID"] = req_id
        return response

rate_limit_store = defaultdict(list)

# class RateLimitMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         client_id = request.headers.get("X-Client-Id", "anonymous")
#         now = time.time()
        
#         rate_limit_store[client_id] = [t for t in rate_limit_store[client_id] if now - t < WINDOW_SECONDS]
        
#         if len(rate_limit_store[client_id]) >= BUCKET_SIZE:
#             return JSONResponse(
#                 status_code=429,
#                 content={"detail": "Rate limit exceeded"},
#                 headers={"Retry-After": str(WINDOW_SECONDS)}
#             )
        
#         rate_limit_store[client_id].append(now)
#         return await call_next(request)

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_id = request.headers.get("X-Client-Id", "anonymous")
        now = time.time()
        
        rate_limit_store[client_id] = [t for t in rate_limit_store[client_id] if now - t < WINDOW_SECONDS]
        
        if len(rate_limit_store[client_id]) >= BUCKET_SIZE:
            response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )
            
            response.headers["Retry-After"] = str(WINDOW_SECONDS)
            
            origin = request.headers.get("Origin")
            if origin in ALLOWED_ORIGINS:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = "*"
                response.headers["Access-Control-Allow-Headers"] = "*"
                
            return response
        
        rate_limit_store[client_id].append(now)
        return await call_next(request)
        
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestContextMiddleware)

@app.get("/ping")
async def ping(request: Request):
    return {
        "email": "24f2005537@ds.study.iitm.ac.in",
        "request_id": request.state.request_id
    }
