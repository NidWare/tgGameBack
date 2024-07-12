from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import user_routes  # Use relative import
from .database import create_tables

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing purposes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_routes.router)

@app.on_event("startup")
def startup():
    create_tables()
