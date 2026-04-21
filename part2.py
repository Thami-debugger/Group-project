"""
Part 2 - Next State Prediction
Usage:
    python part2.py moves       # 2.1 Next Move Prediction
    python part2.py states      # 2.2 Next State Prediction
    python part2.py captures    # 2.3 Next State Prediction with Captures
    python part2.py sensing     # 2.4 Next State Prediction with Sensing

Examples:
    echo "8/5k2/8/8/8/p1p1p2n/P1P1P3/RB2K2R w K - 12 45" | python part2.py moves

    echo "8/8/8/8/k7/8/7K/3B4 w - - 48 32" | python part2.py states

    @"
    k1n1n3/p2p1p2/P2P1P2/8/8/8/8/7K b - - 23 30
    d6
    "@ | python part2.py captures

    @"
    3
    1k6/1ppn4/8/8/8/1P1P4/PN3P2/2K5 w - - 0 32
    1k6/1ppnP3/8/8/8/1P1P4/PN3P2/2K5 w - - 0 32
    1k6/1ppn1p2/8/8/8/1P1P4/PN3P2/2K5 w - - 0 32
    c8:?;d8:?;e8:?;c7:p;d7:n;e7:?;c6:?;d6:?;e6:?
    "@ | python part2.py sensing
"""
import sys
from typing import List, Optional, Set, Tuple

import chess

try:
    from reconchess.utilities import is_illegal_castle, without_opponent_pieces
except Exception:
    is_illegal_castle = None
    without_opponent_pieces = None


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _rbc_moves(board: chess.Board) -> List[chess.Move]:
    moves: Set[chess.Move] = set(board.pseudo_legal_moves)
    moves.add(chess.Move.null())
    if without_opponent_pieces is not None and is_illegal_castle is not None:
        for mv in without_opponent_pieces(board).generate_castling_moves():
            if not is_illegal_castle(board, mv):
                moves.add(mv)
    return sorted(moves, key=lambda m: m.uci())


def _capture_square(board: chess.Board, move: chess.Move) -> Optional[int]:
    if move == chess.Move.null() or not board.is_capture(move):
        return None
    if board.is_en_passant(move):
        return chess.square(chess.square_file(move.to_square), chess.square_rank(move.from_square))
    return move.to_square


def _parse_window(desc: str) -> List[Tuple[int, str]]:
    result = []
    for entry in desc.strip().split(";"):
        entry = entry.strip()
        if not entry:
            continue
        sq_name, piece = entry.split(":", 1)
        result.append((chess.parse_square(sq_name), piece.strip()))
    return result


def _matches_window(board: chess.Board, window: List[Tuple[int, str]]) -> bool:
    for sq, expected in window:
        piece = board.piece_at(sq)
        if (piece.symbol() if piece else "?") != expected:
            return False
    return True


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

def task_moves():
    """2.1 - All possible next moves from a position."""
    board = chess.Board(sys.stdin.readline().strip())
    for move in _rbc_moves(board):
        print(move.uci())


def task_states():
    """2.2 - All possible next board states from a position."""
    board = chess.Board(sys.stdin.readline().strip())
    results = []
    for move in _rbc_moves(board):
        nb = board.copy(stack=False)
        nb.push(move)
        results.append(nb.fen())
    for fen in sorted(results):
        print(fen)


def task_captures():
    """2.3 - Next states filtered to moves that capture on a given square."""
    board = chess.Board(sys.stdin.readline().strip())
    capture_sq = chess.parse_square(sys.stdin.readline().strip())
    results = []
    for move in _rbc_moves(board):
        if _capture_square(board, move) != capture_sq:
            continue
        nb = board.copy(stack=False)
        nb.push(move)
        results.append(nb.fen())
    for fen in sorted(results):
        print(fen)


def task_sensing():
    """2.4 - Filter a list of states to those consistent with a sensing window."""
    count = int(sys.stdin.readline().strip())
    fens = [sys.stdin.readline().strip() for _ in range(count)]
    window = _parse_window(sys.stdin.readline().strip())
    consistent = [fen for fen in fens if _matches_window(chess.Board(fen), window)]
    for fen in sorted(consistent):
        print(fen)


def main():
    tasks = {"moves": task_moves, "states": task_states, "captures": task_captures, "sensing": task_sensing}
    if len(sys.argv) < 2 or sys.argv[1] not in tasks:
        print("Usage: python part2.py moves|states|captures|sensing", file=sys.stderr)
        print("  moves    -> 2.1 Next Move Prediction", file=sys.stderr)
        print("  states   -> 2.2 Next State Prediction", file=sys.stderr)
        print("  captures -> 2.3 Next State with Captures", file=sys.stderr)
        print("  sensing  -> 2.4 Next State with Sensing", file=sys.stderr)
        sys.exit(1)
    tasks[sys.argv[1]]()


if __name__ == "__main__":
    main()
