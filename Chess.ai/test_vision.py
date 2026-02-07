import os
import cv2
from ultralytics import YOLO


def main():
    # 1. Setup Paths (Fixes the "File Not Found" error)
    # This gets the folder where THIS script is running
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, "models", "best.pt")
    image_path = os.path.join(base_dir, "test_board.jpg")  # Make sure this image exists!

    print(f"Loading model from: {model_path}")

    # 2. Check if files actually exist before crashing
    if not os.path.exists(model_path):
        print("ERROR: Model file not found! Did you copy best.pt to the 'models' folder?")
        return
    if not os.path.exists(image_path):
        print("ERROR: test_board.jpg not found! Please add a chessboard image to your project folder.")
        return

    # 3. Load the Model
    try:
        model = YOLO(model_path)
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    print("Model loaded successfully! analyzing image...")

    # 4. Run Inference (The Vision Part)
    # conf=0.25 means "only show me pieces if you are 25% sure"
    results = model.predict(image_path, conf=0.25)

    # 5. Show the Result
    # Plot the bounding boxes on the image
    result_image = results[0].plot()

    # Create a popup window
    cv2.imshow("Chess AI Vision Test", result_image)

    print("Displaying result. Press any key in the window to close it.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
