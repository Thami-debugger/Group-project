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
from Part4_Baseline_RandomSensingAgent import RandomSensingAgent
from Part4_Improved_ImprovedAgent import ImprovedAgent

MAX_STATES = 25

class FastRandom(RandomSensingAgent):
    def choose_move(self, move_actions, seconds_left):
        if len(self.possible_fens) > MAX_STATES:
            self.possible_fens = set(random.sample(list(self.possible_fens), MAX_STATES))
        return super().choose_move(move_actions, seconds_left)

class FastImproved(ImprovedAgent):
    def choose_move(self, move_actions, seconds_left):
        if len(self.possible_fens) > MAX_STATES:
            self.possible_fens = set(random.sample(list(self.possible_fens), MAX_STATES))
        return super().choose_move(move_actions, seconds_left)

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
        seconds_per_player=60,
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
