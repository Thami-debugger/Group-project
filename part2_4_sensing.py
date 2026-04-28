"""
Part 2.4 - Next State Prediction with Sensing
Usage:
    @"
    <N>
    <FEN1>
    <FEN2>
    ...
    <Sensing info>
    "@ | python part2_sensing.py
"""
import sys
import chess

def _parse_window(desc):
    result = []
    for entry in desc.strip().split(";"):
        entry = entry.strip()
        if not entry:
            continue
        sq_name, piece = entry.split(":", 1)
        result.append((chess.parse_square(sq_name), piece.strip()))
    return result

def _matches_window(board, window):
    for sq, expected in window:
        piece = board.piece_at(sq)
        if (piece.symbol() if piece else "?") != expected:
            return False
    return True

def main():
    n = int(sys.stdin.readline().strip())
    fens = [sys.stdin.readline().strip() for _ in range(n)]
    window = _parse_window(sys.stdin.readline().strip())
    consistent = [fen for fen in fens if _matches_window(chess.Board(fen), window)]
    for fen in sorted(consistent):
        print(fen)

if __name__ == "__main__":
    main()
