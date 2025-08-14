# Here are your Instructions
# 🏏 CricBuddy - AI-Powered Cricket Analytics

An intelligent cricket analysis system that uses computer vision and biomechanical analysis to evaluate cricket cover drive techniques in real-time.

Sample video used - YouTube Short: https://youtube.com/shorts/vSX3IRxGnNY

## 🎯 Features

### 🤖 AI-Powered Analysis
- **Real-time pose estimation** using MediaPipe
- **Frame-by-frame video processing** for comprehensive analysis
- **Biomechanical metrics calculation** with 4 key measurements
- **Machine learning-based technique evaluation**

### 📊 Comprehensive Scoring System
- **5-Category Analysis**: Footwork, Head Position, Swing Control, Balance, Follow-through
- **1-10 Scoring Scale** with detailed breakdowns
- **Actionable Feedback** for technique improvement
- **Professional biomechanical metrics** display

### 💻 Modern Web Interface
- **Drag-and-drop video upload** with progress tracking
- **Real-time analysis status** polling
- **Responsive design** for desktop and mobile
- **Professional sports-themed UI** with gradient designs
- **JSON report downloads** for detailed analysis

### 🎬 Video Processing
- **Multiple format support**: MP4, AVI, MOV
- **File size validation** (up to 100MB)
- **Background processing** with status updates
- **Error handling** and validation

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **MediaPipe** - Google's pose estimation library
- **OpenCV** - Computer vision and video processing
- **MongoDB** - Document database for analysis storage
- **Motor** - Async MongoDB driver
- **NumPy & SciPy** - Mathematical computations

### Frontend
- **React 19** - Modern JavaScript framework
- **Axios** - HTTP client for API calls
- **CSS3** - Advanced styling with gradients and animations
- **Responsive Design** - Mobile-first approach

### Infrastructure
- **Docker** - Containerized deployment
- **Supervisor** - Process management
- **CORS** - Cross-origin resource sharing
- **File Upload** - Multipart form handling

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- **MongoDB**
- **Docker** (optional)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/cricbuddy.git
cd cricbuddy
```

2. **Backend Setup**
```bash
cd backend
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
MONGO_URL="mongodb://localhost:27017"
DB_NAME="cricbuddy_db"
CORS_ORIGINS="*"
EOF
```

3. **Frontend Setup**
```bash
cd frontend
yarn install

# Create .env file
cat > .env << EOF
REACT_APP_BACKEND_URL=http://localhost:8001
EOF
```

4. **Start MongoDB**
```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or install MongoDB locally
# Follow instructions at: https://docs.mongodb.com/manual/installation/
```

5. **Run the Application**

Backend:
```bash
cd backend
python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

Frontend:
```bash
cd frontend
yarn start
```

Visit `http://localhost:3000` to access CricBuddy!

## 📖 Usage Guide

### 1. Upload Cricket Video
- Click on the upload area or drag-and-drop your cricket video
- Supported formats: MP4, AVI, MOV (max 100MB)
- Watch the upload progress bar

### 2. AI Analysis Process
- Click "Start AI Analysis" button
- The system processes your video frame-by-frame
- Real-time status updates show analysis progress
- Typical processing time: 30-120 seconds depending on video length

### 3. View Results
- **Scores**: 1-10 ratings across 5 technique categories
- **Feedback**: Actionable advice for improvement
- **Metrics**: Detailed biomechanical measurements
- **Video Info**: Analysis statistics and processing details

### 4. Download & Reset
- Download complete analysis as JSON report
- Use "Analyze Another Video" to start over

## 🔧 API Documentation

### Core Endpoints

#### Upload Video
```http
POST /api/upload-video
Content-Type: multipart/form-data

Body: file (video file)
```

#### Get Analysis Status
```http
GET /api/analysis/{analysis_id}
```

#### List All Analyses
```http
GET /api/analysis
```

