import os
from typing import Iterable, List

import chess
import chess.engine
from flask import Flask, jsonify, render_template, request

from part2 import _capture_square, _matches_window, _parse_window, _rbc_moves
from part3 import _pick_move, _resolve_stockfish


app = Flask(__name__)


PIECE_NAMES = {
    "p": "pawn",
    "n": "knight",
    "b": "bishop",
    "r": "rook",
    "q": "queen",
    "k": "king",
}


def _json_error(message: str, status: int = 400):
    response = jsonify({"error": message})
    response.status_code = status
    return response


def _require_fields(payload: dict, fields: Iterable[str]) -> List[str]:
    missing = []
    for field in fields:
        value = payload.get(field, "")
        if value is None or not str(value).strip():
            missing.append(field)
    return missing


def _load_board(fen: str) -> chess.Board:
    if fen is None:
        raise ValueError("FEN is required.")
    return chess.Board(str(fen).strip())


def _square_payload(board: chess.Board, square: int) -> dict:
    piece = board.piece_at(square)
    return {
        "name": chess.square_name(square),
        "file": chess.square_file(square),
        "rank": chess.square_rank(square),
        "dark": (chess.square_file(square) + chess.square_rank(square)) % 2 == 1,
        "piece": piece.symbol() if piece else None,
        "pieceName": PIECE_NAMES.get(piece.symbol().lower()) if piece else None,
        "pieceColor": "white" if piece and piece.color == chess.WHITE else "black" if piece else None,
    }


def _board_payload(board: chess.Board) -> dict:
    rows = []
    for rank in range(7, -1, -1):
        row = []
        for file_idx in range(8):
            row.append(_square_payload(board, chess.square(file_idx, rank)))
        rows.append(row)

    ascii_rows = []
    for row in rows:
        ascii_rows.append(" ".join(square["piece"] or "." for square in row))

    return {
        "fen": board.fen(),
        "turn": "white" if board.turn == chess.WHITE else "black",
        "isCheck": board.is_check(),
        "isGameOver": board.is_game_over(),
        "result": board.result(claim_draw=True) if board.is_game_over(claim_draw=True) else None,
        "fullmoveNumber": board.fullmove_number,
        "halfmoveClock": board.halfmove_clock,
        "rows": rows,
        "ascii": "\n".join(ascii_rows),
    }


def _engine_available() -> bool:
    return os.path.exists(_resolve_stockfish())


def _legal_moves_payload(board: chess.Board, origin: int | None = None) -> dict:
    legal_moves = list(board.legal_moves)
    if origin is not None:
        legal_moves = [move for move in legal_moves if move.from_square == origin]

    moves = []
    for move in legal_moves:
        moves.append(
            {
                "uci": move.uci(),
                "from": chess.square_name(move.from_square),
                "to": chess.square_name(move.to_square),
                "promotion": chess.piece_symbol(move.promotion) if move.promotion else None,
            }
        )

    return {"count": len(moves), "moves": sorted(moves, key=lambda move: move["uci"])}


def _fen_list_payload(fens: List[str]) -> List[dict]:
    results = []
    for fen in sorted(fens):
        board = chess.Board(fen)
        results.append(_board_payload(board))
    return results


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def health():
    stockfish_path = _resolve_stockfish()
    return jsonify(
        {
            "ok": True,
            "stockfishPath": stockfish_path,
            "stockfishAvailable": _engine_available(),
        }
    )


@app.post("/api/new-game")
def new_game_view():
    payload = request.get_json(silent=True) or {}
    fen = str(payload.get("fen", "")).strip() or chess.STARTING_FEN
    try:
        board = _load_board(fen)
    except ValueError as exc:
        return _json_error(str(exc))

    return jsonify(
        {
            "board": _board_payload(board),
            "legalMoves": _legal_moves_payload(board),
            "engineAvailable": _engine_available(),
        }
    )


@app.post("/api/legal-moves")
def legal_moves_view():
    payload = request.get_json(silent=True) or {}
    missing = _require_fields(payload, ["fen"])
    if missing:
        return _json_error(f"Missing required field(s): {', '.join(missing)}")

    try:
        board = _load_board(payload["fen"])
        square_name = str(payload.get("square", "")).strip()
        origin = chess.parse_square(square_name) if square_name else None
    except ValueError as exc:
        return _json_error(str(exc))

    return jsonify({"fen": board.fen(), **_legal_moves_payload(board, origin)})


