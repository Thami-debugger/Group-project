"""
Part 2.1 - Next Move Prediction
Usage:
    echo "<FEN>" | python part2_moves.py
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

def main():
    fen = sys.stdin.readline().strip()
    board = chess.Board(fen)
    for move in _rbc_moves(board):
        print(move.uci())

if __name__ == "__main__":
    main()