### Response Format
```json
{
  "analysis_id": "uuid",
  "status": "completed",
  "scores": {
    "footwork": 8,
    "head_position": 7,
    "swing_control": 9,
    "balance": 8,
    "follow_through": 7
  },
  "feedback": {
    "footwork": ["Good foot positioning towards target"],
    "head_position": ["Keep head over front knee"]
  },
  "metrics_summary": {
    "elbow_angle": 115.5,
    "spine_lean": 22.3,
    "head_alignment": 0.15,
    "foot_angle": 28.7
  }
}
```

## 📁 Project Structure

```
cricbuddy/
├── backend/
│   ├── server.py                 # FastAPI application
│   ├── requirements.txt          # Python dependencies
│   ├── .env                      # Environment variables
│   ├── output/                   # Processed files storage
│   └── video_analysis/
│       ├── __init__.py
│       └── cricket_analyzer.py   # Core analysis engine
├── frontend/
│   ├── public/                   # Static assets
│   ├── src/
│   │   ├── App.js               # Main React component
│   │   ├── App.css              # Styling
│   │   ├── index.js             # Entry point
│   │   └── index.css            # Global styles
│   ├── package.json             # Node dependencies
│   └── .env                     # Frontend environment
├── tests/                       # Test files
├── README.md                    # This file
└── docker-compose.yml           # Docker setup (optional)
```

## 🧪 Biomechanical Analysis Details

### Metrics Calculated
1. **Front Elbow Angle**: Shoulder-elbow-wrist angle during swing
2. **Spine Lean**: Hip-shoulder line deviation from vertical
3. **Head-over-Knee Alignment**: Horizontal distance measurement
4. **Front Foot Direction**: Foot angle relative to pitch direction

### Evaluation Categories
- **Footwork** (1-10): Stance, balance, foot positioning
- **Head Position** (1-10): Head stability and alignment
- **Swing Control** (1-10): Elbow position and swing path
- **Balance** (1-10): Body stability throughout the shot
- **Follow-through** (1-10): Shot completion and technique consistency

## 🧪 Testing

### Run Backend Tests
```bash
cd backend
python -m pytest tests/ -v
```

### Run Frontend Tests
```bash
cd frontend
yarn test
```

### Manual Testing
1. Upload various cricket video formats
2. Test with different video qualities and lengths
3. Verify analysis accuracy with known good/bad techniques
4. Check responsive design on different devices

## 🚀 Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build individual containers
docker build -t cricbuddy-backend ./backend
docker build -t cricbuddy-frontend ./frontend
```

### Production Environment Variables
```bash
# Backend .env
MONGO_URL="mongodb://your-mongo-host:27017"
DB_NAME="cricbuddy_production"
CORS_ORIGINS="https://yourdomain.com"

# Frontend .env
REACT_APP_BACKEND_URL=https://api.yourdomain.com
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 for Python code
- Use ESLint for JavaScript code
- Add tests for new features
- Update documentation for API changes
- Ensure responsive design for UI changes

## 📋 Roadmap

### Future Enhancements
- [ ] **Multiple Cricket Shots**: Extend beyond cover drive to pulls, drives, cuts
- [ ] **Comparative Analysis**: Compare against professional player techniques
- [ ] **Video Annotations**: Overlay analysis directly on video frames
- [ ] **Progress Tracking**: Historical improvement tracking for players
- [ ] **Team Analytics**: Batch analysis for coaching teams
- [ ] **Mobile App**: Native iOS/Android applications
- [ ] **Live Streaming**: Real-time analysis during practice sessions

## 🐛 Known Issues

- **Large Video Files**: Processing time increases significantly with video length
- **Lighting Conditions**: Poor lighting may affect pose detection accuracy
- **Camera Angles**: Best results with side-on camera positioning
- **Multiple Players**: Currently optimized for single-player analysis

*CricBuddy - Your AI Coaching Assistant for Better Cricket Technique*
