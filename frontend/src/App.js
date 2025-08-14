import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [analysisId, setAnalysisId] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef(null);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('video/')) {
        setError("Please select a video file");
        return;
      }
      
      // Check file size (limit to 100MB)
      if (file.size > 100 * 1024 * 1024) {
        setError("File size must be less than 100MB");
        return;
      }
      
      setSelectedFile(file);
      setError(null);
    }
  };

  const uploadAndAnalyze = async () => {
    if (!selectedFile) {
      setError("Please select a video file first");
      return;
    }

    try {
      setIsAnalyzing(true);
      setError(null);
      setAnalysisResult(null);
      setUploadProgress(0);
      
      const formData = new FormData();
      formData.append('file', selectedFile);
      
      const response = await axios.post(`${API}/upload-video`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        }
      });
      
      setAnalysisId(response.data.analysis_id);
      setUploadProgress(100);
      
      // Start polling for results
      pollForResults(response.data.analysis_id);
      
    } catch (err) {
      console.error("Error uploading video:", err);
      setError(err.response?.data?.detail || "Failed to upload video. Please try again.");
      setIsAnalyzing(false);
      setUploadProgress(0);
    }
  };

  const pollForResults = async (id) => {
    const maxAttempts = 120; // 10 minutes max
    let attempts = 0;
    
    const poll = async () => {
      try {
        attempts++;
        const response = await axios.get(`${API}/analysis/${id}`);
        const result = response.data;
        
        if (result.status === "completed") {
          setAnalysisResult(result);
          setIsAnalyzing(false);
        } else if (result.status === "failed") {
          setError(result.error_message || "Analysis failed");
          setIsAnalyzing(false);
        } else if (attempts >= maxAttempts) {
          setError("Analysis timed out. Please try again.");
          setIsAnalyzing(false);
        } else {
          // Continue polling
          setTimeout(poll, 5000); // Poll every 5 seconds
        }
      } catch (err) {
        console.error("Error polling results:", err);
        if (attempts >= maxAttempts) {
          setError("Failed to get analysis results");
          setIsAnalyzing(false);
        } else {
          setTimeout(poll, 5000);
        }
      }
    };
    
    // Start polling after 2 seconds
    setTimeout(poll, 2000);
  };

  const downloadResults = () => {
    if (analysisResult) {
      const dataStr = JSON.stringify(analysisResult, null, 2);
      const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
      
      const exportFileDefaultName = `cricket_analysis_${analysisId}.json`;
      
      const linkElement = document.createElement('a');
      linkElement.setAttribute('href', dataUri);
      linkElement.setAttribute('download', exportFileDefaultName);
      linkElement.click();
    }
  };

  const resetAnalysis = () => {
    setAnalysisId(null);
    setAnalysisResult(null);
    setIsAnalyzing(false);
    setError(null);
    setSelectedFile(null);
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="App">
      <div className="container">
        <header className="header">
          <h1>🏏 AthleteRise</h1>
          <p>AI-Powered Cricket Analytics</p>
        </header>

        <div className="demo-section">
          <h2>Cover Drive Analysis</h2>
          <p className="demo-description">
            Upload your cricket video to analyze cover drive technique using AI-powered pose estimation and biomechanical analysis.
          </p>
          
          {!analysisResult && (
            <div className="upload-section">
              <div className="file-upload-area" onClick={() => fileInputRef.current?.click()}>
                <input
                  type="file"
                  ref={fileInputRef}
                  accept="video/*"
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                />
                
                {selectedFile ? (
                  <div className="file-selected">
                    <div className="file-icon">🎥</div>
                    <div className="file-info">
                      <p className="file-name">{selectedFile.name}</p>
                      <p className="file-size">{(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                    </div>
                  </div>
                ) : (
                  <div className="file-placeholder">
                    <div className="upload-icon">📁</div>
                    <p>Click to select cricket video</p>
                    <p className="file-hint">Supports MP4, AVI, MOV (max 100MB)</p>
                  </div>
                )}
              </div>

              {selectedFile && (
                <button 
                  className={`analyze-btn ${isAnalyzing ? 'analyzing' : ''}`}
                  onClick={uploadAndAnalyze}
                  disabled={isAnalyzing}
                >
                  {isAnalyzing ? (
                    <>
                      <div className="spinner"></div>
                      {uploadProgress < 100 ? `Uploading... ${uploadProgress}%` : 'Analyzing Cricket Technique...'}
                    </>
                  ) : (
                    'Start AI Analysis'
                  )}
                </button>
              )}

              {uploadProgress > 0 && uploadProgress < 100 && (
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${uploadProgress}%` }}></div>
                </div>
              )}
            </div>
          )}

          {error && (
            <div className="error-message">
              <p>❌ {error}</p>
              <button className="retry-btn" onClick={resetAnalysis}>Try Again</button>
            </div>
          )}

          {analysisResult && (
            <div className="results-section">
              <h3>🎯 Analysis Complete!</h3>
              
              <div className="scores-grid">
                <div className="score-card">
                  <h4>Footwork</h4>
                  <div className="score">{analysisResult.scores?.footwork || 'N/A'}/10</div>
                </div>
                <div className="score-card">
                  <h4>Head Position</h4>
                  <div className="score">{analysisResult.scores?.head_position || 'N/A'}/10</div>
                </div>
                <div className="score-card">
                  <h4>Swing Control</h4>
                  <div className="score">{analysisResult.scores?.swing_control || 'N/A'}/10</div>
                </div>
                <div className="score-card">
                  <h4>Balance</h4>
                  <div className="score">{analysisResult.scores?.balance || 'N/A'}/10</div>
                </div>
                <div className="score-card">
                  <h4>Follow-through</h4>
                  <div className="score">{analysisResult.scores?.follow_through || 'N/A'}/10</div>
                </div>
              </div>

              <div className="feedback-section">
                <h4>💡 Actionable Feedback</h4>
                {analysisResult.feedback && Object.entries(analysisResult.feedback).map(([category, feedback]) => (
                  <div key={category} className="feedback-item">
                    <strong>{category.replace('_', ' ').toUpperCase()}:</strong>
                    <ul>
                      {Array.isArray(feedback) ? feedback.map((item, index) => (
                        <li key={index}>{item}</li>
                      )) : (
                        <li>{feedback}</li>
                      )}
                    </ul>
                  </div>
                ))}
              </div>

              {analysisResult.metrics_summary && (
                <div className="metrics-section">
                  <h4>📊 Biomechanical Metrics</h4>
                  <div className="metrics-grid">
                    {Object.entries(analysisResult.metrics_summary).map(([metric, value]) => (
                      <div key={metric} className="metric-item">
                        <span className="metric-name">{metric.replace('_', ' ').toUpperCase()}:</span>
                        <span className="metric-value">{typeof value === 'number' ? value.toFixed(1) : value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {analysisResult.video_info && (
                <div className="video-info">
                  <h4>📹 Video Analysis Info</h4>
                  <p>Duration: {analysisResult.video_info.duration_seconds?.toFixed(1)}s | 
                     Frames Analyzed: {analysisResult.video_info.frames_with_pose}/{analysisResult.video_info.frames_total}</p>
                </div>
              )}

              <div className="action-buttons">
                <button className="download-btn" onClick={downloadResults}>
                  📥 Download Full Report (JSON)
                </button>
                <button className="new-analysis-btn" onClick={resetAnalysis}>
                  🔄 Analyze Another Video
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;