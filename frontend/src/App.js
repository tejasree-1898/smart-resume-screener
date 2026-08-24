import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [resumes, setResumes] = useState([]);
  const [jobDescription, setJobDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [jobTitle, setJobTitle] = useState('');
  const [jobSaved, setJobSaved] = useState(false);

  const API_BASE_URL = 'http://localhost:8000';
  axios.defaults.baseURL = API_BASE_URL;
  const prevJobDescriptionRef = useRef('');
  useEffect(() => {
    loadAllResumes();
  }, []);
  useEffect(() => {
    const hasJobDescription = jobDescription.trim().length > 0;
    const hasResumes = resumes.length > 0;
    const jobDescriptionChanged = jobDescription !== prevJobDescriptionRef.current;

    if (hasJobDescription && hasResumes && jobDescriptionChanged) {
      prevJobDescriptionRef.current = jobDescription;
      const hasAnyResumes = resumes.length > 0;
      if (hasAnyResumes) {
        rematchAllResumes();
      }
    }
  }, [jobDescription]);
  const loadAllResumes = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/resumes/');
      
      let resumesData = [];
      if (response.data && response.data.resumes) {
        resumesData = response.data.resumes;
      } else if (Array.isArray(response.data)) {
        resumesData = response.data;
      }
      
      const formattedResumes = resumesData.map(resume => ({
        id: resume.id || resume._id || Date.now().toString(),
        name: resume.name || 'Unnamed Candidate',
        skills: resume.skills || [],
        experience: resume.experience || '',
        education: resume.education || '',
        match_score: resume.match_score || null,
        justification: resume.justification || null,
        matched_skills: resume.matched_skills || [],
        missing_skills: resume.missing_skills || [],
        filename: resume.filename || ''
      }));
      
      setResumes(formattedResumes);
      
    } catch (error) {
      console.error('Error fetching resumes:', error);
    } finally {
      setLoading(false);
    }
  };
  const uploadResume = async (file) => {
    if (!file) {
      alert('Please select a file first');
      return;
    }

    const existingFile = resumes.find(r => r.filename === file.name);
    if (existingFile) {
      alert(`File "${file.name}" is already uploaded!`);
      document.getElementById('file-upload').value = '';
      setSelectedFile(null);
      return null;
    }

    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await axios.post('/upload-resume/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      const newResume = {
        id: response.data.resume_id || Date.now().toString(),
        name: response.data.data?.name || 'Unnamed Candidate',
        skills: response.data.data?.skills || [],
        experience: response.data.data?.experience || '',
        education: response.data.data?.education || '',
        filename: file.name,
        match_score: null,
        justification: null,
        matched_skills: [],
        missing_skills: []
      };
      
      setResumes(prev => [...prev, newResume]);
      
      if (jobDescription.trim()) {
        await matchSingleResume(newResume.id);
      }
      
      return newResume;
      
    } catch (error) {
      console.error('Upload error:', error);
      alert(`Failed to upload "${file.name}": ${error.response?.data?.detail || error.message}`);
      return null;
    }
  };
  const matchSingleResume = async (resumeId) => {
    if (!jobDescription.trim()) {
      return;
    }

    try {
      const jobResponse = await axios.post('/save-job/', {
        title: jobTitle || 'Untitled Position',
        description: jobDescription,
        requirements: jobDescription
      });
      
      const jobId = jobResponse.data.job_id;

      const matchResponse = await axios.post('/match-resume/', {
        resume_id: resumeId,
        job_id: jobId
      });

      setResumes(prev => prev.map(resume => 
        resume.id === resumeId 
          ? { 
              ...resume, 
              match_score: matchResponse.data.match_score,
              justification: matchResponse.data.justification,
              matched_skills: matchResponse.data.matched_skills || [],
              missing_skills: matchResponse.data.missing_skills || []
            }
          : resume
      ));

    } catch (error) {
      console.error('Match error:', error);
    }
  };
  const rematchAllResumes = async () => {
    if (!jobDescription.trim() || resumes.length === 0) {
      return;
    }

    setLoading(true);

    try {
      const jobResponse = await axios.post('/save-job/', {
        title: jobTitle || 'Untitled Position',
        description: jobDescription,
        requirements: jobDescription
      });
      
      const jobId = jobResponse.data.job_id;

      for (let resume of resumes) {
        try {
          const matchResponse = await axios.post('/match-resume/', {
            resume_id: resume.id,
            job_id: jobId
          });

          setResumes(prev => prev.map(r => 
            r.id === resume.id 
              ? { 
                  ...r, 
                  match_score: matchResponse.data.match_score,
                  justification: matchResponse.data.justification,
                  matched_skills: matchResponse.data.matched_skills || [],
                  missing_skills: matchResponse.data.missing_skills || []
                }
              : r
          ));
          
        } catch (error) {
          console.error(`Failed to match resume ${resume.id}:`, error);
        }
      }

    } catch (error) {
      console.error('Rematch all error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Match ALL unmatched resumes (for initial match)
  const matchAllResumes = async () => {
    if (!jobDescription.trim()) {
      return;
    }

    const unmatchedResumes = resumes.filter(r => !r.match_score || r.match_score === null);
    
    if (unmatchedResumes.length === 0) {
      return;
    }

    setLoading(true);

    try {
      const jobResponse = await axios.post('/save-job/', {
        title: jobTitle || 'Untitled Position',
        description: jobDescription,
        requirements: jobDescription
      });
      
      const jobId = jobResponse.data.job_id;

      for (let resume of unmatchedResumes) {
        try {
          const matchResponse = await axios.post('/match-resume/', {
            resume_id: resume.id,
            job_id: jobId
          });

          setResumes(prev => prev.map(r => 
            r.id === resume.id 
              ? { 
                  ...r, 
                  match_score: matchResponse.data.match_score,
                  justification: matchResponse.data.justification,
                  matched_skills: matchResponse.data.matched_skills || [],
                  missing_skills: matchResponse.data.missing_skills || []
                }
              : r
          ));
          
        } catch (error) {
          console.error(`Failed to match resume ${resume.id}:`, error);
        }
      }

    } catch (error) {
      console.error('Match all error:', error);
    } finally {
      setLoading(false);
    }
  };
  const saveJobDescription = async () => {
    if (!jobDescription.trim()) {
      alert('Please paste a job description first.');
      return;
    }

    setLoading(true);
    try {
      await axios.post('/save-job/', {
        title: jobTitle || 'Untitled Position',
        description: jobDescription,
        requirements: jobDescription
      });
      
      setJobSaved(true);
      
      prevJobDescriptionRef.current = jobDescription;
      
      alert('Job description saved! Rematching all resumes...');
      
      await rematchAllResumes();
      
    } catch (error) {
      console.error('Save job error:', error);
      alert('Failed to save job description: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };
  const handleFileChange = (event) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
      const validFiles = [];
      
      for (let file of files) {
        if (validTypes.includes(file.type)) {
          validFiles.push(file);
        }
      }
      
      if (validFiles.length > 0) {
        const existingFilenames = resumes.map(r => r.filename);
        const uniqueFiles = validFiles.filter(f => !existingFilenames.includes(f.name));
        
        if (uniqueFiles.length === 0) {
          alert('All selected files are already uploaded!');
          setSelectedFile(null);
          return;
        }
        
        const dataTransfer = new DataTransfer();
        uniqueFiles.forEach(f => dataTransfer.items.add(f));
        event.target.files = dataTransfer.files;
        setSelectedFile(dataTransfer.files);
      } else {
        alert('Please upload only PDF or DOCX files.');
        setSelectedFile(null);
      }
    } else {
      setSelectedFile(null);
    }
  };
  const handleUpload = async () => {
    if (!selectedFile || selectedFile.length === 0) {
      alert('Please select at least one file');
      return;
    }
    
    setLoading(true);
    let successCount = 0;
    
    for (let file of selectedFile) {
      const result = await uploadResume(file);
      if (result) successCount++;
    }
    
    setLoading(false);
    setSelectedFile(null);
    document.getElementById('file-upload').value = '';
    
    if (successCount > 0) {
      alert(`Successfully uploaded ${successCount} resume(s)!`);
    }
  };

  // Get shortlisted candidates
  const getShortlisted = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/shortlisted/?min_score=7');
      
      let candidates = response.data?.candidates || [];
      
      const formattedCandidates = candidates.map(candidate => ({
        id: candidate.id || candidate._id || Date.now().toString(),
        name: candidate.name || 'Unnamed Candidate',
        skills: candidate.skills || [],
        experience: candidate.experience || '',
        education: candidate.education || '',
        match_score: candidate.match_score || 0,
        justification: candidate.justification || 'No justification provided',
        matched_skills: candidate.matched_skills || [],
        missing_skills: candidate.missing_skills || [],
        filename: candidate.filename || ''
      }));
      
      setResumes(formattedCandidates);
      
      if (formattedCandidates.length === 0) {
        alert('No shortlisted candidates found (score >= 7)');
      } else {
        alert(`Found ${formattedCandidates.length} shortlisted candidates!`);
      }
      
    } catch (error) {
      console.error('Error fetching shortlisted:', error);
      alert('Failed to fetch shortlisted candidates');
    } finally {
      setLoading(false);
    }
  };
  const deleteResume = async (resumeId) => {
    if (!window.confirm('Delete this resume? This action cannot be undone!')) {
      return;
    }

    setLoading(true);
    try {
      const response = await axios.delete(`/resume/${resumeId}`);
      
      if (response.status === 200) {
        setResumes(resumes.filter(r => r.id !== resumeId));
        alert('Resume deleted successfully from database!');
      }
    } catch (error) {
      console.error('Delete error:', error);
      alert('Failed to delete resume: ' + (error.response?.data?.detail || error.message));
      await loadAllResumes();
    } finally {
      setLoading(false);
    }
  };
  const CandidateCard = ({ resume }) => (
    <div className="candidate-card">
      <div className="card-header">
        <h3>{resume.name || `Candidate ${resume.id}`}</h3>
        <button 
          className="delete-btn" 
          onClick={() => deleteResume(resume.id)}
          disabled={loading}
          title="Delete this resume"
        >
          X
        </button>
      </div>
      {resume.filename && (
        <div className="filename">
          <small>{resume.filename}</small>
        </div>
      )}
      {resume.match_score !== null && resume.match_score !== undefined ? (
        <>
          <div className="match-score">
            <span className={`score ${resume.match_score >= 7 ? 'high' : resume.match_score >= 5 ? 'medium' : 'low'}`}>
              Match Score: {resume.match_score}/10
            </span>
          </div>
          {resume.justification && (
            <div className="justification">
              <strong>Justification:</strong> {resume.justification}
            </div>
          )}
          {resume.matched_skills && resume.matched_skills.length > 0 && (
            <div className="matched-skills">
              <strong>Matched Skills:</strong> {resume.matched_skills.join(', ')}
            </div>
          )}
          {resume.missing_skills && resume.missing_skills.length > 0 && (
            <div className="missing-skills">
              <strong>Missing Skills:</strong> {resume.missing_skills.join(', ')}
            </div>
          )}
        </>
      ) : (
        <div className="pending-match">
          <span className="pending-badge">Waiting for job description...</span>
        </div>
      )}
      {resume.skills && resume.skills.length > 0 && (
        <div className="skills">
          <strong>Skills:</strong> {resume.skills.join(', ')}
        </div>
      )}
      {resume.experience && resume.experience !== 'No experience details found' && resume.experience !== 'Error parsing' && (
        <div className="experience">
          <strong>Experience:</strong> {resume.experience}
        </div>
      )}
      {resume.education && resume.education !== 'No education details found' && resume.education !== 'Error parsing' && (
        <div className="education">
          <strong>Education:</strong> {resume.education}
        </div>
      )}
    </div>
  );

  return (
    <div className="App">
      <header className="app-header">
        <h1>Smart Resume Screener</h1>
        <p>Upload resumes and they will be automatically matched with the job description</p>
      </header>

      <div className="container">
        <div className="left-panel">
          {/* Job Description Section */}
          <div className="section">
            <h2>Job Description</h2>
            <input
              type="text"
              placeholder="Job Title"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              className="job-title-input"
            />
            <textarea
              placeholder="Paste job description here... (Resumes will auto-rematch when you edit)"
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              rows="6"
              className="job-description-input"
            />
            <button 
              onClick={saveJobDescription}
              className="save-job-btn"
              disabled={loading || !jobDescription.trim()}
            >
              {loading ? 'Saving...' : 'Save & Match All'}
            </button>
            {jobSaved && (
              <div className="job-saved-badge">
                Job saved! Edits will auto-rematch all resumes.
              </div>
            )}
          </div>

          {/* Upload Resume Section */}
          <div className="section">
            <h2>Upload Resume(s)</h2>
            <div className="upload-area">
              <input
                type="file"
                accept=".pdf,.docx"
                onChange={handleFileChange}
                className="file-input"
                id="file-upload"
                multiple
              />
              <label htmlFor="file-upload" className="file-label">
                {selectedFile ? `${selectedFile.length} file(s) selected` : 'Choose PDF or DOCX files (multiple allowed)'}
              </label>
              <button 
                onClick={handleUpload}
                className="upload-btn"
                disabled={loading || !selectedFile}
              >
                {loading ? 'Uploading...' : 'Upload All Resumes'}
              </button>
              {selectedFile && selectedFile.length > 0 && (
                <div className="selected-files">
                  <strong>Selected files:</strong>
                  <ul>
                    {Array.from(selectedFile).map((file, index) => (
                      <li key={index}>{file.name}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="section">
            <button 
              onClick={getShortlisted} 
              className="shortlist-btn" 
              disabled={loading}
            >
              {loading ? 'Loading...' : 'Get Shortlisted Candidates'}
            </button>
          </div>
        </div>

        <div className="right-panel">
          <h2>Candidates ({resumes.length})</h2>
          {loading && (
            <div className="loading-spinner">
              Processing...
            </div>
          )}
          <div className="candidates-list">
            {resumes.length === 0 ? (
              <p className="no-candidates">
                No resumes uploaded yet. 
                <br />
                <small>Upload a resume and it will be automatically matched!</small>
              </p>
            ) : (
              resumes.map((resume, index) => {
                const key = resume.id || resume._id || `resume-${index}`;
                return <CandidateCard key={key} resume={resume} />;
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
