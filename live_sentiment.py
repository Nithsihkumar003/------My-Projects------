import cv2
import torch
import torch.nn as nn
from torchvision import transforms, models
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np


def load_model(device):
    """Load trained ResNet18 model and class names."""
    data_dir = Path(__file__).resolve().parent
    model_path = data_dir / "emotion_resnet18.pth"

    print(f"[DEBUG] Loading model from: {model_path}")
    checkpoint = torch.load(model_path, map_location=device)
    class_names = checkpoint["class_names"]
    num_classes = len(class_names)

    model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)
    model.eval()

    print(f"[DEBUG] Model loaded with classes: {class_names}")
    return model, class_names


def load_copperplate_font(font_size=40):
    """
    Load Copperplate Gothic Bold TrueType font.

    Put the font file (e.g. COPRGTB.TTF or CopperplateGothicBold.ttf)
    in the same folder as this script and update font_path name if needed.
    """
    data_dir = Path(__file__).resolve().parent

    # >>> IMPORTANT: change ONLY the name below if your file is COPRGTB.TTF
    font_path = data_dir / "COPRGTB.TTF"
    # Example alternatives:
    # font_path = data_dir / "CopperplateGothicBold.ttf"
    # font_path = Path(r"C:/Windows/Fonts/Coprgtb.ttf")

    print(f"[DEBUG] Trying to load font from: {font_path}")

    try:
        font = ImageFont.truetype(str(font_path), font_size)
        print(f"[DEBUG] Loaded Copperplate Gothic Bold successfully.")
    except OSError as e:
        print("[ERROR] Could not load Copperplate Gothic Bold font file.")
        print("        Reason:", e)
        print("        Falling back to Pillow default font.")
        font = ImageFont.load_default()

    return font


def draw_copperplate_text_bgr(frame_bgr, text, position, font, color=(0, 255, 255)):
    """
    Draw text using Copperplate TTF on a BGR OpenCV frame via Pillow.

    color is BGR; (0, 255, 255) = yellow.
    """
    if not text:
        return frame_bgr

    # Convert BGR -> RGB
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(frame_rgb)

    draw = ImageDraw.Draw(pil_image)
    # Convert BGR to RGB
    b, g, r = color
    rgb_color = (r, g, b)

    draw.text(position, text, font=font, fill=rgb_color)

    # Convert back RGB -> BGR
    frame_bgr_out = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    return frame_bgr_out


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device:", device)

    model, class_names = load_model(device)
    copperplate_font = load_copperplate_font(font_size=40)

    # Use OpenCV's installed Haar cascade
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    print("Cascade loaded:", not face_cascade.empty())
    if face_cascade.empty():
        print("Error: Haar cascade could not be loaded.")
        return

    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                             [0.229, 0.224, 0.225]),
    ])

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Error: cannot open webcam.")
        return

    cv2.namedWindow("Real-time Sentiment", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Real-time Sentiment",
                          cv2.WND_PROP_FULLSCREEN,
                          cv2.WINDOW_FULLSCREEN)

    DARK_THRESHOLD = 40.0

    print("[DEBUG] Starting main loop. Press 'q' to exit.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame.")
                break

            display = frame.copy()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=4,
                minSize=(60, 60),
            )

            text = ""
            roi = None

            if len(faces) > 0:
                faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
                (x, y, w, h) = faces[0]
                roi = frame[y:y + h, x:x + w]
                cv2.rectangle(display, (x, y), (x + w, y + h),
                              (0, 255, 0), 2)

                gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                brightness = gray_roi.mean()

                if brightness < DARK_THRESHOLD:
                    text = "Too dark / no face"
                    roi = None
                else:
                    img = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
                    img = transform(img)
                    img = img.unsqueeze(0).to(device)

                    with torch.no_grad():
                        outputs = model(img)
                        probs = torch.softmax(outputs, dim=1)
                        conf, pred = torch.max(probs, 1)

                    label = class_names[pred.item()]
                    conf_val = float(conf.item())
                    text = f"{label} ({conf_val:.2f})"
            else:
                if gray.mean() < DARK_THRESHOLD:
                    text = "Too dark / no face"
                else:
                    text = "No face detected"

            # IMPORTANT: this replaces cv2.putText completely
            display = draw_copperplate_text_bgr(
                display,
                text,
                position=(20, 50),
                font=copperplate_font,
                color=(0, 255, 255),  # yellow
            )

            cv2.imshow("Real-time Sentiment", display)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
