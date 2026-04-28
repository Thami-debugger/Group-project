"""
Part 1.2 - Move Execution
Usage:
    @"
    <FEN>
    <UCI move>
    "@ | python part1_move.py
"""
import sys
import chess

def main():
    """Read a FEN and a UCI move from stdin and print resulting FEN."""
    fen = sys.stdin.readline().strip()
    move_uci = sys.stdin.readline().strip()
    board = chess.Board(fen)
    board.push(chess.Move.from_uci(move_uci))
    print(board.fen())

if __name__ == "__main__":
    main()
