import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [analysisId, setAnalysisId] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  const startAnalysis = async () => {
    try {
      setIsAnalyzing(true);
      setError(null);
      setAnalysisResult(null);
      
      const response = await axios.post(`${API}/analyze-video`, {
        video_url: "https://youtube.com/shorts/vSX3IRxGnNY"
      });
      
      setAnalysisId(response.data.analysis_id);
      
      // Start polling for results
      pollForResults(response.data.analysis_id);
      
    } catch (err) {
      console.error("Error starting analysis:", err);
      setError("Failed to start analysis. Please try again.");
      setIsAnalyzing(false);
    }
  };

  const pollForResults = async (id) => {
    const maxAttempts = 60; // 5 minutes max
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

  return (
    <div className="App">
      <div className="container">
        <header className="header">
          <h1>🏏 AthleteRise</h1>
          <p>AI-Powered Cricket Analytics</p>
        </header>

        <div className="demo-section">
          <h2>Cover Drive Analysis Demo</h2>
          <p className="demo-description">
            Analyze the cricket cover drive technique using AI-powered pose estimation and biomechanical analysis.
          </p>
          
          <div className="video-preview">
            <p><strong>Demo Video:</strong> Cricket Cover Drive</p>
            <p className="video-url">https://youtube.com/shorts/vSX3IRxGnNY</p>
          </div>

          <button 
            className={`analyze-btn ${isAnalyzing ? 'analyzing' : ''}`}
            onClick={startAnalysis}
            disabled={isAnalyzing}
          >
            {isAnalyzing ? (
              <>
                <div className="spinner"></div>
                Analyzing Cricket Technique...
              </>
            ) : (
              'Start AI Analysis'
            )}
          </button>

          {error && (
            <div className="error-message">
              <p>❌ {error}</p>
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

              <button className="download-btn" onClick={downloadResults}>
                📥 Download Full Report (JSON)
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;