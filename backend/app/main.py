from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import os
from typing import List

from .config import Config
from .models import JobDescription, MatchRequest
from .database import Database
from .parsers import ResumeParser
from .matcher import ResumeMatcher

app = FastAPI(
    title="Smart Resume Screener API",
    description="API for parsing resumes and matching with job descriptions using AI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()
resume_parser = ResumeParser()
resume_matcher = ResumeMatcher()

@app.get("/")
async def root():
    return {
        "message": "Smart Resume Screener API",
        "version": "1.0.0",
        "database": "SQLite",
        "endpoints": {
            "/upload-resume": "POST - Upload and parse a resume",
            "/save-job": "POST - Save a job description",
            "/match-resume": "POST - Match a resume with a job",
            "/shortlisted": "GET - Get shortlisted candidates",
            "/resumes": "GET - Get all resumes",
            "/jobs": "GET - Get all jobs",
            "/health": "GET - Health check"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "SQLite",
        "openai_configured": bool(Config.OPENAI_API_KEY)
    }

@app.post("/upload-resume/")
async def upload_resume(file: UploadFile = File(...)):
    try:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in Config.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format. Please upload: {', '.join(Config.ALLOWED_EXTENSIONS)}"
            )
        
        content = await file.read()
        if len(content) > Config.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {Config.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        parsed_data = await resume_parser.parse_resume(content, file.filename)
        
        resume_id = await db.save_resume({
            "filename": file.filename,
            "uploaded_at": datetime.now().isoformat(),
            **parsed_data
        })
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Resume uploaded and parsed successfully",
                "resume_id": resume_id,
                "data": parsed_data
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save-job/")
async def save_job(job: JobDescription):
    try:
        job_data = job.dict()
        job_data["created_at"] = datetime.now().isoformat()
        
        job_id = await db.save_job(job_data)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Job description saved successfully",
                "job_id": job_id
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/match-resume/")
async def match_resume(request: MatchRequest):
    try:
        resume = await db.get_resume(request.resume_id)
        job = await db.get_job(request.job_id)
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        match_result = await resume_matcher.calculate_match(resume, job)
        
        await db.update_resume_score(request.resume_id, match_result)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Match calculated successfully",
                "match_score": match_result["match_score"],
                "justification": match_result["justification"],
                "matched_skills": match_result.get("matched_skills", []),
                "missing_skills": match_result.get("missing_skills", [])
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/shortlisted/")
async def get_shortlisted(min_score: int = 7, limit: int = 20):
    try:
        candidates = await db.get_shortlisted(min_score, limit)
        
        return JSONResponse(
            status_code=200,
            content={
                "count": len(candidates),
                "candidates": candidates
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/resumes/")
async def get_all_resumes():
    try:
        resumes = await db.get_all_resumes()
        return JSONResponse(
            status_code=200,
            content={"resumes": resumes}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/")
async def get_all_jobs():
    try:
        jobs = await db.get_all_jobs()
        return JSONResponse(
            status_code=200,
            content={"jobs": jobs}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/resume/{resume_id}")
async def delete_resume(resume_id: str):
    try:
        await db.delete_resume(resume_id)
        return JSONResponse(
            status_code=200,
            content={"message": "Resume deleted successfully"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=True
    )