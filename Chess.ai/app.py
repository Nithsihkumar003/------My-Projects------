import os
from ultralytics import YOLO
import chess
import chess.engine

# --- CONFIG ---
MODEL_PATH = "models/best.pt"
STOCKFISH_PATH = "stockfish/stockfish.exe"  # Make sure this matches your file!
IMAGE_PATH = "test_board.jpg"


def get_advice(fen, engine_path):
    print(f"Analyzing position: {fen}")

    # Check if engine exists
    if not os.path.exists(engine_path):
        return "ERROR: Stockfish not found. Check path."

    try:
        engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        board = chess.Board(fen)

        # Analyze for 2 seconds
        result = engine.analyse(board, chess.engine.Limit(time=2.0), multipv=2)
        engine.quit()

        # Extract Info
        best_move = result[0]["pv"][0]
        score = result[0]["score"].white()

        if score.is_mate():
            eval_text = f"Mate in {abs(score.mate())}"
        else:
            eval_text = f"{score.score() / 100:+.2f}"

        return f"ADVICE: Play {best_move} (Eval: {eval_text})"

    except Exception as e:
        return f"Engine Error: {e}"


def main():
    # 1. Vision Step (Detect pieces)
    print("--- 1. VISION ---")
    model = YOLO(MODEL_PATH)
    results = model(IMAGE_PATH)
    results[0].show()  # Show what it sees

    # NOTE: Converting boxes to a real FEN requires complex grid mapping.
    # For now, we will simulate the connection with a test FEN string.
    # (Imagine YOLO successfully read this from the image)
    detected_fen = "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2"

    print(f"\n[Simulated] YOLO mapped board to FEN: {detected_fen}")

    # 2. Brain Step (Get Advice)
    print("\n--- 2. ADVICE ---")
    advice = get_advice(detected_fen, STOCKFISH_PATH)
    print(advice)


if __name__ == "__main__":
    main()
