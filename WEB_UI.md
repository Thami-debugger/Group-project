# RBC Visualizer

This folder now includes a small local web app for visualizing the assignment logic in Parts 1, 2, and 3.

## Install

```powershell
pip install -r requirements.txt
```

## Run

```powershell
python app.py
```

Open http://127.0.0.1:5000 in your browser.

## What it includes

- Click-to-play board mode from the browser
- Part 1.1 board rendering from a FEN string
- Part 1.2 move execution and live board update
- Part 2.1 next move generation
- Part 2.2 next state generation
- Part 2.3 capture-based state filtering
- Part 2.4 sensing-window filtering across candidate states
- Part 3 single-board and multi-board move selection

## Notes

- Part 3 still depends on a working Stockfish binary.
- The app uses the same Python logic already present in `part2.py` and `part3.py`.
- In play mode, you start from a FEN, click a white piece, then click a highlighted destination square.