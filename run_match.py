"""
Quick local match: RandomSensingAgent (White) vs RandomSensingAgent (Black).
Run from RBC/solution:
    python run_match.py

Wraps both agents to print live turn-by-turn progress and caps possible FENs
at MAX_STATES for speed.
"""
import sys
import os
import random
sys.path.insert(0, os.path.dirname(__file__))

import chess
from reconchess import play_local_game, WinReason
from reconchess.history import Turn

from Part4_Baseline_RandomSensingAgent import RandomSensingAgent

MAX_STATES = 500   # cap possible FENs for speed; lower = faster but less accurate


class VerboseAgent(RandomSensingAgent):
    """RandomSensingAgent with live per-turn output and a tighter FEN cap."""

    def __init__(self, label: str) -> None:
        super().__init__()
        self.label = label
        self._turn = 0

    def choose_move(self, move_actions, seconds_left):
        # Cap states for speed
        if len(self.possible_fens) > MAX_STATES:
            self.possible_fens = set(random.sample(list(self.possible_fens), MAX_STATES))

        self._turn += 1
        move = super().choose_move(move_actions, seconds_left)
        print(f"  [{self.label}] turn {self._turn:3d} | "
              f"states={len(self.possible_fens):5d} | "
              f"move={move.uci() if move else 'null'} | "
              f"time_left={seconds_left:.0f}s")
        return move


def main():
    white = VerboseAgent("White")
    black = VerboseAgent("Black")

    print("=" * 60)
    print("  RandomSensingAgent (White) vs RandomSensingAgent (Black)")
    print(f"  (possible-states capped at {MAX_STATES} per agent for speed)")
    print("=" * 60)

    winner_color, win_reason, history = play_local_game(
        white_player=white,
        black_player=black,
        seconds_per_player=300,
    )

    print("\n" + "=" * 60)
    if winner_color is None:
        print("  Result: DRAW")
    else:
        winner_name = "White" if winner_color == chess.WHITE else "Black"
        reason = win_reason.value if win_reason else "unknown"
        print(f"  Winner : {winner_name} (RandomSensingAgent)")
        print(f"  Reason : {reason}")
    print("=" * 60)

    # Print final true board
    try:
        black_turns = len(history._fens_after_move[chess.BLACK])
        white_turns = len(history._fens_after_move[chess.WHITE])
        if black_turns > 0:
            last = Turn(chess.BLACK, black_turns - 1)
        else:
            last = Turn(chess.WHITE, white_turns - 1)
        print("\nFinal board (true state):")
        print(history.truth_board_after_move(last))
    except Exception as exc:
        print(f"(Could not print final board: {exc})")


if __name__ == "__main__":
    main()
