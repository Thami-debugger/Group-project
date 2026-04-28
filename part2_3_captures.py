"""
Part 2.3 - Next State Prediction with Captures
Usage:
    @"
    <FEN>
    <move>
    "@ | python part2_captures.py
"""
import sys
import chess

try:
    from reconchess.utilities import is_illegal_castle, without_opponent_pieces
except Exception:
    is_illegal_castle = None
    without_opponent_pieces = None

def _rbc_moves(board):
    moves = set(board.pseudo_legal_moves)
    moves.add(chess.Move.null())
    if without_opponent_pieces is not None and is_illegal_castle is not None:
        for mv in without_opponent_pieces(board).generate_castling_moves():
            if not is_illegal_castle(board, mv):
                moves.add(mv)
    return sorted(moves, key=lambda m: m.uci())

def _capture_square(board, move):
    if move == chess.Move.null() or not board.is_capture(move):
        return None
    if board.is_en_passant(move):
        return chess.square(chess.square_file(move.to_square), chess.square_rank(move.from_square))
    return move.to_square

def main():
    fen = sys.stdin.readline().strip()
    capture_sq = chess.parse_square(sys.stdin.readline().strip())
    board = chess.Board(fen)
    results = []
    for move in _rbc_moves(board):
        if _capture_square(board, move) != capture_sq:
            continue
        nb = board.copy(stack=False)
        nb.push(move)
        results.append(nb.fen())
    for fen in sorted(results):
        print(fen)

if __name__ == "__main__":
    main()
