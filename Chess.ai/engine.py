import chess
import chess.engine
import os

# Path to your stockfish executable
STOCKFISH_PATH = os.path.join("stockfish", "stockfish.exe")


class ChessAdvisor:
    def __init__(self):
        # Initialize engine
        self.engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

    def get_analysis(self, fen_string, time_limit=2.0):
        board = chess.Board(fen_string)

        # Analyze top 2 moves to compare them
        info = self.engine.analyse(board, chess.engine.Limit(time=time_limit), multipv=2)

        best_move_info = info[0]
        second_move_info = info[1] if len(info) > 1 else None

        return self._generate_advice(best_move_info, second_move_info, board)

    def _generate_advice(self, best, second, board):
        best_move = best["pv"][0]
        score = best["score"].white()

        # Format the score (CP = centipawns)
        if score.is_mate():
            eval_text = f"Mate in {abs(score.mate())}"
            status = "CRITICAL: Forced Mate sequence!"
        else:
            cp = score.score()
            eval_text = f"{cp / 100:+.2f}"

            # Advice Logic
            if second:
                score2 = second["score"].white().score()
                diff = abs(cp - score2)
                if diff > 150:  # > 1.5 pawns difference
                    status = f"CRITICAL: Only move '{best_move}' works. Others lose advantage."
                else:
                    status = "Normal: Multiple good moves available."
            else:
                status = "Only one legal move available."

        return {
            "best_move": best_move.uci(),
            "evaluation": eval_text,
            "status": status,
            "fen": board.fen()
        }

    def close(self):
        self.engine.quit()
