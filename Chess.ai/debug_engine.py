import os
import streamlit as st
import chess
import chess.engine

# Must be first Streamlit command
st.set_page_config(page_title="Chess Advisor (Stable)", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STOCKFISH_PATH = os.path.join(BASE_DIR, "stockfish", "stockfish.exe")
CREATE_NO_WINDOW = 0x08000000  # Windows: hide console window

st.title("Chess Advisor (Stable old version)")
st.caption(f"RUNNING FILE: {__file__}")
st.caption(f"PID: {os.getpid()}")

with st.sidebar:
    st.subheader("Diagnostics")
    st.write(f"Stockfish: `{STOCKFISH_PATH}`")
    st.write(f"Exists: `{os.path.exists(STOCKFISH_PATH)}`")

@st.cache_resource
def get_engine():
    # Recommended method to communicate with Stockfish. [web:116]
    return chess.engine.SimpleEngine.popen_uci(
        STOCKFISH_PATH,
        creationflags=CREATE_NO_WINDOW
    )

def analyse_fen(fen: str, think_time: float = 1.0):
    board = chess.Board(fen)  # validates FEN
    engine = get_engine()
    limit = chess.engine.Limit(time=think_time)

    info = engine.analyse(board, limit)
    if "pv" in info and info["pv"]:
        best_move = info["pv"][0]
    else:
        best_move = engine.play(board, limit).move

    score_obj = info.get("score")
    if score_obj is not None:
        pov = score_obj.pov(board.turn)
        if pov.is_mate():
            score = f"Mate in {pov.mate()}"
        else:
            cp = pov.score(mate_score=100000)
            score = f"{cp/100:+.2f}" if cp is not None else "N/A"
    else:
        score = "N/A"

    return best_move.uci(), score

uploaded = st.file_uploader("Upload image (optional)", type=["jpg", "jpeg", "png"])
if uploaded:
    st.info("Image uploaded. (This stable version does not auto-detect pieces yet.)")

default_fen = chess.STARTING_FEN
fen = st.text_area("Paste FEN here", value=default_fen, height=80)

think_time = st.slider("Think time (seconds)", 0.1, 5.0, 1.0, 0.1)

if st.button("Analyze"):
    try:
        # Validate first
        chess.Board(fen)
    except Exception as e:
        st.error(f"Invalid FEN: {e}")
        st.stop()

    try:
        best_move, score = analyse_fen(fen, think_time=think_time)
        st.success(f"Best move: {best_move}")
        st.write(f"Score: {score}")
    except Exception as e:
        st.error(f"Engine error: {e}")
