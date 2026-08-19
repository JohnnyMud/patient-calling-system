from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router

app = FastAPI(
    title="Patient Calling System",
    description="API for triggering, monitoring, and auditing AI appointment-reminder calls.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/", tags=["health"])
async def root():
    """Health check endpoint to verify the API is up and running."""
    return {
        "status": "healthy",
        "message": "Patient calling system API",
    }
