from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import os

from routers.auth import auth_router
from routers.admin import admin_router
from dotenv import load_dotenv
from routers.profiles import profiles_router # <-- ADD THIS LINE
from routers.firms import firms_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    print("Loading environment variables...")
    load_dotenv()
    logger.info("Environment variables loaded successfully.")
except Exception as e:
    logger.error(f"Error loading environment variables: {e}")

port = int(os.environ.get("PORT", 8001))

app = FastAPI(title="User Management API")

try:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:4201"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS middleware configured.")
except Exception as e:
    logger.error(f"Error configuring CORS middleware: {e}")

try:
    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(profiles_router)
    app.include_router(firms_router)
    logger.info("Routers included successfully.")
except Exception as e:
    logger.error(f"Error including routers: {e}")

@app.get("/")
async def root():
    logger.info("Root endpoint accessed.")
    try:
        return {"message": "User Management API is running"}
    except Exception as e:
        logger.error(f"Error in root endpoint: {e}")
        return {"error": "Internal server error"}

if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=port)
        logger.info("Uvicorn server started.")
    except Exception as e:
        logger.error(f"Error starting Uvicorn server: {e}")
