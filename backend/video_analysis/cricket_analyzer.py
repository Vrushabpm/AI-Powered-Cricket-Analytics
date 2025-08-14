import cv2
import mediapipe as mp
import numpy as np
import json
import os
import logging
import yt_dlp
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import math
from datetime import datetime

logger = logging.getLogger(__name__)

class CricketVideoAnalyzer:
    """
    AI-Powered Cricket Cover Drive Analyzer
    Performs real-time pose estimation and biomechanical analysis
    """
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize MediaPipe
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Biomechanical thresholds for evaluation
        self.thresholds = {
            'elbow_angle': {'good': (90, 135), 'excellent': (105, 125)},
            'spine_lean': {'good': (10, 30), 'excellent': (15, 25)},  # degrees from vertical
            'head_alignment': {'good': 0.2, 'excellent': 0.1},  # normalized distance
            'foot_angle': {'good': (15, 45), 'excellent': (20, 35)}  # degrees from horizontal
        }
        
    def download_video(self, url: str) -> str:
        """Download video from YouTube using yt-dlp"""
        try:
            output_path = self.output_dir / "input_video.mp4"
            
            ydl_opts = {
                'format': 'best[height<=720]',  # Limit quality for faster processing
                'outtmpl': str(output_path),
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            logger.info(f"Video downloaded successfully: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error downloading video: {str(e)}")
            raise Exception(f"Failed to download video: {str(e)}")
    
    def calculate_angle(self, point1: List[float], point2: List[float], point3: List[float]) -> float:
        """Calculate angle between three points"""
        try:
            # Convert to numpy arrays
            p1 = np.array(point1[:2])  # Only use x, y coordinates
            p2 = np.array(point2[:2])
            p3 = np.array(point3[:2])
            
            # Calculate vectors
            v1 = p1 - p2
            v2 = p3 - p2
            
            # Calculate angle using dot product
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            cos_angle = np.clip(cos_angle, -1.0, 1.0)  # Clamp to valid range
            angle = np.arccos(cos_angle)
            
            return math.degrees(angle)
        except:
            return 0.0
    
    def calculate_spine_lean(self, hip: List[float], shoulder: List[float]) -> float:
        """Calculate spine lean angle from vertical"""
        try:
            # Calculate angle from vertical (90 degrees from horizontal)
            dx = shoulder[0] - hip[0]
            dy = shoulder[1] - hip[1]
            
            # Angle from horizontal
            angle_from_horizontal = math.degrees(math.atan2(abs(dy), abs(dx)))
            
            # Convert to angle from vertical
            spine_lean = abs(90 - angle_from_horizontal)
            
            return spine_lean
        except:
            return 0.0
    
    def calculate_head_alignment(self, head: List[float], knee: List[float], 
                                frame_width: int) -> float:
        """Calculate head-over-knee alignment (normalized distance)"""
        try:
            # Normalized horizontal distance between head and knee
            head_x = head[0] * frame_width
            knee_x = knee[0] * frame_width
            
            distance = abs(head_x - knee_x) / frame_width
            return distance
        except:
            return 1.0  # Max distance if calculation fails
    
    def calculate_foot_angle(self, ankle: List[float], toe: List[float]) -> float:
        """Calculate foot direction angle (approximated from ankle-toe line)"""
        try:
            # Use ankle position as reference (toe position not available in MediaPipe)
            # Approximate foot angle based on ankle position relative to frame
            # This is a simplified calculation
            dx = toe[0] - ankle[0] if toe else 0
            dy = toe[1] - ankle[1] if toe else 0
            
            angle = math.degrees(math.atan2(abs(dy), abs(dx)))
            return angle
        except:
            return 0.0
    
    def extract_pose_landmarks(self, results) -> Dict[str, List[float]]:
        """Extract key pose landmarks"""
        if not results.pose_landmarks:
            return {}
        
        landmarks = results.pose_landmarks.landmark
        
        # Extract key points
        pose_points = {
            'nose': [landmarks[0].x, landmarks[0].y, landmarks[0].z],
            'left_shoulder': [landmarks[11].x, landmarks[11].y, landmarks[11].z],
            'right_shoulder': [landmarks[12].x, landmarks[12].y, landmarks[12].z],
            'left_elbow': [landmarks[13].x, landmarks[13].y, landmarks[13].z],
            'right_elbow': [landmarks[14].x, landmarks[14].y, landmarks[14].z],
            'left_wrist': [landmarks[15].x, landmarks[15].y, landmarks[15].z],
            'right_wrist': [landmarks[16].x, landmarks[16].y, landmarks[16].z],
            'left_hip': [landmarks[23].x, landmarks[23].y, landmarks[23].z],
            'right_hip': [landmarks[24].x, landmarks[24].y, landmarks[24].z],
            'left_knee': [landmarks[25].x, landmarks[25].y, landmarks[25].z],
            'right_knee': [landmarks[26].x, landmarks[26].y, landmarks[26].z],
            'left_ankle': [landmarks[27].x, landmarks[27].y, landmarks[27].z],
            'right_ankle': [landmarks[28].x, landmarks[28].y, landmarks[28].z],
        }
        
        return pose_points
    
    def analyze_biomechanics(self, pose_points: Dict[str, List[float]], 
                           frame_width: int) -> Dict[str, float]:
        """Analyze biomechanical metrics"""
        metrics = {}
        
        try:
            # Determine which side is front (assume right-handed batsman, left side forward)
            front_shoulder = pose_points['left_shoulder']
            front_elbow = pose_points['left_elbow']
            front_wrist = pose_points['left_wrist']
            front_hip = pose_points['left_hip']
            front_knee = pose_points['left_knee']
            front_ankle = pose_points['left_ankle']
            
            # 1. Front elbow angle (shoulder-elbow-wrist)
            elbow_angle = self.calculate_angle(front_shoulder, front_elbow, front_wrist)
            metrics['elbow_angle'] = elbow_angle
            
            # 2. Spine lean (hip-shoulder line vs vertical)
            spine_lean = self.calculate_spine_lean(front_hip, front_shoulder)
            metrics['spine_lean'] = spine_lean
            
            # 3. Head-over-knee alignment
            head_alignment = self.calculate_head_alignment(pose_points['nose'], front_knee, frame_width)
            metrics['head_alignment'] = head_alignment
            
            # 4. Front foot direction (simplified)
            foot_angle = self.calculate_foot_angle(front_ankle, front_knee)  # Approximation
            metrics['foot_angle'] = foot_angle
            
        except Exception as e:
            logger.warning(f"Error calculating biomechanics: {str(e)}")
            metrics = {
                'elbow_angle': 0.0,
                'spine_lean': 0.0,
                'head_alignment': 1.0,
                'foot_angle': 0.0
            }
        
        return metrics
    
    def evaluate_technique(self, all_metrics: List[Dict[str, float]]) -> Dict[str, Any]:
        """Evaluate cricket technique based on biomechanical metrics"""
        if not all_metrics:
            return self._default_evaluation()
        
        # Calculate average metrics across all frames
        avg_metrics = {}
        for metric in ['elbow_angle', 'spine_lean', 'head_alignment', 'foot_angle']:
            values = [m.get(metric, 0) for m in all_metrics if m.get(metric, 0) > 0]
            avg_metrics[metric] = np.mean(values) if values else 0
        
        # Score each category (1-10)
        scores = {}
        feedback = {}
        
        # 1. Footwork (based on foot angle and stability)
        foot_score = self._score_metric(avg_metrics['foot_angle'], 
                                       self.thresholds['foot_angle'])
        scores['footwork'] = foot_score
        feedback['footwork'] = self._get_footwork_feedback(avg_metrics['foot_angle'])
        
        # 2. Head Position (based on head-over-knee alignment)
        head_score = 10 - (avg_metrics['head_alignment'] * 10)  # Lower distance = higher score
        head_score = max(1, min(10, head_score))
        scores['head_position'] = round(head_score)
        feedback['head_position'] = self._get_head_feedback(avg_metrics['head_alignment'])
        
        # 3. Swing Control (based on elbow angle)
        swing_score = self._score_metric(avg_metrics['elbow_angle'], 
                                        self.thresholds['elbow_angle'])
        scores['swing_control'] = swing_score
        feedback['swing_control'] = self._get_swing_feedback(avg_metrics['elbow_angle'])
        
        # 4. Balance (based on spine lean)
        balance_score = self._score_metric(avg_metrics['spine_lean'], 
                                          self.thresholds['spine_lean'])
        scores['balance'] = balance_score
        feedback['balance'] = self._get_balance_feedback(avg_metrics['spine_lean'])
        
        # 5. Follow-through (simplified - based on overall technique)
        follow_through_score = round(np.mean(list(scores.values())))
        scores['follow_through'] = follow_through_score
        feedback['follow_through'] = self._get_followthrough_feedback(follow_through_score)
        
        return {
            'scores': scores,
            'feedback': feedback,
            'metrics_summary': avg_metrics
        }
    
    def _score_metric(self, value: float, thresholds: Dict[str, Tuple[float, float]]) -> int:
        """Score a metric based on thresholds"""
        if not value:
            return 1
        
        excellent_range = thresholds['excellent']
        good_range = thresholds['good']
        
        if excellent_range[0] <= value <= excellent_range[1]:
            return 9 + int(np.random.random() * 2)  # 9-10
        elif good_range[0] <= value <= good_range[1]:
            return 6 + int(np.random.random() * 3)  # 6-8
        else:
            # Distance from ideal range
            excellent_center = (excellent_range[0] + excellent_range[1]) / 2
            distance = abs(value - excellent_center)
            score = max(1, 6 - int(distance / 10))
            return score
    
    def _get_footwork_feedback(self, foot_angle: float) -> List[str]:
        """Generate footwork feedback"""
        feedback = []
        if foot_angle < 15:
            feedback.append("Try to point your front foot more towards the target")
        elif foot_angle > 45:
            feedback.append("Front foot is pointing too wide, align more towards the pitch")
        else:
            feedback.append("Good foot positioning towards the target")
        
        feedback.append("Focus on balanced weight transfer during the shot")
        return feedback
    
    def _get_head_feedback(self, head_alignment: float) -> List[str]:
        """Generate head position feedback"""
        feedback = []
        if head_alignment > 0.2:
            feedback.append("Keep your head more directly over your front knee")
            feedback.append("This will improve balance and shot accuracy")
        else:
            feedback.append("Excellent head position over the front knee")
        
        return feedback
    
    def _get_swing_feedback(self, elbow_angle: float) -> List[str]:
        """Generate swing control feedback"""
        feedback = []
        if elbow_angle < 90:
            feedback.append("Try to keep your front elbow higher during the shot")
        elif elbow_angle > 135:
            feedback.append("Front elbow is too high, lower it slightly for better control")
        else:
            feedback.append("Good elbow positioning for controlled swing")
        
        feedback.append("Maintain smooth acceleration through the ball")
        return feedback
    
    def _get_balance_feedback(self, spine_lean: float) -> List[str]:
        """Generate balance feedback"""
        feedback = []
        if spine_lean < 10:
            feedback.append("Lean slightly forward for better balance and power")
        elif spine_lean > 30:
            feedback.append("Reduce forward lean to maintain better balance")
        else:
            feedback.append("Good spine angle for balanced shot execution")
        
        return feedback
    
    def _get_followthrough_feedback(self, score: int) -> List[str]:
        """Generate follow-through feedback"""
        if score >= 8:
            return ["Excellent overall technique", "Continue practicing for consistency"]
        elif score >= 6:
            return ["Good technique with room for refinement", "Focus on identified weak areas"]
        else:
            return ["Technique needs improvement", "Practice basic fundamentals regularly"]
    
    def _default_evaluation(self) -> Dict[str, Any]:
        """Return default evaluation when analysis fails"""
        return {
            'scores': {
                'footwork': 5,
                'head_position': 5,
                'swing_control': 5,
                'balance': 5,
                'follow_through': 5
            },
            'feedback': {
                'footwork': ["Analysis incomplete - please ensure clear video quality"],
                'head_position': ["Analysis incomplete - please ensure clear video quality"],
                'swing_control': ["Analysis incomplete - please ensure clear video quality"],
                'balance': ["Analysis incomplete - please ensure clear video quality"],
                'follow_through': ["Analysis incomplete - please ensure clear video quality"]
            },
            'metrics_summary': {
                'elbow_angle': 0.0,
                'spine_lean': 0.0,
                'head_alignment': 0.0,
                'foot_angle': 0.0
            }
        }
    
    def analyze_video_file(self, video_path: str) -> Dict[str, Any]:
        """Main analysis function for local video files"""
        try:
            logger.info(f"Starting analysis of video file: {video_path}")
            
            # Check if file exists
            if not os.path.exists(video_path):
                raise Exception(f"Video file not found: {video_path}")
            
            # Open video
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception("Could not open video file")
            
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            logger.info(f"Video info: {frame_count} frames, {fps} FPS, {frame_width}x{frame_height}")
            
            all_metrics = []
            frames_processed = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process with MediaPipe
                results = self.pose.process(rgb_frame)
                
                if results.pose_landmarks:
                    # Extract pose landmarks
                    pose_points = self.extract_pose_landmarks(results)
                    
                    if pose_points:
                        # Analyze biomechanics
                        metrics = self.analyze_biomechanics(pose_points, frame_width)
                        all_metrics.append(metrics)
                
                frames_processed += 1
                
                # Log progress every 10 frames
                if frames_processed % 10 == 0:
                    logger.info(f"Processed {frames_processed}/{frame_count} frames")
            
            cap.release()
            
            logger.info(f"Analysis complete. Processed {frames_processed} frames with {len(all_metrics)} valid pose detections")
            
            # Evaluate technique
            evaluation = self.evaluate_technique(all_metrics)
            
            # Save results
            output_file = self.output_dir / f"evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump(evaluation, f, indent=2)
            
            result = {
                'evaluation': evaluation,
                'video_info': {
                    'frames_total': frame_count,
                    'frames_processed': frames_processed,
                    'frames_with_pose': len(all_metrics),
                    'fps': fps,
                    'duration_seconds': frame_count / fps if fps > 0 else 0
                },
                'output_files': {
                    'evaluation_json': str(output_file),
                    'input_video': video_path
                }
            }
            
            logger.info("Cricket analysis completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            raise Exception(f"Video analysis failed: {str(e)}")
        
        finally:
            # Cleanup
            if 'cap' in locals():
                cap.release()
    
    def analyze_video(self, video_url: str) -> Dict[str, Any]:
        """Main analysis function for video URLs (downloads first)"""
        try:
            logger.info(f"Starting analysis of video: {video_url}")
            
            # Download video
            video_path = self.download_video(video_url)
            
            # Use the local file analysis
            return self.analyze_video_file(video_path)
            
        except Exception as e:
            logger.error(f"URL-based analysis failed: {str(e)}")
            raise Exception(f"Video analysis failed: {str(e)}")