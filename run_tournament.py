"""
Double round-robin tournament:
  RandomSensing vs ImprovedAgent vs RandomBot vs TroutBot
Each pair plays twice (once as white, once as black).
Results saved to tournament_results.json
"""
import sys, os, json, subprocess

PY = sys.executable
HERE = os.path.dirname(os.path.abspath(__file__))
RUNNER = os.path.join(HERE, "run_single_game.py")

NAMES = ["RandomSensing", "ImprovedAgent", "RandomBot", "TroutBot"]
results = {n: {"wins": 0, "losses": 0, "draws": 0, "points": 0.0} for n in NAMES}
game_log = []

fixtures = [
    ("RandomSensing", "RandomBot"),
    ("RandomSensing", "TroutBot"),
    ("ImprovedAgent", "RandomBot"),
    ("ImprovedAgent", "TroutBot"),
]
total = len(fixtures) * 2
done = 0

for white_name, black_name in fixtures:
    for (wn, bn) in [(white_name, black_name), (black_name, white_name)]:
        done += 1
        print(f"[{done}/{total}] {wn} (W) vs {bn} (B) ...", end=" ", flush=True)
        try:
            proc = subprocess.run(
                [PY, RUNNER, wn, bn],
                cwd=HERE,
                capture_output=True,
                text=True,
                timeout=180,
            )
            # Find JSON line in stdout (last non-empty line)
            lines = [l.strip() for l in proc.stdout.splitlines() if l.strip()]
            result_line = next((l for l in reversed(lines) if l.startswith("{")), None)
            if result_line is None:
                raise RuntimeError(proc.stderr[-500:] if proc.stderr else "no output")
            g = json.loads(result_line)
        except Exception as e:
            print(f"ERROR: {e}")
            game_log.append({"white": wn, "black": bn, "winner": None, "reason": str(e)})
            continue

        winner = g["winner"]
        reason  = g["reason"]
        if winner == "draw":
            results[wn]["draws"] += 1
            results[bn]["draws"] += 1
            results[wn]["points"] += 0.5
            results[bn]["points"] += 0.5
            outcome = "DRAW"
        elif winner == wn:
            results[wn]["wins"] += 1
            results[bn]["losses"] += 1
            results[wn]["points"] += 1
            outcome = f"{wn} wins"
        else:
            results[bn]["wins"] += 1
            results[wn]["losses"] += 1
            results[bn]["points"] += 1
            outcome = f"{bn} wins"

        print(f"{outcome} ({reason})")
        game_log.append({"white": wn, "black": bn, "winner": outcome, "reason": reason})

print("\n=== FINAL STANDINGS ===")
standings = sorted(NAMES, key=lambda n: results[n]["points"], reverse=True)
for rank, name in enumerate(standings, 1):
    r = results[name]
    print(f"{rank}. {name:20s}  W={r['wins']} L={r['losses']} D={r['draws']}  Pts={r['points']:.1f}")

with open(os.path.join(HERE, "tournament_results.json"), "w") as f:
    json.dump({"standings": results, "games": game_log}, f, indent=2)
print("\nResults saved to tournament_results.json")
