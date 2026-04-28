import requests

base_url = "http://127.0.0.1:5000/api"

def run_test():
    try:
        # 1. New Game
        ng_res = requests.post(f"{base_url}/new-game", json={})
        print(f"New Game: {ng_res.status_code}")
        if ng_res.status_code != 200: return
        start_fen = ng_res.json()["board"]["fen"]

        # 2. Play Turn
        pt_res = requests.post(f"{base_url}/play-turn", json={
            "fen": start_fen,
            "move": "e2e4",
            "engineEnabled": True,
            "engineColor": "black"
        })
        pt_data = pt_res.json() if pt_res.status_code == 200 else {}
        print(f"Play Turn: {pt_res.status_code}")
        print(f"  playerMove: {pt_data.get('playerMove')}")
        print(f"  engineMove: {pt_data.get('engineMove')}")
        print(f"  turn: {pt_data.get('board', {}).get('turn')}")
        print(f"  result: {pt_data.get('board', {}).get('result')}")

        # 3. Replay
        rp_res = requests.post(f"{base_url}/replay", json={
            "fen": start_fen,
            "moves": ["e2e4"]
        })
        rp_data = rp_res.json() if rp_res.status_code == 200 else {}
        print(f"Replay: {rp_res.status_code}")
        print(f"  turn: {rp_data.get('board', {}).get('turn')}")
        print(f"  result: {rp_data.get('board', {}).get('result')}")

        # 4. Engine Move
        em_res = requests.post(f"{base_url}/engine-move", json={
            "fen": start_fen,
            "engineColor": "white"
        })
        em_data = em_res.json() if em_res.status_code == 200 else {}
        print(f"Engine Move: {em_res.status_code}")
        print(f"  engineMove: {em_data.get('engineMove')}")
        print(f"  turn: {em_data.get('board', {}).get('turn')}")
        print(f"  result: {em_data.get('board', {}).get('result')}")

    except Exception as e:
        print(f"Error: {e}")

run_test()
