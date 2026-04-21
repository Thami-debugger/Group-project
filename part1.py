"""
Part 1 - State Representation
Usage:
    python part1.py board       # 1.1 Board Representation
    python part1.py move        # 1.2 Move Execution

Examples:
    echo "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" | python part1.py board

    @"
    rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
    e2e4
    "@ | python part1.py move
"""
import sys
import chess


def task_board():
    """1.1 - Read a FEN string, print ASCII board."""
    fen = sys.stdin.readline().strip()
    board = chess.Board(fen)
    for rank in range(7, -1, -1):
        row = []
        for file_idx in range(8):
            piece = board.piece_at(chess.square(file_idx, rank))
            row.append(piece.symbol() if piece else ".")
        print(" ".join(row))


def task_move():
    """1.2 - Read a FEN and a UCI move, print resulting FEN."""
    fen = sys.stdin.readline().strip()
    move_uci = sys.stdin.readline().strip()
    board = chess.Board(fen)
    board.push(chess.Move.from_uci(move_uci))
    print(board.fen())


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("board", "move"):
        print("Usage: python part1.py board|move", file=sys.stderr)
        print("  board  -> 1.1 Board Representation", file=sys.stderr)
        print("  move   -> 1.2 Move Execution", file=sys.stderr)
        sys.exit(1)

    {"board": task_board, "move": task_move}[sys.argv[1]]()


if __name__ == "__main__":
    main()
