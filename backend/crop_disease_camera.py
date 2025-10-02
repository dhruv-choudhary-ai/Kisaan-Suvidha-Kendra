"""
Real-time crop disease detection using camera feed
Detects leaves, captures frame, sends to Gemini Vision for diagnosis
"""
import cv2
import numpy as np
import base64
import time
import logging
from typing import Optional, Tuple, Dict
import google.generativeai as genai
from config import Config
import io
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini with vision capability
genai.configure(api_key=Config.GEMINI_API_KEY)

class CropDiseaseCamera:
    """Real-time camera-based crop disease detection"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.leaf_cascade = None
        self.setup_leaf_detection()
        
    def setup_leaf_detection(self):
        """Setup leaf detection using color and contour analysis"""
        # We'll use color-based detection since OpenCV doesn't have leaf cascade
        # Green color range in HSV for leaf detection
        self.lower_green = np.array([25, 40, 40])
        self.upper_green = np.array([90, 255, 255])
        
        # Alternative: brown/yellow for diseased leaves
        self.lower_brown = np.array([10, 40, 40])
        self.upper_brown = np.array([25, 255, 255])
    
    def detect_leaf_in_frame(self, frame: np.ndarray) -> Tuple[bool, Optional[np.ndarray], float]:
        """
        Detect if a leaf is present in the frame using color segmentation
        
        Returns:
            (is_leaf_detected, cropped_leaf_region, confidence_score)
        """
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Create masks for green and brown/yellow colors
        mask_green = cv2.inRange(hsv, self.lower_green, self.upper_green)
        mask_brown = cv2.inRange(hsv, self.lower_brown, self.upper_brown)
        
        # Combine masks
        mask = cv2.bitwise_or(mask_green, mask_brown)
        
        # Morphological operations to reduce noise
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return False, None, 0.0
        
        # Find the largest contour (likely the leaf)
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)
        
        # Minimum area threshold (adjust based on camera distance)
        min_area = frame.shape[0] * frame.shape[1] * 0.15  # 15% of frame
        
        if area < min_area:
            return False, None, 0.0
        
        # Get bounding box of the leaf
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # Add padding
        padding = 20
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(frame.shape[1] - x, w + 2 * padding)
        h = min(frame.shape[0] - y, h + 2 * padding)
        
        # Crop the leaf region
        leaf_region = frame[y:y+h, x:x+w]
        
        # Calculate confidence based on area ratio and shape
        frame_area = frame.shape[0] * frame.shape[1]
        confidence = min(1.0, (area / frame_area) * 5)  # Scale confidence
        
        return True, leaf_region, confidence
    
    def encode_image_to_base64(self, image: np.ndarray) -> str:
        """Convert OpenCV image to base64 string"""
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(image_rgb)
        
        # Resize for faster processing (max 1024px)
        max_size = 1024
        if max(pil_image.size) > max_size:
            ratio = max_size / max(pil_image.size)
            new_size = tuple(int(dim * ratio) for dim in pil_image.size)
            pil_image = pil_image.resize(new_size, Image.LANCZOS)
        
        # Convert to bytes
        buffer = io.BytesIO()
        pil_image.save(buffer, format='JPEG', quality=85, optimize=True)
        image_bytes = buffer.getvalue()
        
        # Encode to base64
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def check_if_leaf_present(self, image_base64: str, language: str = "hindi") -> Dict:
        """
        Check if a plant leaf is present in the image (faster check)
        
        Args:
            image_base64: Base64 encoded image
            language: Response language
            
        Returns:
            Dictionary with leaf presence result
        """
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_base64)
            pil_image = Image.open(io.BytesIO(image_bytes))
            
            # Quick check with Gemini
            prompt = """
            Is there a plant leaf visible in this image? Answer with ONLY "YES" or "NO" followed by confidence percentage.
            Format: YES 95% or NO 10%
            """
            
            response = self.model.generate_content([prompt, pil_image])
            response_text = response.text.strip().upper()
            
            is_leaf = "YES" in response_text
            
            messages = {
                "hindi": "पत्ती को कैमरे के सामने अच्छे से रखिए" if not is_leaf else "पत्ती मिल गई, विश्लेषण हो रहा है...",
                "english": "Please hold the leaf properly in front of camera" if not is_leaf else "Leaf found, analyzing..."
            }
            
            return {
                "success": True,
                "is_leaf_present": is_leaf,
                "message": messages[language],
                "raw_response": response_text
            }
            
        except Exception as e:
            logger.error(f"Leaf check error: {str(e)}")
            return {
                "success": False,
                "is_leaf_present": False,
                "error": str(e)
            }
    
    def diagnose_from_base64(self, image_base64: str, language: str = "hindi") -> Dict:
        """
        Diagnose disease from base64 encoded image (for web/mobile)
        
        Args:
            image_base64: Base64 encoded image from browser
            language: Response language
            
        Returns:
            Dictionary with diagnosis results
        """
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_base64)
            pil_image = Image.open(io.BytesIO(image_bytes))
            
            # Resize for faster processing
            max_size = 1024
            if max(pil_image.size) > max_size:
                ratio = max_size / max(pil_image.size)
                new_size = tuple(int(dim * ratio) for dim in pil_image.size)
                pil_image = pil_image.resize(new_size, Image.LANCZOS)
            
            # Create prompt based on language
            prompts = {
                "hindi": """
                आप एक विशेषज्ञ कृषि रोग विशेषज्ञ हैं। इस पत्ती की तस्वीर का विश्लेषण करें और बताएं:
                
                1. फसल का नाम (अगर पहचान सकें)
                2. क्या कोई बीमारी या कीट का संक्रमण है?
                3. बीमारी का नाम और लक्षण
                4. गंभीरता स्तर (कम, मध्यम, उच्च)
                5. उपचार के तरीके (जैविक और रासायनिक दोनों)
                6. रोकथाम के उपाय
                
                सरल हिंदी में जवाब दें जो किसान आसानी से समझ सकें। अधिकतम 150 शब्दों में।
                """,
                "english": """
                You are an expert agricultural disease specialist. Analyze this leaf image and provide:
                
                1. Crop name (if identifiable)
                2. Is there any disease or pest infestation?
                3. Disease name and symptoms
                4. Severity level (low, medium, high)
                5. Treatment methods (both organic and chemical)
                6. Prevention measures
                
                Provide response in simple language that farmers can easily understand. Maximum 150 words.
                """
            }
            
            prompt = prompts.get(language, prompts["hindi"])
            
            # Generate diagnosis using Gemini Vision
            response = self.model.generate_content([prompt, pil_image])
            
            return {
                "success": True,
                "diagnosis": response.text,
                "language": language,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Gemini diagnosis error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "diagnosis": "निदान में त्रुटि हुई" if language == "hindi" else "Diagnosis error occurred"
            }
        """
        Send leaf image to Gemini Vision for disease diagnosis
        
        Args:
            image: OpenCV image (numpy array)
            language: Response language
            
        Returns:
            Dictionary with diagnosis results
        """
        try:
            # Convert image to PIL format for Gemini
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
            
            # Resize for faster processing
            max_size = 1024
            if max(pil_image.size) > max_size:
                ratio = max_size / max(pil_image.size)
                new_size = tuple(int(dim * ratio) for dim in pil_image.size)
                pil_image = pil_image.resize(new_size, Image.LANCZOS)
            
            # Create prompt based on language
            prompts = {
                "hindi": """
                आप एक विशेषज्ञ कृषि रोग विशेषज्ञ हैं। इस पत्ती की तस्वीर का विश्लेषण करें और बताएं:
                
                1. फसल का नाम (अगर पहचान सकें)
                2. क्या कोई बीमारी या कीट का संक्रमण है?
                3. बीमारी का नाम और लक्षण
                4. गंभीरता स्तर (कम, मध्यम, उच्च)
                5. उपचार के तरीके (जैविक और रासायनिक दोनों)
                6. रोकथाम के उपाय
                
                सरल हिंदी में जवाब दें जो किसान आसानी से समझ सकें।
                """,
                "english": """
                You are an expert agricultural disease specialist. Analyze this leaf image and provide:
                
                1. Crop name (if identifiable)
                2. Is there any disease or pest infestation?
                3. Disease name and symptoms
                4. Severity level (low, medium, high)
                5. Treatment methods (both organic and chemical)
                6. Prevention measures
                
                Provide response in simple language that farmers can easily understand.
                """
            }
            
            prompt = prompts.get(language, prompts["hindi"])
            
            # Generate diagnosis using Gemini Vision
            response = self.model.generate_content([prompt, pil_image])
            
            return {
                "success": True,
                "diagnosis": response.text,
                "language": language,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Gemini diagnosis error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "diagnosis": "निदान में त्रुटि हुई" if language == "hindi" else "Diagnosis error occurred"
            }
    
    def capture_and_diagnose(
        self, 
        camera_index: int = 0,
        timeout_seconds: int = 5,
        language: str = "hindi"
    ) -> Dict:
        """
        Open camera, detect leaf, capture frame, and diagnose disease
        
        Args:
            camera_index: Camera device index (0 for default)
            timeout_seconds: Maximum time to wait for leaf detection
            language: Response language
            
        Returns:
            Dictionary with diagnosis results
        """
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            return {
                "success": False,
                "error": "Camera could not be opened",
                "message": "कैमरा नहीं खुल सका" if language == "hindi" else "Camera failed to open"
            }
        
        # Set camera properties for faster processing
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        start_time = time.time()
        best_frame = None
        best_confidence = 0.0
        frame_count = 0
        
        messages = {
            "hindi": "कृपया पत्ती को सही से कैमरे के सामने रखें",
            "english": "Please hold the leaf properly in front of the camera"
        }
        
        logger.info(f"Camera opened. Waiting for leaf detection (timeout: {timeout_seconds}s)")
        
        try:
            while (time.time() - start_time) < timeout_seconds:
                ret, frame = cap.read()
                
                if not ret:
                    continue
                
                frame_count += 1
                
                # Skip frames for faster processing (process every 3rd frame)
                if frame_count % 3 != 0:
                    continue
                
                # Detect leaf in frame
                is_detected, leaf_region, confidence = self.detect_leaf_in_frame(frame)
                
                # Draw detection feedback on frame
                if is_detected:
                    cv2.putText(
                        frame, 
                        f"Leaf Detected: {confidence:.2f}", 
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.7, 
                        (0, 255, 0), 
                        2
                    )
                    
                    # Keep track of best frame
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_frame = leaf_region.copy()
                    
                    # If confidence is high enough, capture immediately
                    if confidence > 0.7:
                        logger.info(f"High confidence detection: {confidence:.2f}")
                        break
                else:
                    cv2.putText(
                        frame,
                        messages[language],
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 0, 255),
                        2
                    )
                
                # Display frame (optional - comment out for headless servers)
                cv2.imshow('Crop Disease Detection', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
        finally:
            cap.release()
            cv2.destroyAllWindows()
        
        # Check if leaf was detected
        if best_frame is None or best_confidence < 0.3:
            return {
                "success": False,
                "message": messages[language],
                "confidence": best_confidence
            }
        
        logger.info(f"Leaf captured with confidence: {best_confidence:.2f}. Sending to Gemini...")
        
        # Diagnose the disease using Gemini Vision
        diagnosis_result = self.diagnose_disease_with_gemini(best_frame, language)
        diagnosis_result["confidence"] = best_confidence
        diagnosis_result["image_base64"] = self.encode_image_to_base64(best_frame)
        
        return diagnosis_result


# FastAPI endpoint integration
def create_disease_detection_endpoint():
    """
    Add this to main.py to integrate camera-based disease detection
    """
    from fastapi import BackgroundTasks
    from pydantic import BaseModel
    
    class DiseaseDetectionRequest(BaseModel):
        camera_index: int = 0
        timeout_seconds: int = 5
        language: str = "hindi"
    
    camera_detector = CropDiseaseCamera()
    
    async def detect_crop_disease(request: DiseaseDetectionRequest):
        """
        Endpoint to start camera-based disease detection
        """
        result = camera_detector.capture_and_diagnose(
            camera_index=request.camera_index,
            timeout_seconds=request.timeout_seconds,
            language=request.language
        )
        
        return result
    
    return detect_crop_disease


# Standalone testing
if __name__ == "__main__":
    detector = CropDiseaseCamera()
    
    print("Starting camera-based crop disease detection...")
    print("Press 'q' to quit")
    
    result = detector.capture_and_diagnose(
        camera_index=0,
        timeout_seconds=10,
        language="hindi"
    )
    
    if result["success"]:
        print("\n=== Diagnosis Result ===")
        print(result["diagnosis"])
        print(f"\nConfidence: {result.get('confidence', 0):.2f}")
    else:
        print(f"\nError: {result.get('message', 'Unknown error')}")