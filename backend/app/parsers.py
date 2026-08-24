import PyPDF2
import docx
import io
import openai
import json
import re
from typing import Dict, Any
from .config import Config

openai.api_key = Config.OPENAI_API_KEY

class ResumeParser:
    async def parse_resume(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        try:
            text = self._extract_text(file_content, filename)
            
            if Config.OPENAI_API_KEY:
                return await self._parse_with_ai(text)
            else:
                return self._fallback_parse(text)
                
        except Exception as e:
            print(f"Error parsing resume: {e}")
            return {
                "name": None,
                "skills": [],
                "experience": "Error parsing",
                "education": "Error parsing",
                "raw_text": "Error extracting text",
                "filename": filename
            }
    
    def _extract_text(self, file_content: bytes, filename: str) -> str:
        if filename.lower().endswith('.pdf'):
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip() or "No text found"
        elif filename.lower().endswith('.docx'):
            doc_file = io.BytesIO(file_content)
            doc = docx.Document(doc_file)
            text = ""
            for paragraph in doc.paragraphs:
                if paragraph.text:
                    text += paragraph.text + "\n"
            return text.strip() or "No text found"
        else:
            raise ValueError("Unsupported file format")
    
    async def _parse_with_ai(self, text: str) -> Dict[str, Any]:
        prompt = f"""
        Extract from this resume:
        {text[:8000]}
        
        Return JSON only:
        {{
            "name": "Candidate name or null",
            "skills": ["skill1", "skill2"],
            "experience": "Summary with years",
            "education": "Summary with degrees"
        }}
        """
        
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Extract resume data. Return only JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            json_str = response.choices[0].message.content.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            
            return json.loads(json_str)
        except:
            return self._fallback_parse(text)
    
    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        common_skills = [
            'Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'C#', 'Ruby', 'Go',
            'React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask',
            'SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis',
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Git',
            'Machine Learning', 'AI', 'TensorFlow', 'PyTorch',
            'Agile', 'Scrum', 'JIRA', 'Project Management',
            'HTML', 'CSS', 'REST API', 'GraphQL', 'Linux'
        ]
        
        text_lower = text.lower()
        found_skills = []
        for skill in common_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        # Extract name
        name = None
        name_match = re.search(r'[Nn]ame:?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)', text)
        if name_match:
            name = name_match.group(1)
        else:
            lines = text.split('\n')[:5]
            for line in lines:
                line = line.strip()
                if line and len(line.split()) >= 2:
                    words = line.split()
                    if len(words) >= 2 and words[0][0].isupper() and words[1][0].isupper():
                        if not any(keyword in line.lower() for keyword in ['experience', 'education', 'skills']):
                            name = ' '.join(words[:2])
                            break
        experience = "No experience details found"
        exp_years = re.search(r'(\d+)\s*(?:years?|yrs?)\s*(?:of)?\s*experience', text_lower)
        if exp_years:
            experience = f"{exp_years.group(1)} years of experience"
        education = "No education details found"
        edu_patterns = [
            r'([Bb]achelor(?: of)? [A-Za-z\s]+)',
            r'([Mm]aster(?: of)? [A-Za-z\s]+)',
            r'([Pp]h\.?D(?:\.)? in [A-Za-z\s]+)',
        ]
        
        for pattern in edu_patterns:
            edu_match = re.search(pattern, text)
            if edu_match:
                education = edu_match.group(1).strip()
                break
        
        return {
            "name": name or "Candidate",
            "skills": found_skills[:30],
            "experience": experience,
            "education": education
        }