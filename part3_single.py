"""
Part 3.1 - Move Generation (Single Board)
Usage:
    echo "<FEN>" | python part3_single.py
"""
import sys
import os
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
    fen = sys.stdin.readline().strip()
    board = chess.Board(fen)
    engine = chess.engine.SimpleEngine.popen_uci(_resolve_stockfish(), setpgrp=True)
    try:
        forced = _king_capture(board)
        if forced:
            print(forced.uci())
        else:
            print(engine.play(board, chess.engine.Limit(time=0.5)).move.uci())
    finally:
        engine.quit()

if __name__ == "__main__":
    main()
