import streamlit as st
from ultralytics import YOLO
import chess
import cv2
import numpy as np
import tempfile
import os
import subprocess

# --- STREAMLIT CONFIG (must be first Streamlit command) ---
st.set_page_config(page_title="Chess AI Advisor", page_icon="♟️", layout="wide")  # [web:147]

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "best.pt")
STOCKFISH_PATH = os.path.join(BASE_DIR, "stockfish", "stockfish.exe")


# ---------------- HELPERS ----------------
def get_friendly_move(move, board):
    start_square = move.from_square
    end_square = move.to_square
    piece = board.piece_at(start_square)
    if not piece:
        return f"Move {move.uci()}"

    piece_names = {'p': 'Pawn', 'n': 'Knight', 'b': 'Bishop', 'r': 'Rook', 'q': 'Queen', 'k': 'King'}
    piece_name = piece_names.get(piece.symbol().lower(), "Piece")

    color = "White" if piece.color == chess.WHITE else "Black"
    action = "captures on" if board.is_capture(move) else "moves to"
    dest = chess.square_name(end_square)
    return f"{color} {piece_name} {action} {dest}"


def analyze_position(fen):
    """
    Returns:
      friendly_text (str), score_text (str), best_move_uci (str or None), error (str or None)
    """
    if not os.path.exists(STOCKFISH_PATH):
        return None, "0.00", None, f"CRITICAL ERROR: Stockfish not found at:\n{STOCKFISH_PATH}"

    # Validate FEN early (avoid weird engine behavior)
    try:
        board = chess.Board(fen)
    except Exception as e:
        return None, "0.00", None, f"Invalid FEN: {e}"

    try:
        process = subprocess.Popen(
            STOCKFISH_PATH,
            universal_newlines=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # 3. Send Commands (give Stockfish more time)
        commands = f"uci\nposition fen {fen}\ngo movetime 5000\nquit\n"
        stdout, stderr = process.communicate(input=commands)

        if process.returncode not in (0, None):
            return None, "0.00", None, f"Engine Error: {stderr}"

        best_move_uci = None
        score_text = "0.00"

        for line in stdout.split("\n"):
            if "score cp" in line:
                try:
                    parts = line.split()
                    idx = parts.index("cp")
                    score_val = int(parts[idx + 1]) / 100.0
                    score_text = f"{score_val:+.2f}"
                except:
                    pass
            elif "score mate" in line:
                try:
                    parts = line.split()
                    idx = parts.index("mate")
                    score_text = f"Mate in {parts[idx + 1]}"
                except:
                    pass

            if line.startswith("bestmove"):
                parts = line.split()
                if len(parts) > 1:
                    best_move_uci = parts[1]

        if not best_move_uci or best_move_uci == "(none)":
            return None, score_text, None, "No best move returned (checkmate/stalemate or invalid position)."

        move = chess.Move.from_uci(best_move_uci)
        friendly_text = get_friendly_move(move, board)
        return friendly_text, score_text, best_move_uci, None

    except Exception as e:
        return None, "0.00", None, f"System Error: {e}"


def square_center_in_warped(square_name, cell_size=100):
    """
    In a normalized 8x8 warped board image of size 800x800 (cell_size=100),
    return center pixel (x,y) of a square.
    Assumes warped board is oriented with a8 at top-left, h1 at bottom-right.
    """
    sq = chess.parse_square(square_name)  # a1=0..h8=63
    file_idx = chess.square_file(sq)      # a=0..h=7
    rank_idx = chess.square_rank(sq)      # 1=0..8=7

    # In image coords: top row is rank 8, bottom row is rank 1
    row = 7 - rank_idx
    col = file_idx

    x = int(col * cell_size + cell_size / 2)
    y = int(row * cell_size + cell_size / 2)
    return x, y


def draw_move_arrow_on_image(img_bgr, best_move_uci, corners):
    """
    corners: dict with keys 'tl','tr','br','bl' each (x,y) in original image.
    We warp the board to 800x800, draw arrow, then unwarp back.
    """
    if not best_move_uci or len(best_move_uci) < 4:
        return img_bgr

    # parse move squares
    from_sq = best_move_uci[:2]
    to_sq = best_move_uci[2:4]

    src = np.float32([corners["tl"], corners["tr"], corners["br"], corners["bl"]])
    dst = np.float32([[0, 0], [800, 0], [800, 800], [0, 800]])

    # Perspective transform (board -> square) [web:183]
    M = cv2.getPerspectiveTransform(src, dst)
    Minv = cv2.getPerspectiveTransform(dst, src)

    warped = cv2.warpPerspective(img_bgr, M, (800, 800))

    p1 = square_center_in_warped(from_sq, cell_size=100)
    p2 = square_center_in_warped(to_sq, cell_size=100)

    cv2.arrowedLine(warped, p1, p2, (0, 255, 0), 8, tipLength=0.25)

    # bring it back to original perspective
    unwarped = cv2.warpPerspective(warped, Minv, (img_bgr.shape[1], img_bgr.shape[0]))

    # Blend: overlay arrow region nicely
    out = cv2.addWeighted(img_bgr, 0.65, unwarped, 0.35, 0)
    return out


# ---------------- UI ----------------
st.title("♟️ AI Chess Advisor")
st.write("Upload a board image, enter/confirm FEN, and get the best move + an arrow marking what to move.")

# 1) Upload image
st.subheader("Step 1: Upload Image")
uploaded_file = st.file_uploader("Choose a chess image...", type=["jpg", "png", "jpeg"])

img_bgr = None
temp_filename = None

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tfile:
        tfile.write(uploaded_file.read())
        temp_filename = tfile.name

    img_bgr = cv2.imread(temp_filename)

# 2) Show YOLO detection preview (optional)
st.subheader("Step 2: AI Detection Preview (optional)")
if img_bgr is not None:
    col1, col2 = st.columns(2)
    with col1:
        st.image(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB), caption="Uploaded Image", use_container_width=True)

    if os.path.exists(MODEL_PATH):
        try:
            model = YOLO(MODEL_PATH)
            results = model(temp_filename)
            det_preview = results[0].plot()
            det_rgb = cv2.cvtColor(det_preview, cv2.COLOR_BGR2RGB)
            with col2:
                st.image(det_rgb, caption="AI Detection", use_container_width=True)
        except Exception as e:
            with col2:
                st.error(f"Vision Error: {e}")
    else:
        with col2:
            st.error(f"YOLO model not found: {MODEL_PATH}")