@app.post("/api/play-turn")
def play_turn_view():
    payload = request.get_json(silent=True) or {}
    missing = _require_fields(payload, ["fen", "move"])
    if missing:
        return _json_error(f"Missing required field(s): {', '.join(missing)}")

    engine_enabled = bool(payload.get("engineEnabled", True))
    engine_color_name = str(payload.get("engineColor", "black")).strip().lower()
    if engine_color_name not in {"white", "black"}:
        return _json_error("engineColor must be white or black.")
    engine_color = chess.WHITE if engine_color_name == "white" else chess.BLACK

    try:
        board = _load_board(payload["fen"])
        player_move = chess.Move.from_uci(str(payload["move"]).strip())
        if player_move not in board.legal_moves:
            return _json_error("Move is not legal for this position.")
        board.push(player_move)
    except ValueError as exc:
        return _json_error(str(exc))

    response = {
        "playerMove": player_move.uci(),
        "engineMove": None,
        "board": _board_payload(board),
        "legalMoves": _legal_moves_payload(board),
        "engineAvailable": _engine_available(),
    }

    if not engine_enabled or board.is_game_over() or board.turn != engine_color:
        return jsonify(response)

    stockfish_path = _resolve_stockfish()
    if not os.path.exists(stockfish_path):
        return jsonify(response)

    try:
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path, setpgrp=True)
    except Exception as exc:
        response["engineError"] = f"Unable to start Stockfish: {exc}"
        return jsonify(response)

    try:
        engine_move = _pick_move(board, engine, 0.35)
        board.push(engine_move)
        response["engineMove"] = engine_move.uci()
        response["board"] = _board_payload(board)
        response["legalMoves"] = _legal_moves_payload(board)
        return jsonify(response)
    except Exception as exc:
        response["engineError"] = f"Engine move failed: {exc}"
        return jsonify(response)
    finally:
        engine.quit()


@app.post("/api/engine-move")
def engine_move_view():
    """Ask the engine to make a move for the specified side from a given position."""
    payload = request.get_json(silent=True) or {}
    missing = _require_fields(payload, ["fen"])
    if missing:
        return _json_error(f"Missing required field(s): {', '.join(missing)}")

    engine_color_name = str(payload.get("engineColor", "white")).strip().lower()
    if engine_color_name not in {"white", "black"}:
        return _json_error("engineColor must be white or black.")
    engine_color = chess.WHITE if engine_color_name == "white" else chess.BLACK

    try:
        board = _load_board(payload["fen"])
    except ValueError as exc:
        return _json_error(str(exc))

    if board.is_game_over():
        return jsonify({"engineMove": None, "board": _board_payload(board), "legalMoves": _legal_moves_payload(board)})

    if board.turn != engine_color:
        return _json_error("It is not the engine's turn in this position.")

    stockfish_path = _resolve_stockfish()
    if not os.path.exists(stockfish_path):
        return _json_error("Stockfish not available.", status=503)

    try:
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path, setpgrp=True)
    except Exception as exc:
        return _json_error(f"Unable to start Stockfish: {exc}", status=503)

    try:
        engine_move = _pick_move(board, engine, 0.35)
        board.push(engine_move)
        return jsonify({
            "engineMove": engine_move.uci(),
            "board": _board_payload(board),
            "legalMoves": _legal_moves_payload(board),
        })
    finally:
        engine.quit()


@app.post("/api/replay")
def replay_view():
    """Replay a sequence of moves from a starting FEN and return the resulting position."""
    payload = request.get_json(silent=True) or {}
    missing = _require_fields(payload, ["fen"])
    if missing:
        return _json_error(f"Missing required field(s): {', '.join(missing)}")

    moves = payload.get("moves", [])
    if not isinstance(moves, list):
        return _json_error("moves must be a list of UCI strings.")

    try:
        board = _load_board(payload["fen"])
        for uci in moves:
            move = chess.Move.from_uci(str(uci).strip())
            if move not in board.legal_moves:
                return _json_error(f"Move {uci} is not legal in the replayed position.")
            board.push(move)
    except ValueError as exc:
        return _json_error(str(exc))

    return jsonify({"board": _board_payload(board), "legalMoves": _legal_moves_payload(board)})


@app.post("/api/board")
def board_view():
    payload = request.get_json(silent=True) or {}
    missing = _require_fields(payload, ["fen"])
    if missing:
        return _json_error(f"Missing required field(s): {', '.join(missing)}")

    try:
        board = _load_board(payload["fen"])
    except ValueError as exc:
        return _json_error(str(exc))
    return jsonify(_board_payload(board))


