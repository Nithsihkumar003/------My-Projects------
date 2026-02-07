from vision import BoardReader
from engine import ChessAdvisor


def main():
    print("--- AI Chess Advisor ---")

    # 1. Initialize Modules
    try:
        # Use yolov8n.pt for first run if you don't have a custom model yet
        reader = BoardReader(model_path="yolov8n.pt")
        advisor = ChessAdvisor()

        # 2. Input Image (Put a chess.jpg in your project folder)
        image_path = "chess_board.jpg"

        # 3. Vision Step
        print(f"Analyzing image: {image_path}...")
        fen = reader.predict_fen(image_path)
        print(f"Detected FEN: {fen}")

        # 4. Analysis Step
        print("Consulting Stockfish...")
        advice = advisor.get_analysis(fen)

        # 5. Output Result
        print("\n" + "=" * 30)
        print(f"ADVICE: {advice['status']}")
        print(f"BEST MOVE: {advice['best_move']}")
        print(f"EVALUATION: {advice['evaluation']}")
        print("=" * 30)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'advisor' in locals():
            advisor.close()


if __name__ == "__main__":
    main()
