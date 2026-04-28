"""
Part 3.2 - Multiple Move Generation (N Boards)
Usage:
    @"
    <N>
    <FEN1>
    <FEN2>
    ...
    "@ | python part3_multiple.py
"""
import sys
import os
from collections import Counter
import chess
import chess.engine

def _resolve_stockfish():
    # For automarker compatibility, always use the required path
    return "/opt/stockfish/stockfish"

def _king_capture(board):
    ek = board.king(not board.turn)
    if ek is None:
        return None
    candidates = [
        chess.Move(f, ek)
        for f in board.attackers(board.turn, ek)
        if chess.Move(f, ek) in board.pseudo_legal_moves
    ]
    return sorted(candidates, key=lambda m: m.uci())[0] if candidates else None

def main():
    n = int(sys.stdin.readline().strip())
    fens = [sys.stdin.readline().strip() for _ in range(n)]
    engine = chess.engine.SimpleEngine.popen_uci(_resolve_stockfish(), setpgrp=True)
    try:
        votes = Counter()
        for fen in fens:
            board = chess.Board(fen)
            forced = _king_capture(board)
            if forced:
                votes[forced] += 1
            else:
                votes[engine.play(board, chess.engine.Limit(time=0.5)).move] += 1
        best = max(votes.values())
        tied = [m for m, c in votes.items() if c == best]
        print(sorted(tied, key=lambda m: m.uci())[0].uci())
    finally:
        engine.quit()

if __name__ == "__main__":
    main()
