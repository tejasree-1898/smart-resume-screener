import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite")
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./resume_screener.db")
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    MAX_FILE_SIZE = 10 * 1024 * 1024  
    ALLOWED_EXTENSIONS = [".pdf", ".docx"]