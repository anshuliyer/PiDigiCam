import cv2
import os
import sys

class ImageEnhancer:
    """
    Ultra-lightweight image enhancement using FSRCNN (Fast Super-Resolution Convolutional Neural Network).
    Designed for edge devices like Raspberry Pi.
    """
    def __init__(self, model_path, scale=2):
        self.scale = scale
        self.sr = cv2.dnn_superres.DnnSuperResImpl_create()
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")
            
        # Load the model
        print(f"Loading model from {model_path}...")
        self.sr.readModel(model_path)
        
        # Extract model name from filename (e.g., fsrcnn)
        model_name = os.path.basename(model_path).split('_')[0].lower()
        self.sr.setModel(model_name, scale)
        print(f"Model {model_name} loaded with scale {scale}")

    def enhance(self, img_input):
        """
        Enhances the input image.
        :param img_input: Can be a path to an image or an OpenCV image (numpy array).
        :return: Enhanced OpenCV image.
        """
        if isinstance(img_input, str):
            image = cv2.imread(img_input)
            if image is None:
                raise ValueError(f"Could not read image at {img_input}")
        else:
            image = img_input

        # Upsample using AI model
        print("Upsampling image...")
        result = self.sr.upsample(image)
        
        return result

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python enhancer.py <input_image> <output_image> [model_path]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    # Default model path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = sys.argv[3] if len(sys.argv) > 3 else os.path.join(script_dir, "models", "FSRCNN_x2.pb")

    try:
        enhancer = ImageEnhancer(model_path)
        enhanced_img = enhancer.enhance(input_path)
        cv2.imwrite(output_path, enhanced_img)
        print(f"Successfully enhanced image and saved to {output_path}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
