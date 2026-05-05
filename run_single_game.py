"""
Run a single RBC game between two named agents and print the JSON result.
Usage: python run_single_game.py <WhiteAgent> <BlackAgent>
"""
import sys, os, json, random
sys.path.insert(0, os.path.dirname(__file__))

# TroutBot needs STOCKFISH_EXECUTABLE in the environment
_sf = r"C:\Users\nkosi\AppData\Local\Microsoft\WinGet\Links\stockfish.exe"
if os.path.exists(_sf):
    os.environ.setdefault("STOCKFISH_EXECUTABLE", _sf)

import chess
from reconchess import play_local_game
from reconchess.bots.random_bot import RandomBot
from reconchess.bots.trout_bot import TroutBot
from Part4_Baseline_RandomSensingAgent import RandomSensingAgent, _pick_move
from Part4_Improved_ImprovedAgent import ImprovedAgent

MAX_STATES = 25

class FastRandom(RandomSensingAgent):
    def choose_move(self, move_actions, seconds_left):
        if len(self.possible_fens) > MAX_STATES:
            self.possible_fens = set(random.sample(list(self.possible_fens), MAX_STATES))
        return super().choose_move(move_actions, seconds_left)

class FastImproved(ImprovedAgent):
    def choose_move(self, move_actions, seconds_left):
        if not move_actions:
            return None
        if len(self.possible_fens) > MAX_STATES:
            self.possible_fens = set(random.sample(list(self.possible_fens), MAX_STATES))
        # Use a small fixed time per state so we never exceed the clock
        from collections import Counter
        legal = set(move_actions)
        votes: Counter = Counter()
        secs = 0.05  # 0.05s x 25 states = 1.25s per turn, well within budget
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

AGENTS = {
    "RandomSensing": FastRandom,
    "ImprovedAgent": FastImproved,
    "RandomBot":     RandomBot,
    "TroutBot":      TroutBot,
}

def main():
    wn, bn = sys.argv[1], sys.argv[2]
    white = AGENTS[wn]()
    black = AGENTS[bn]()
    winner_color, win_reason, _ = play_local_game(
        white_player=white,
        black_player=black,
        seconds_per_player=300,
    )
    if winner_color is None:
        winner = "draw"
    elif winner_color == chess.WHITE:
        winner = wn
    else:
        winner = bn
    reason = win_reason.name if win_reason else "unknown"
    print(json.dumps({"white": wn, "black": bn, "winner": winner, "reason": reason}))

if __name__ == "__main__":
    main()
