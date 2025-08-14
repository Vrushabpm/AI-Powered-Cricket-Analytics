from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
import asyncio
import shutil
from video_analysis.cricket_analyzer import CricketVideoAnalyzer

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create output directory
OUTPUT_DIR = ROOT_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="AthleteRise Cricket Analytics API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize analyzer
analyzer = CricketVideoAnalyzer(output_dir=str(OUTPUT_DIR))

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class AnalysisRequest(BaseModel):
    video_url: Optional[str] = None

class FileUploadResponse(BaseModel):
    message: str
    analysis_id: str
    filename: str

class AnalysisResult(BaseModel):
    analysis_id: str
    status: str  # "processing", "completed", "failed"
    video_url: str
    scores: Optional[Dict[str, Any]] = None
    feedback: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

# Global storage for analysis results (in production, use database)
analysis_results: Dict[str, Dict] = {}

# Background task for video analysis
async def process_video_analysis(analysis_id: str, video_path: str, is_uploaded: bool = False):
    """Background task to process cricket video analysis"""
    try:
        # Update status to processing
        analysis_results[analysis_id]["status"] = "processing"
        
        # Run the analysis
        result = await asyncio.to_thread(analyzer.analyze_video_file, video_path)
        
        # Update with results
        analysis_results[analysis_id].update({
            "status": "completed",
            "scores": result["evaluation"]["scores"],
            "feedback": result["evaluation"]["feedback"],
            "metrics_summary": result["evaluation"]["metrics_summary"],
            "completed_at": datetime.utcnow(),
            "output_files": result.get("output_files", {}),
            "video_info": result.get("video_info", {})
        })
        
        # Store in database
        await db.cricket_analyses.insert_one({
            "analysis_id": analysis_id,
            "video_source": "uploaded" if is_uploaded else "url",
            "result": analysis_results[analysis_id],
            "created_at": analysis_results[analysis_id]["created_at"]
        })
        
    except Exception as e:
        analysis_results[analysis_id].update({
            "status": "failed",
            "error_message": str(e),
            "completed_at": datetime.utcnow()
        })
        logging.error(f"Analysis failed for {analysis_id}: {str(e)}")
        
        # Clean up uploaded file on failure
        if is_uploaded and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except:
                pass

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "AthleteRise Cricket Analytics API", "version": "1.0.0"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

@api_router.post("/upload-video", response_model=FileUploadResponse)
async def upload_cricket_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload cricket video for analysis"""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")
        
        # Generate analysis ID and file path
        analysis_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ['.mp4', '.avi', '.mov', '.mkv']:
            file_extension = '.mp4'  # Default extension
        
        video_filename = f"uploaded_{analysis_id}{file_extension}"
        video_path = OUTPUT_DIR / video_filename
        
        # Save uploaded file
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Initialize analysis record
        analysis_results[analysis_id] = {
            "analysis_id": analysis_id,
            "status": "initiated",
            "video_source": "uploaded",
            "filename": file.filename,
            "created_at": datetime.utcnow(),
            "completed_at": None,
            "error_message": None
        }
        
        # Add background task
        background_tasks.add_task(process_video_analysis, analysis_id, str(video_path), True)
        
        return FileUploadResponse(
            message="Video uploaded successfully. Analysis started.",
            analysis_id=analysis_id,
            filename=file.filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@api_router.post("/analyze-video", response_model=Dict[str, str])
async def start_video_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Start cricket video analysis from URL (kept for backward compatibility)"""
    if not request.video_url:
        raise HTTPException(status_code=400, detail="video_url is required")
        
    analysis_id = str(uuid.uuid4())
    
    # Initialize analysis record
    analysis_results[analysis_id] = {
        "analysis_id": analysis_id,
        "status": "initiated",
        "video_url": request.video_url,
        "created_at": datetime.utcnow(),
        "completed_at": None,
        "error_message": None
    }
    
    # Add background task (will try to download from URL)
    background_tasks.add_task(process_video_analysis, analysis_id, request.video_url, False)
    
    return {
        "analysis_id": analysis_id,
        "status": "initiated",
        "message": "Cricket video analysis started. Use the analysis_id to check status."
    }

@api_router.get("/analysis/{analysis_id}", response_model=Dict[str, Any])
async def get_analysis_result(analysis_id: str):
    """Get analysis result by ID"""
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis_results[analysis_id]

@api_router.get("/analysis", response_model=List[Dict[str, Any]])
async def get_all_analyses():
    """Get all analysis results"""
    return list(analysis_results.values())

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()