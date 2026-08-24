# app/matcher.py
import openai
import json
import re
from typing import Dict, Any, List
from .config import Config

openai.api_key = Config.OPENAI_API_KEY

class ResumeMatcher:
    async def calculate_match(self, resume: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
        if not Config.OPENAI_API_KEY:
            print("No OpenAI API key found. Using fallback matching.")
            return self._fallback_match(resume, job)
        resume_skills = ', '.join(resume.get('skills', []))
        resume_experience = resume.get('experience', 'Not specified')
        resume_education = resume.get('education', 'Not specified')
        
        job_title = job.get('title', 'Unknown')
        job_description = job.get('description', '')
        job_requirements = job.get('requirements', job_description)
        
        prompt = f"""
        You are an expert HR recruiter. Compare the following resume with the job description and provide a detailed match analysis.
        
        JOB DESCRIPTION:
        Title: {job_title}
        Description: {job_description[:3000]}
        Requirements: {job_requirements[:1500]}
        
        RESUME:
        Skills: {resume_skills[:1000]}
        Experience: {resume_experience[:1000]}
        Education: {resume_education[:500]}
        
        Analyze the match and provide response in valid JSON format:
        {{
            "match_score": <score between 1-10>,
            "justification": "<detailed explanation of why this score was given>",
            "matched_skills": ["list", "of", "skills", "that", "match"],
            "missing_skills": ["list", "of", "skills", "that", "are", "missing"]
        }}
        
        Scoring guidelines:
        - 9-10: Exceptional match, candidate exceeds requirements
        - 7-8: Strong match, candidate meets most requirements
        - 5-6: Moderate match, candidate meets some requirements
        - 3-4: Weak match, candidate meets few requirements
        - 1-2: Poor match, candidate doesn't meet requirements
        
        Return ONLY the JSON object, no additional text.
        """
        
        try:
            response = await self._call_openai(prompt)
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            
            result = json.loads(json_str.strip())
            result.setdefault("match_score", 5)
            result.setdefault("justification", "Match analysis completed")
            result.setdefault("matched_skills", [])
            result.setdefault("missing_skills", [])
            
            return result
            
        except Exception as e:
            print(f"Match calculation error: {e}")
            return self._fallback_match(resume, job)
    
    async def _call_openai(self, prompt: str) -> str:
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert HR recruiter and resume screener."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {e}")
            raise e
    
    def _is_valid_skill(self, skill: str) -> bool:
        skill = skill.strip()
        
        if len(skill) <= 1:
            return False
        common_words = [
            'the', 'and', 'for', 'with', 'from', 'have', 'this', 'that',
            'are', 'all', 'but', 'not', 'you', 'we', 'our', 'will', 'can',
            'should', 'would', 'could', 'may', 'might', 'must', 'shall',
            'your', 'our', 'their', 'them', 'they', 'what', 'when', 'where',
            'which', 'who', 'whom', 'whose', 'etc', 'etc.', 'including',
            'including:', 'such', 'such as', 'e.g.', 'i.e.', 'etc.',
            'like', 'also', 'well', 'very', 'too', 'much', 'more', 'most',
            'some', 'any', 'no', 'every', 'each', 'either', 'neither',
            'both', 'several', 'many', 'few', 'lot', 'lots', 'enough'
        ]
        
        if skill.lower() in common_words:
            return False
        if re.match(r'^\d+$', skill):
            return False
        
        if re.match(r'^[^a-zA-Z]+$', skill):
            return False
        
        if len(skill) < 2:
            return False
        
        return True
    
    def _extract_skills_from_job(self, job: Dict[str, Any]) -> List[str]:
        job_text = job.get('description', '') + ' ' + job.get('requirements', '')
        job_text_lower = job_text.lower()
        
        common_skills = [
            'Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'C#', 'Ruby', 'Go', 'Rust',
            'Swift', 'Kotlin', 'PHP', 'Perl', 'Scala', 'R', 'MATLAB', 'Dart', 'Groovy',
            'Elixir', 'Clojure', 'Haskell', 'Erlang', 'Julia', 'Lua', 'VBA', 'Assembly',
            
            'React', 'Angular', 'Vue.js', 'Next.js', 'Nuxt.js', 'Svelte', 'Redux',
            'HTML', 'CSS', 'SASS', 'LESS', 'Tailwind', 'Bootstrap', 'Material-UI',
            'jQuery', 'Backbone', 'Ember', 'Webpack', 'Babel', 'Vite',
            
            'Node.js', 'Django', 'Flask', 'Spring Boot', 'Express.js', 'Laravel',
            'Ruby on Rails', 'ASP.NET', 'FastAPI', 'GraphQL', 'REST API',
            'Spring', 'Hibernate', 'JPA', 'Maven', 'Gradle',
            
            'SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Cassandra', 'Elasticsearch',
            'DynamoDB', 'Oracle', 'SQLite', 'Firebase', 'Neo4j', 'InfluxDB',
            
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'Git', 'CI/CD',
            'Terraform', 'Ansible', 'Linux', 'Shell Scripting', 'Bash', 'GitHub Actions',
            'GitLab CI', 'CircleCI', 'Travis CI', 'Prometheus', 'Grafana', 'ELK Stack',
            
            'Machine Learning', 'AI', 'Deep Learning', 'NLP', 'Computer Vision',
            'TensorFlow', 'PyTorch', 'Pandas', 'NumPy', 'Scikit-learn', 'Keras',
            'Data Science', 'Analytics', 'Tableau', 'Power BI', 'Excel',
            'Hadoop', 'Spark', 'Hive', 'Kafka', 'Airflow',
            
            'Agile', 'Scrum', 'Kanban', 'Waterfall', 'JIRA', 'Confluence', 
            'Project Management', 'Leadership', 'Communication', 'Problem Solving',
            'Critical Thinking', 'Teamwork', 'Mentoring', 'SAFe', 'Lean', 'Six Sigma',
            'PMBOK', 'PRINCE2', 'ITIL', 'COBIT', 'DevOps',
            
            'Testing', 'Jest', 'PyTest', 'Unit Testing', 'Integration Testing',
            'Selenium', 'Cucumber', 'TestNG', 'JUnit', 'Mocha', 'Chai',
            'QA', 'Quality Assurance', 'Test Automation', 'BDD', 'TDD',
            'Cypress', 'Playwright', 'Puppeteer',
            
            'Security', 'DevSecOps', 'SRE', 'Penetration Testing', 'Vulnerability',
            'Cybersecurity', 'Information Security', 'Network Security', 'Firewall',
            'Encryption', 'Authentication', 'Authorization', 'OAuth', 'JWT',
            
            'Microservices', 'Serverless', 'Monolithic', 'Event-Driven', 'SOA',
            'Design Patterns', 'SOLID', 'Clean Code', 'Refactoring', 'Code Review',
            
            'EC2', 'S3', 'RDS', 'Lambda', 'CloudFront', 'Route53', 'VPC',
            'Azure Functions', 'Azure DevOps', 'GCP', 'Cloud Run', 'BigQuery',
            
            'Blockchain', 'IoT', 'AR', 'VR', 'UX', 'UI', 'Figma', 'Sketch',
            'WordPress', 'Shopify', 'Salesforce', 'SAP', 'Oracle',
            'Web3', 'Solidity', 'Ethereum', 'Hyperledger',
            'System Design', 'Distributed Systems', 'High Availability'
        ]
        
        # Find all skills mentioned in the job description
        found_skills = []
        for skill in common_skills:
            if skill.lower() in job_text_lower:
                found_skills.append(skill.lower())
        
        # Also extract skills using regex patterns
        skill_patterns = [
            r'required:?\s*([^.]+)',
            r'must have:?\s*([^.]+)',
            r'requirements?:?\s*([^.]+)',
            r'skills:?\s*([^.]+)',
            r'expert in:?\s*([^.]+)',
            r'experience with:?\s*([^.]+)',
            r'knowledge of:?\s*([^.]+)',
            r'familiar with:?\s*([^.]+)',
            r'proficient in:?\s*([^.]+)',
            r'qualifications:?\s*([^.]+)',
            r'nice to have:?\s*([^.]+)',
            r'bonus:?\s*([^.]+)',
            r'preferred:?\s*([^.]+)'
        ]
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, job_text_lower, re.IGNORECASE)
            for match in matches:
                parts = re.split(r'[,;\n•\-]', match)
                for part in parts:
                    part = part.strip()
                    if part and self._is_valid_skill(part):
                        for skill in common_skills:
                            skill_lower = skill.lower()
                            if skill_lower in part or part in skill_lower:
                                if skill_lower not in found_skills:
                                    found_skills.append(skill_lower)
        found_skills = [s for s in found_skills if self._is_valid_skill(s)]
        return list(set(found_skills))
    
    def _fallback_match(self, resume: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
        resume_skills = [s.lower().strip() for s in resume.get('skills', []) if self._is_valid_skill(s)]
        
        required_skills = self._extract_skills_from_job(job)
        
        if not required_skills:
            job_text = job.get('description', '').lower() + ' ' + job.get('requirements', '').lower()
            matched = []
            missing = []
            for skill in resume_skills:
                if skill in job_text:
                    matched.append(skill)
                else:
                    missing.append(skill)
            
            if not resume_skills:
                score = 5
            else:
                match_percentage = len(matched) / len(resume_skills)
                score = max(1, min(10, int(match_percentage * 10)))
        else:
            matched = []
            missing = []
            for skill in required_skills:
                skill_lower = skill.lower()
                found = False
                
                for r_skill in resume_skills:
                    r_skill_lower = r_skill.lower()
                    if skill_lower == r_skill_lower or skill_lower in r_skill_lower or r_skill_lower in skill_lower:
                        matched.append(skill_lower)
                        found = True
                        break
                
                if not found:
                    missing.append(skill_lower)
            if len(required_skills) == 0:
                score = 5
            else:
                match_percentage = len(matched) / len(required_skills)
                score = max(1, min(10, int(match_percentage * 10)))
        
        total_required = len(required_skills) if required_skills else len(resume_skills)
        
        if score >= 8:
            justification = f"Strong match! Found {len(matched)} required skills out of {total_required}."
        elif score >= 6:
            justification = f"Good match. Found {len(matched)} required skills out of {total_required}."
        elif score >= 4:
            justification = f"Moderate match. Found {len(matched)} required skills out of {total_required}."
        else:
            justification = f"Weak match. Only found {len(matched)} required skills out of {total_required}."
        
        if missing:
            justification += f" Missing skills: {', '.join(missing[:5])}"
        if len(missing) > 5:
            justification += f" and {len(missing) - 5} more."
        
        return {
            "match_score": score,
            "justification": justification,
            "matched_skills": matched[:10],
            "missing_skills": missing[:10]
        }