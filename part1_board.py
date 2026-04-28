"""
Part 1.1 - Board Representation
Usage:
    echo "<FEN>" | python part1_board.py
"""
import sys
import chess

def main():
    """Read a FEN string from stdin and print ASCII board."""
    fen = sys.stdin.readline().strip()
    board = chess.Board(fen)
    for rank in range(7, -1, -1):
        row = []
        for file_idx in range(8):
            piece = board.piece_at(chess.square(file_idx, rank))
            row.append(piece.symbol() if piece else ".")
        print(" ".join(row))

if __name__ == "__main__":
    main()
