"""
Part 4 Submission - ImprovedAgent
Improved RBC agent: information-gain sensing, Stockfish majority-vote moves.
Run from RBC/solution:
    rc-bot-match ImprovedAgent.py <other_bot.py>
"""
import os
import random
from collections import Counter
from typing import List, Optional, Sequence, Set, Tuple

import chess
import chess.engine
from reconchess import Color, GameHistory, Player, Square, WinReason

try:
    from reconchess.utilities import is_illegal_castle, without_opponent_pieces
except Exception:
    is_illegal_castle = None
    without_opponent_pieces = None


# ---------------------------------------------------------------------------
# Helpers (inlined so this file is self-contained)
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


def _generate_rbc_moves(board: chess.Board) -> List[chess.Move]:
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


def _matches_window(board: chess.Board, window: List[Tuple[int, str]]) -> bool:
    for sq, expected in window:
        piece = board.piece_at(sq)
        if (piece.symbol() if piece else "?") != expected:
            return False
    return True


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class ImprovedAgent(Player):
    """
    Improvement over RandomSensingAgent: instead of sensing randomly,
    choose the square whose 3x3 window produces the most distinct
    observations across current possible boards (maximises information gain).
    """

    def __init__(self) -> None:
        self.color: Optional[Color] = None
        self.possible_fens: Set[str] = set()
        self.engine = chess.engine.SimpleEngine.popen_uci(_resolve_stockfish(), setpgrp=True)

    def handle_game_start(self, color: Color, board: chess.Board, opponent_name: str) -> None:
        self.color = color
        self.possible_fens = {board.fen()}

    def handle_opponent_move_result(self, captured_my_piece: bool, capture_square: Optional[Square]) -> None:
        if self.color is None:
            return
        opp_turn = not self.color
        next_states: Set[str] = set()
        for fen in self.possible_fens:
            board = chess.Board(fen)
            if board.turn != opp_turn:
                next_states.add(fen)
                continue
            for move in _generate_rbc_moves(board):
                sq = _capture_square(board, move)
                if captured_my_piece and sq != capture_square:
                    continue
                if not captured_my_piece and sq is not None:
                    continue
                nb = board.copy(stack=False)
                nb.push(move)
                next_states.add(nb.fen())
        self.possible_fens = next_states

    def choose_sense(self, sense_actions: Sequence[Square], move_actions: Sequence[chess.Move], seconds_left: float) -> Optional[Square]:
        if not sense_actions:
            return None

        candidates = [sq for sq in sense_actions if 0 < chess.square_file(sq) < 7 and 0 < chess.square_rank(sq) < 7]
        if not candidates:
            candidates = list(sense_actions)

        fens = list(self.possible_fens)
        if not fens:
            return random.choice(candidates)

        sample = random.sample(fens, min(500, len(fens)))
        best_sq, best_score = candidates[0], -1

        for sq in candidates:
            cf, cr = chess.square_file(sq), chess.square_rank(sq)
            signatures: Set[tuple] = set()
            for fen in sample:
                board = chess.Board(fen)
                window = []
                for df in (-1, 0, 1):
                    for dr in (-1, 0, 1):
                        f, r = cf + df, cr + dr
                        if 0 <= f < 8 and 0 <= r < 8:
                            p = board.piece_at(chess.square(f, r))
                            window.append(p.symbol() if p else "?")
                        else:
                            window.append("#")
                signatures.add(tuple(window))
            score = len(signatures)
            if score > best_score:
                best_score, best_sq = score, sq

        return best_sq

    def handle_sense_result(self, sense_result: List[Tuple[Square, Optional[chess.Piece]]]) -> None:
        if not sense_result:
            return
        window = [(sq, p.symbol() if p else "?") for sq, p in sense_result]
        filtered = {fen for fen in self.possible_fens if _matches_window(chess.Board(fen), window)}
        if filtered:
            self.possible_fens = filtered

    def choose_move(self, move_actions: Sequence[chess.Move], seconds_left: float) -> Optional[chess.Move]:
        if not move_actions:
            return None
        if len(self.possible_fens) > 10000:
            self.possible_fens = set(random.sample(list(self.possible_fens), 10000))
        secs = max(0.01, 10.0 / max(1, len(self.possible_fens)))
        legal = set(move_actions)
        votes: Counter[chess.Move] = Counter()
        for fen in self.possible_fens:
            board = chess.Board(fen)
            try:
                mv = _pick_move(board, self.engine, secs)
            except chess.engine.EngineError:
                continue
            if mv in legal:
                votes[mv] += 1
        if votes:
            best = max(votes.values())
            tied = [m for m, c in votes.items() if c == best]
            return sorted(tied, key=lambda m: m.uci())[0]
        return random.choice(list(move_actions))

    def handle_move_result(self, requested_move: Optional[chess.Move], taken_move: Optional[chess.Move], captured_opponent_piece: bool, capture_square: Optional[Square]) -> None:
        next_states: Set[str] = set()
        for fen in self.possible_fens:
            board = chess.Board(fen)
            moves = set(_generate_rbc_moves(board))
            if taken_move is None:
                if requested_move is not None and requested_move in moves:
                    continue
                nb = board.copy(stack=False)
                nb.push(chess.Move.null())
                next_states.add(nb.fen())
                continue
            if taken_move not in moves:
                continue
            if requested_move is not None and requested_move.from_square != taken_move.from_square:
                continue
            cap = _capture_square(board, taken_move)
            if captured_opponent_piece and cap != capture_square:
                continue
            if not captured_opponent_piece and cap is not None:
                continue
            nb = board.copy(stack=False)
            nb.push(taken_move)
            next_states.add(nb.fen())
        if next_states:
            self.possible_fens = next_states

    def handle_game_end(self, winner_color: Optional[Color], win_reason: Optional[WinReason], game_history: GameHistory) -> None:
        self.engine.quit()
