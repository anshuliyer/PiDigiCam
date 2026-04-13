import cv2
import numpy as np
import os
from enhancer import ImageEnhancer

def test_enhancement():
    # Create a small sample image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.putText(img, "TEST", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    input_path = "test_input.png"
    output_path = "test_output.png"
    cv2.imwrite(input_path, img)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, "models", "FSRCNN_x2.pb")
    
    print(f"Testing enhancement with model: {model_path}")
    
    try:
        enhancer = ImageEnhancer(model_path)
        enhanced_img = enhancer.enhance(img)
        
        print(f"Original shape: {img.shape}")
        print(f"Enhanced shape: {enhanced_img.shape}")
        
        if enhanced_img.shape[0] == img.shape[0] * 2 and enhanced_img.shape[1] == img.shape[1] * 2:
            print("Verification SUCCESS: Image dimensions doubled correctly.")
        else:
            print(f"Verification FAILURE: Unexpected dimensions {enhanced_img.shape}")
            
        cv2.imwrite(output_path, enhanced_img)
        print(f"Test output saved to {output_path}")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
    finally:
        # Clean up
        if os.path.exists(input_path):
            os.remove(input_path)

if __name__ == "__main__":
    test_enhancement()
