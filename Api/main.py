from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from routers.auth import auth_router
from routers.admin import admin_router
from dotenv import load_dotenv
from routers.profiles import profiles_router # <-- ADD THIS LINE

print("Loading environment variables...")  
load_dotenv()

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(title="User Management API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Allow your Angular app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(profiles_router)

@app.get("/")
async def root():
    return {"message": "User Management API is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
