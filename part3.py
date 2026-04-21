"""
Part 3 - Move Selection (requires Stockfish)
Usage:
    python part3.py single      # 3.1 Move Generation (one board)
    python part3.py multiple    # 3.2 Multiple Move Generation (N boards)

Examples:
    echo "8/8/8/8/k7/8/7K/3B4 w - - 48 32" | python part3.py single

    @"
    2
    r1bqk2r/pppp1ppp/2n2n2/4B3/1b2P3/1P3N2/P1PP1PPP/RN1QKB1R b KQkq - 0 5
    r1bqk2r/pppp1ppp/2n2n2/4N3/1b2P3/1P6/PBPP1PPP/RN1QKB1R b KQkq - 0 5
    "@ | python part3.py multiple
"""
import os
import sys
from collections import Counter
from typing import List, Optional, Set

import chess
import chess.engine

try:
    from reconchess.utilities import is_illegal_castle, without_opponent_pieces
except Exception:
    is_illegal_castle = None
    without_opponent_pieces = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_stockfish() -> str:
    env = os.environ.get("STOCKFISH_PATH")
    if env:
        return env
    for path in [
        r"C:\Users\nkosi\AppData\Local\Microsoft\WinGet\Links\stockfish.exe",
        "./stockfish",
        "./stockfish.exe",
        "/opt/stockfish/stockfish",
    ]:
        if os.path.exists(path):
            return path
    return "/opt/stockfish/stockfish"


def _king_capture(board: chess.Board) -> Optional[chess.Move]:
    ek = board.king(not board.turn)
    if ek is None:
        return None
    candidates = [
        chess.Move(f, ek)
        for f in board.attackers(board.turn, ek)
        if chess.Move(f, ek) in board.pseudo_legal_moves
    ]
    return sorted(candidates, key=lambda m: m.uci())[0] if candidates else None


def _pick_move(board: chess.Board, engine: chess.engine.SimpleEngine, secs: float) -> chess.Move:
    forced = _king_capture(board)
    if forced:
        return forced
    return engine.play(board, chess.engine.Limit(time=secs)).move


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

def task_single():
    """3.1 - Best move for one board."""
    board = chess.Board(sys.stdin.readline().strip())
    engine = chess.engine.SimpleEngine.popen_uci(_resolve_stockfish(), setpgrp=True)
    try:
        print(_pick_move(board, engine, 0.5).uci())
    finally:
        engine.quit()


def task_multiple():
    """3.2 - Majority-vote best move across N boards."""
    count = int(sys.stdin.readline().strip())
    fens = [sys.stdin.readline().strip() for _ in range(count)]
    engine = chess.engine.SimpleEngine.popen_uci(_resolve_stockfish(), setpgrp=True)
    try:
        votes: Counter[chess.Move] = Counter()
        for fen in fens:
            votes[_pick_move(chess.Board(fen), engine, 0.5)] += 1
        best = max(votes.values())
        tied = [m for m, c in votes.items() if c == best]
        print(sorted(tied, key=lambda m: m.uci())[0].uci())
    finally:
        engine.quit()


def main():
    tasks = {"single": task_single, "multiple": task_multiple}
    if len(sys.argv) < 2 or sys.argv[1] not in tasks:
        print("Usage: python part3.py single|multiple", file=sys.stderr)
        print("  single   -> 3.1 Move Generation (one board)", file=sys.stderr)
        print("  multiple -> 3.2 Multiple Move Generation (N boards)", file=sys.stderr)
        sys.exit(1)
    tasks[sys.argv[1]]()


if __name__ == "__main__":
    main()
