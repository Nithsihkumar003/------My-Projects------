from ultralytics import YOLO
import torch

def main():
    # 1. Check GPU
    if torch.cuda.is_available():
        print(f"Using GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("WARNING: Using CPU. Training will be slow.")

    # 2. Load the Nano model (fastest)
    model = YOLO('yolov8n.pt')

    # 3. Train the model
    # We point to the 'data.yaml' file inside your new 'chess_pieces' folder
    results = model.train(
        data='datasets/chess_pieces/data.yaml',
        epochs=30,           # 30 runs through the data (takes ~15 mins on RTX 4060)
        imgsz=640,           # Image size
        device=0,            # Use GPU 0
        batch=16,            # Process 16 images at once
        name='chess_model'   # Name of the output folder
    )

    print("Training Complete! Best model saved in: runs/detect/chess_model/weights/best.pt")

if __name__ == '__main__':
    # This weird protection is REQUIRED for Windows multiprocessing
    main()