@app.post("/api/move")
def move_view():
    payload = request.get_json(silent=True) or {}
    missing = _require_fields(payload, ["fen", "move"])
    if missing:
        return _json_error(f"Missing required field(s): {', '.join(missing)}")

    try:
        board = _load_board(payload["fen"])
        move = chess.Move.from_uci(payload["move"].strip())
        if move != chess.Move.null() and move not in board.pseudo_legal_moves:
            return _json_error("Move is not pseudo-legal for this position.")
        board.push(move)
    except ValueError as exc:
        return _json_error(str(exc))

    return jsonify(_board_payload(board))


@app.post("/api/moves")
def moves_view():
    payload = request.get_json(silent=True) or {}
    missing = _require_fields(payload, ["fen"])
    if missing:
        return _json_error(f"Missing required field(s): {', '.join(missing)}")

    try:
        board = _load_board(payload["fen"])
    except ValueError as exc:
        return _json_error(str(exc))

    moves = [move.uci() for move in _rbc_moves(board)]
    return jsonify({"fen": board.fen(), "count": len(moves), "moves": moves})


@app.post("/api/states")
def states_view():
    payload = request.get_json(silent=True) or {}
    missing = _require_fields(payload, ["fen"])
    if missing:
        return _json_error(f"Missing required field(s): {', '.join(missing)}")

    try:
        board = _load_board(payload["fen"])
    except ValueError as exc:
        return _json_error(str(exc))

    fens = []
    for move in _rbc_moves(board):
        next_board = board.copy(stack=False)
        next_board.push(move)
        fens.append(next_board.fen())

    return jsonify({"count": len(fens), "states": _fen_list_payload(fens)})


@app.post("/api/captures")
def captures_view():
    payload = request.get_json(silent=True) or {}
    missing = _require_fields(payload, ["fen", "square"])
    if missing:
        return _json_error(f"Missing required field(s): {', '.join(missing)}")

    try:
        board = _load_board(payload["fen"])
        capture_square = chess.parse_square(payload["square"].strip())
    except ValueError as exc:
        return _json_error(str(exc))

    fens = []
    for move in _rbc_moves(board):
        if _capture_square(board, move) != capture_square:
            continue
        next_board = board.copy(stack=False)
        next_board.push(move)
        fens.append(next_board.fen())

    return jsonify({"count": len(fens), "states": _fen_list_payload(fens)})


@app.post("/api/sensing")
def sensing_view():
    payload = request.get_json(silent=True) or {}
    fens = payload.get("fens") or []
    window = str(payload.get("window", "")).strip()
    if not fens or not window:
        return _json_error("Both fens and window are required.")

    try:
        parsed_window = _parse_window(window)
        consistent = [fen for fen in fens if _matches_window(chess.Board(fen), parsed_window)]
    except ValueError as exc:
        return _json_error(str(exc))

    return jsonify({"count": len(consistent), "states": _fen_list_payload(consistent)})


@app.post("/api/select-move")
def select_move_view():
    payload = request.get_json(silent=True) or {}
    mode = str(payload.get("mode", "single")).strip().lower()
    fens = payload.get("fens") or []
    if mode not in {"single", "multiple"}:
        return _json_error("Mode must be single or multiple.")
    if mode == "single" and not str(payload.get("fen", "")).strip():
        return _json_error("fen is required for single mode.")
    if mode == "multiple" and not fens:
        return _json_error("fens is required for multiple mode.")

    stockfish_path = _resolve_stockfish()
    if not os.path.exists(stockfish_path):
        return _json_error(f"Stockfish not found at {stockfish_path}", status=503)

    try:
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path, setpgrp=True)
    except Exception as exc:
        return _json_error(f"Unable to start Stockfish: {exc}", status=503)

    try:
        if mode == "single":
            board = _load_board(payload["fen"])
            move = _pick_move(board, engine, 0.5)
            return jsonify({"move": move.uci(), "board": _board_payload(board)})

        votes = {}
        for fen in fens:
            board = chess.Board(fen)
            move = _pick_move(board, engine, 0.5).uci()
            votes[move] = votes.get(move, 0) + 1
        best = max(votes.values())
        tied = sorted(move for move, count in votes.items() if count == best)
        return jsonify({"move": tied[0], "votes": votes, "count": len(fens)})
    except ValueError as exc:
        return _json_error(str(exc))
    finally:
        engine.quit()


if __name__ == "__main__":
    app.run(debug=True)