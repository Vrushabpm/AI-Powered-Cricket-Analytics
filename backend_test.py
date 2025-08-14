#!/usr/bin/env python3
"""
Backend Test Suite for AthleteRise Cricket Analytics
Tests the complete video analysis pipeline including API endpoints and core functionality
"""

import requests
import json
import time
import os
import sys
from pathlib import Path
import asyncio
import logging

# Add backend to path for imports
sys.path.append('/app/backend')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CricketAnalyticsBackendTester:
    def __init__(self):
        # Get backend URL from frontend env
        frontend_env_path = Path('/app/frontend/.env')
        self.backend_url = None
        
        if frontend_env_path.exists():
            with open(frontend_env_path, 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        self.backend_url = line.split('=', 1)[1].strip()
                        break
        
        if not self.backend_url:
            raise Exception("Could not find REACT_APP_BACKEND_URL in frontend/.env")
        
        self.api_url = f"{self.backend_url}/api"
        logger.info(f"Testing backend at: {self.api_url}")
        
        # Test video URL
        self.test_video_url = "https://youtube.com/shorts/vSX3IRxGnNY"
        
        # Test results
        self.test_results = {
            'api_health': False,
            'status_endpoints': False,
            'file_upload_valid': False,
            'file_upload_invalid_type': False,
            'file_upload_processing': False,
            'video_analysis_start': False,
            'video_analysis_polling': False,
            'video_analysis_completion': False,
            'biomechanical_calculations': False,
            'evaluation_system': False,
            'error_details': []
        }
    
    def test_api_health(self):
        """Test basic API health check"""
        logger.info("Testing API health check...")
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "AthleteRise Cricket Analytics API" in data.get("message", ""):
                    logger.info("✅ API health check passed")
                    self.test_results['api_health'] = True
                    return True
                else:
                    logger.error(f"❌ Unexpected API response: {data}")
            else:
                logger.error(f"❌ API health check failed with status {response.status_code}")
        except Exception as e:
            logger.error(f"❌ API health check failed: {str(e)}")
            self.test_results['error_details'].append(f"API Health: {str(e)}")
        
        return False
    
    def test_status_endpoints(self):
        """Test status check endpoints"""
        logger.info("Testing status endpoints...")
        try:
            # Test POST /status
            test_data = {"client_name": "cricket_test_client"}
            response = requests.post(f"{self.api_url}/status", json=test_data, timeout=10)
            
            if response.status_code == 200:
                status_obj = response.json()
                if status_obj.get("client_name") == "cricket_test_client":
                    logger.info("✅ POST /status endpoint working")
                    
                    # Test GET /status
                    response = requests.get(f"{self.api_url}/status", timeout=10)
                    if response.status_code == 200:
                        statuses = response.json()
                        if isinstance(statuses, list):
                            logger.info("✅ GET /status endpoint working")
                            self.test_results['status_endpoints'] = True
                            return True
                        else:
                            logger.error("❌ GET /status returned non-list response")
                    else:
                        logger.error(f"❌ GET /status failed with status {response.status_code}")
                else:
                    logger.error("❌ POST /status returned incorrect data")
            else:
                logger.error(f"❌ POST /status failed with status {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Status endpoints test failed: {str(e)}")
            self.test_results['error_details'].append(f"Status Endpoints: {str(e)}")
        
        return False
    
    def test_file_upload_valid(self):
        """Test uploading a valid video file"""
        logger.info("Testing valid file upload...")
        try:
            # Check if test video exists
            test_video_path = "/app/test_cricket_video.mp4"
            if not os.path.exists(test_video_path):
                logger.error("❌ Test video file not found")
                return False
            
            # Upload the test video
            with open(test_video_path, 'rb') as video_file:
                files = {'file': ('test_cricket_video.mp4', video_file, 'video/mp4')}
                response = requests.post(f"{self.api_url}/upload-video", files=files, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if "analysis_id" in result and "filename" in result:
                    self.upload_analysis_id = result["analysis_id"]
                    logger.info(f"✅ Valid file upload successful - Analysis ID: {self.upload_analysis_id}")
                    self.test_results['file_upload_valid'] = True
                    return True
                else:
                    logger.error(f"❌ Upload response missing required fields: {result}")
            else:
                logger.error(f"❌ File upload failed with status {response.status_code}")
                logger.error(f"Response: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ File upload test failed: {str(e)}")
            self.test_results['error_details'].append(f"File Upload Valid: {str(e)}")
        
        return False
    
    def test_file_upload_invalid_type(self):
        """Test uploading an invalid file type"""
        logger.info("Testing invalid file type upload...")
        try:
            # Create a text file to test invalid upload
            test_text_content = "This is not a video file"
            
            files = {'file': ('test.txt', test_text_content, 'text/plain')}
            response = requests.post(f"{self.api_url}/upload-video", files=files, timeout=10)
            
            if response.status_code == 400:
                logger.info("✅ Invalid file type correctly rejected")
                self.test_results['file_upload_invalid_type'] = True
                return True
            else:
                logger.error(f"❌ Invalid file type not rejected - Status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Invalid file type test failed: {str(e)}")
            self.test_results['error_details'].append(f"File Upload Invalid Type: {str(e)}")
        
        return False
    
    def test_file_upload_processing(self):
        """Test that uploaded file starts processing"""
        if not hasattr(self, 'upload_analysis_id'):
            logger.error("❌ No upload analysis ID available for processing test")
            return False
        
        logger.info("Testing uploaded file processing...")
        try:
            # Check analysis status
            response = requests.get(f"{self.api_url}/analysis/{self.upload_analysis_id}", timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                status = result.get("status")
                if status in ["initiated", "processing"]:
                    logger.info(f"✅ Uploaded file processing started - Status: {status}")
                    self.test_results['file_upload_processing'] = True
                    # Store this for completion testing
                    self.analysis_id = self.upload_analysis_id
                    return True
                else:
                    logger.error(f"❌ Unexpected processing status: {status}")
            else:
                logger.error(f"❌ Processing status check failed with status {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ File upload processing test failed: {str(e)}")
            self.test_results['error_details'].append(f"File Upload Processing: {str(e)}")
        
        return False
    def test_video_analysis_start(self):
        """Test starting video analysis (URL-based - for backward compatibility)"""
        logger.info("Testing video analysis start (URL-based)...")
        try:
            analysis_data = {"video_url": self.test_video_url}
            response = requests.post(f"{self.api_url}/analyze-video", json=analysis_data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "initiated" and "analysis_id" in result:
                    self.url_analysis_id = result["analysis_id"]
                    logger.info(f"✅ URL-based video analysis started with ID: {self.url_analysis_id}")
                    self.test_results['video_analysis_start'] = True
                    return True
                else:
                    logger.error(f"❌ Unexpected analysis start response: {result}")
            else:
                logger.error(f"❌ Video analysis start failed with status {response.status_code}")
                logger.error(f"Response: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Video analysis start failed: {str(e)}")
            self.test_results['error_details'].append(f"Video Analysis Start: {str(e)}")
        
        return False
    
    def test_video_analysis_polling(self):
        """Test polling for analysis results"""
        if not hasattr(self, 'analysis_id'):
            logger.error("❌ No analysis ID available for polling test")
            return False
        
        logger.info("Testing video analysis polling...")
        try:
            # Test immediate polling (should show processing)
            response = requests.get(f"{self.api_url}/analysis/{self.analysis_id}", timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("analysis_id") == self.analysis_id:
                    logger.info(f"✅ Analysis polling working - Status: {result.get('status')}")
                    self.test_results['video_analysis_polling'] = True
                    return True
                else:
                    logger.error(f"❌ Analysis polling returned wrong ID: {result}")
            else:
                logger.error(f"❌ Analysis polling failed with status {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Video analysis polling failed: {str(e)}")
            self.test_results['error_details'].append(f"Video Analysis Polling: {str(e)}")
        
        return False
    
    def test_video_analysis_completion(self, max_wait_time=120):
        """Test waiting for analysis completion"""
        if not hasattr(self, 'analysis_id'):
            logger.error("❌ No analysis ID available for completion test")
            return False
        
        logger.info(f"Testing video analysis completion (max wait: {max_wait_time}s)...")
        start_time = time.time()
        
        try:
            while time.time() - start_time < max_wait_time:
                response = requests.get(f"{self.api_url}/analysis/{self.analysis_id}", timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status")
                    
                    if status == "completed":
                        logger.info("✅ Video analysis completed successfully")
                        
                        # Verify result structure
                        if self.verify_analysis_result(result):
                            self.test_results['video_analysis_completion'] = True
                            self.analysis_result = result
                            return True
                        else:
                            logger.error("❌ Analysis result structure invalid")
                            return False
                    
                    elif status == "failed":
                        error_msg = result.get("error_message", "Unknown error")
                        logger.error(f"❌ Video analysis failed: {error_msg}")
                        self.test_results['error_details'].append(f"Analysis Failed: {error_msg}")
                        return False
                    
                    elif status in ["processing", "initiated"]:
                        logger.info(f"Analysis in progress... Status: {status}")
                        time.sleep(5)  # Wait 5 seconds before next check
                    
                    else:
                        logger.warning(f"Unknown analysis status: {status}")
                        time.sleep(5)
                
                else:
                    logger.error(f"❌ Polling failed with status {response.status_code}")
                    return False
            
            logger.error(f"❌ Analysis did not complete within {max_wait_time} seconds")
            
        except Exception as e:
            logger.error(f"❌ Video analysis completion test failed: {str(e)}")
            self.test_results['error_details'].append(f"Video Analysis Completion: {str(e)}")
        
        return False
    
    def verify_analysis_result(self, result):
        """Verify the structure of analysis result"""
        try:
            # Check required fields
            required_fields = ["analysis_id", "status", "video_url", "scores", "feedback"]
            for field in required_fields:
                if field not in result:
                    logger.error(f"❌ Missing required field: {field}")
                    return False
            
            # Check scores structure
            scores = result.get("scores", {})
            expected_scores = ["footwork", "head_position", "swing_control", "balance", "follow_through"]
            for score_type in expected_scores:
                if score_type not in scores:
                    logger.error(f"❌ Missing score type: {score_type}")
                    return False
                
                score_value = scores[score_type]
                if not isinstance(score_value, (int, float)) or not (1 <= score_value <= 10):
                    logger.error(f"❌ Invalid score for {score_type}: {score_value}")
                    return False
            
            # Check feedback structure
            feedback = result.get("feedback", {})
            for score_type in expected_scores:
                if score_type not in feedback:
                    logger.error(f"❌ Missing feedback for: {score_type}")
                    return False
                
                if not isinstance(feedback[score_type], list):
                    logger.error(f"❌ Feedback for {score_type} is not a list")
                    return False
            
            logger.info("✅ Analysis result structure is valid")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error verifying analysis result: {str(e)}")
            return False
    
    def test_biomechanical_calculations(self):
        """Test biomechanical calculation functions"""
        logger.info("Testing biomechanical calculations...")
        try:
            # Import the analyzer
            from video_analysis.cricket_analyzer import CricketVideoAnalyzer
            
            analyzer = CricketVideoAnalyzer()
            
            # Test angle calculation
            point1 = [0.5, 0.3, 0.1]
            point2 = [0.6, 0.4, 0.1]
            point3 = [0.7, 0.3, 0.1]
            
            angle = analyzer.calculate_angle(point1, point2, point3)
            if isinstance(angle, (int, float)) and 0 <= angle <= 180:
                logger.info(f"✅ Angle calculation working: {angle:.2f} degrees")
            else:
                logger.error(f"❌ Invalid angle calculation result: {angle}")
                return False
            
            # Test spine lean calculation
            hip = [0.5, 0.6, 0.1]
            shoulder = [0.5, 0.4, 0.1]
            
            spine_lean = analyzer.calculate_spine_lean(hip, shoulder)
            if isinstance(spine_lean, (int, float)) and 0 <= spine_lean <= 90:
                logger.info(f"✅ Spine lean calculation working: {spine_lean:.2f} degrees")
            else:
                logger.error(f"❌ Invalid spine lean calculation: {spine_lean}")
                return False
            
            # Test head alignment calculation
            head = [0.5, 0.3, 0.1]
            knee = [0.5, 0.7, 0.1]
            
            head_alignment = analyzer.calculate_head_alignment(head, knee, 640)
            if isinstance(head_alignment, (int, float)) and 0 <= head_alignment <= 1:
                logger.info(f"✅ Head alignment calculation working: {head_alignment:.3f}")
            else:
                logger.error(f"❌ Invalid head alignment calculation: {head_alignment}")
                return False
            
            logger.info("✅ All biomechanical calculations working")
            self.test_results['biomechanical_calculations'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Biomechanical calculations test failed: {str(e)}")
            self.test_results['error_details'].append(f"Biomechanical Calculations: {str(e)}")
        
        return False
    
    def test_evaluation_system(self):
        """Test the evaluation scoring system"""
        logger.info("Testing evaluation system...")
        try:
            from video_analysis.cricket_analyzer import CricketVideoAnalyzer
            
            analyzer = CricketVideoAnalyzer()
            
            # Create sample metrics data
            sample_metrics = [
                {
                    'elbow_angle': 115.0,
                    'spine_lean': 20.0,
                    'head_alignment': 0.15,
                    'foot_angle': 30.0
                },
                {
                    'elbow_angle': 120.0,
                    'spine_lean': 22.0,
                    'head_alignment': 0.12,
                    'foot_angle': 28.0
                }
            ]
            
            evaluation = analyzer.evaluate_technique(sample_metrics)
            
            # Verify evaluation structure
            if not isinstance(evaluation, dict):
                logger.error("❌ Evaluation result is not a dictionary")
                return False
            
            required_keys = ['scores', 'feedback', 'metrics_summary']
            for key in required_keys:
                if key not in evaluation:
                    logger.error(f"❌ Missing evaluation key: {key}")
                    return False
            
            # Check scores
            scores = evaluation['scores']
            expected_score_types = ['footwork', 'head_position', 'swing_control', 'balance', 'follow_through']
            
            for score_type in expected_score_types:
                if score_type not in scores:
                    logger.error(f"❌ Missing score type: {score_type}")
                    return False
                
                score = scores[score_type]
                if not isinstance(score, (int, float)) or not (1 <= score <= 10):
                    logger.error(f"❌ Invalid score for {score_type}: {score}")
                    return False
            
            # Check feedback
            feedback = evaluation['feedback']
            for score_type in expected_score_types:
                if score_type not in feedback:
                    logger.error(f"❌ Missing feedback for: {score_type}")
                    return False
                
                if not isinstance(feedback[score_type], list) or len(feedback[score_type]) == 0:
                    logger.error(f"❌ Invalid feedback for {score_type}")
                    return False
            
            logger.info("✅ Evaluation system working correctly")
            logger.info(f"Sample scores: {scores}")
            self.test_results['evaluation_system'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Evaluation system test failed: {str(e)}")
            self.test_results['error_details'].append(f"Evaluation System: {str(e)}")
        
        return False
    
    def test_list_analyses(self):
        """Test listing all analyses"""
        logger.info("Testing list all analyses...")
        try:
            response = requests.get(f"{self.api_url}/analysis", timeout=10)
            
            if response.status_code == 200:
                analyses = response.json()
                if isinstance(analyses, list):
                    logger.info(f"✅ List analyses working - Found {len(analyses)} analyses")
                    return True
                else:
                    logger.error("❌ List analyses returned non-list response")
            else:
                logger.error(f"❌ List analyses failed with status {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ List analyses test failed: {str(e)}")
            self.test_results['error_details'].append(f"List Analyses: {str(e)}")
        
        return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        logger.info("🏏 Starting AthleteRise Cricket Analytics Backend Tests")
        logger.info("=" * 60)
        
        # Test sequence - prioritize file upload tests
        tests = [
            ("API Health Check", self.test_api_health),
            ("Status Endpoints", self.test_status_endpoints),
            ("Valid File Upload", self.test_file_upload_valid),
            ("Invalid File Type Upload", self.test_file_upload_invalid_type),
            ("File Upload Processing", self.test_file_upload_processing),
            ("Biomechanical Calculations", self.test_biomechanical_calculations),
            ("Evaluation System", self.test_evaluation_system),
            ("Video Analysis Polling", self.test_video_analysis_polling),
            ("Video Analysis Completion", self.test_video_analysis_completion),
            ("List All Analyses", self.test_list_analyses),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n🧪 Running: {test_name}")
            try:
                if test_func():
                    passed_tests += 1
                    logger.info(f"✅ {test_name} PASSED")
                else:
                    logger.error(f"❌ {test_name} FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name} FAILED with exception: {str(e)}")
                self.test_results['error_details'].append(f"{test_name}: {str(e)}")
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("🏏 CRICKET ANALYTICS BACKEND TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Tests Passed: {passed_tests}/{total_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if self.test_results['error_details']:
            logger.info("\n❌ ERRORS ENCOUNTERED:")
            for error in self.test_results['error_details']:
                logger.error(f"  - {error}")
        
        # Detailed results
        logger.info("\n📊 DETAILED RESULTS:")
        for key, value in self.test_results.items():
            if key != 'error_details':
                status = "✅ PASS" if value else "❌ FAIL"
                logger.info(f"  {key.replace('_', ' ').title()}: {status}")
        
        return passed_tests, total_tests, self.test_results

def main():
    """Main test execution"""
    try:
        tester = CricketAnalyticsBackendTester()
        passed, total, results = tester.run_all_tests()
        
        # Exit with appropriate code
        if passed == total:
            logger.info("\n🎉 ALL TESTS PASSED! Cricket Analytics Backend is working correctly.")
            sys.exit(0)
        else:
            logger.error(f"\n💥 {total - passed} TESTS FAILED! Please check the issues above.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 Test execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()