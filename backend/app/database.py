import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from .config import Config

class Database:
    def __init__(self):
        self.db_path = Config.SQLITE_DB_PATH
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create resumes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                name TEXT,
                skills TEXT,
                experience TEXT,
                education TEXT,
                raw_text TEXT,
                uploaded_at TEXT,
                match_score INTEGER DEFAULT NULL,
                justification TEXT,
                matched_skills TEXT,
                missing_skills TEXT
            )
        ''')
        
        # Create jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                requirements TEXT,
                created_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ SQLite Database initialized!")
    
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
    
    async def save_resume(self, resume_data: Dict[str, Any]) -> str:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO resumes (
                filename, name, skills, experience, education, 
                raw_text, uploaded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            resume_data.get('filename', ''),
            resume_data.get('name', ''),
            json.dumps(resume_data.get('skills', [])),
            resume_data.get('experience', ''),
            resume_data.get('education', ''),
            resume_data.get('raw_text', ''),
            resume_data.get('uploaded_at', datetime.now().isoformat())
        ))
        
        conn.commit()
        resume_id = cursor.lastrowid
        conn.close()
        return str(resume_id)
    
    async def save_job(self, job_data: Dict[str, Any]) -> str:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO jobs (title, description, requirements, created_at)
            VALUES (?, ?, ?, ?)
        ''', (
            job_data.get('title', ''),
            job_data.get('description', ''),
            job_data.get('requirements', ''),
            job_data.get('created_at', datetime.now().isoformat())
        ))
        
        conn.commit()
        job_id = cursor.lastrowid
        conn.close()
        return str(job_id)
    
    async def get_resume(self, resume_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM resumes WHERE id = ?', (int(resume_id),))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": str(row[0]),
                "filename": row[1],
                "name": row[2],
                "skills": json.loads(row[3]) if row[3] else [],
                "experience": row[4],
                "education": row[5],
                "raw_text": row[6],
                "uploaded_at": row[7],
                "match_score": row[8],
                "justification": row[9],
                "matched_skills": json.loads(row[10]) if row[10] else [],
                "missing_skills": json.loads(row[11]) if row[11] else []
            }
        return None
    
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM jobs WHERE id = ?', (int(job_id),))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": str(row[0]),
                "title": row[1],
                "description": row[2],
                "requirements": row[3],
                "created_at": row[4]
            }
        return None
    
    async def update_resume_score(self, resume_id: str, match_result: Dict[str, Any]):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE resumes 
            SET match_score = ?, justification = ?, matched_skills = ?, missing_skills = ?
            WHERE id = ?
        ''', (
            match_result.get("match_score", 0),
            match_result.get("justification", ""),
            json.dumps(match_result.get("matched_skills", [])),
            json.dumps(match_result.get("missing_skills", [])),
            int(resume_id)
        ))
        conn.commit()
        conn.close()
    
    async def get_shortlisted(self, min_score: int = 7, limit: int = 20) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM resumes WHERE match_score >= ? 
            ORDER BY match_score DESC LIMIT ?
        ''', (min_score, limit))
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            "id": str(row[0]),
            "filename": row[1],
            "name": row[2],
            "skills": json.loads(row[3]) if row[3] else [],
            "experience": row[4],
            "education": row[5],
            "uploaded_at": row[7],
            "match_score": row[8],
            "justification": row[9],
            "matched_skills": json.loads(row[10]) if row[10] else [],
            "missing_skills": json.loads(row[11]) if row[11] else []
        } for row in rows]
    
    async def get_all_resumes(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM resumes ORDER BY uploaded_at DESC')
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            "id": str(row[0]),
            "filename": row[1],
            "name": row[2],
            "skills": json.loads(row[3]) if row[3] else [],
            "experience": row[4],
            "education": row[5],
            "uploaded_at": row[7],
            "match_score": row[8]
        } for row in rows]
    
    async def delete_resume(self, resume_id: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM resumes WHERE id = ?', (int(resume_id),))
        conn.commit()
        conn.close()