else:
    st.info("Upload an image to see detection preview.")

# 3) FEN input
st.subheader("Step 3: Enter / Confirm FEN")
default_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
detected_fen = st.text_input(
    "FEN string:",
    value=default_fen,
    help="For now, paste FEN from chess.com/lichess, or type it manually."
)

# 4) Corner calibration (manual)
st.subheader("Step 4: Calibrate board corners (to draw arrow on photo)")
st.caption("Enter 4 points in the uploaded image: Top-Left(a8), Top-Right(h8), Bottom-Right(h1), Bottom-Left(a1).")

use_arrow = st.checkbox("Draw move arrow on the uploaded image", value=True)

corners = None
if use_arrow and img_bgr is not None:
    c1, c2 = st.columns(2)
    with c1:
        tlx = st.number_input("Top-Left x (a8)", min_value=0, value=0)
        tly = st.number_input("Top-Left y (a8)", min_value=0, value=0)
        trx = st.number_input("Top-Right x (h8)", min_value=0, value=img_bgr.shape[1]-1 if img_bgr is not None else 0)
        try_ = st.number_input("Top-Right y (h8)", min_value=0, value=0)
    with c2:
        brx = st.number_input("Bottom-Right x (h1)", min_value=0, value=img_bgr.shape[1]-1 if img_bgr is not None else 0)
        bry = st.number_input("Bottom-Right y (h1)", min_value=0, value=img_bgr.shape[0]-1 if img_bgr is not None else 0)
        blx = st.number_input("Bottom-Left x (a1)", min_value=0, value=0)
        bly = st.number_input("Bottom-Left y (a1)", min_value=0, value=img_bgr.shape[0]-1 if img_bgr is not None else 0)

    corners = {
        "tl": (float(tlx), float(tly)),
        "tr": (float(trx), float(try_)),
        "br": (float(brx), float(bry)),
        "bl": (float(blx), float(bly)),
    }
elif use_arrow and img_bgr is None:
    st.warning("Upload an image first to draw an arrow.")

# 5) Analyze
st.write("---")
st.subheader("Step 5: Get Advice")

if st.button("Get Best Move", type="primary"):
    with st.spinner("Consulting Stockfish..."):
        friendly, score, best_move_uci, err = analyze_position(detected_fen)

    if err:
        st.error(err)
    else:
        st.success(f"Best Move: {friendly}")
        st.write(f"UCI: {best_move_uci}")
        st.metric(label="Evaluation", value=score)

        # Try to draw on photo
        if use_arrow and img_bgr is not None and corners is not None:
            try:
                out = draw_move_arrow_on_image(img_bgr.copy(), best_move_uci, corners)
                st.image(cv2.cvtColor(out, cv2.COLOR_BGR2RGB), caption="Move marked on image (arrow)", use_container_width=True)
            except Exception as e:
                st.warning(f"Could not draw arrow (corner calibration may be wrong): {e}")

# cleanup
if temp_filename and os.path.exists(temp_filename):
    try:
        os.remove(temp_filename)
    except Exception:
        pass
