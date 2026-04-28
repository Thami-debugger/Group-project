import requests

base_url = "http://127.0.0.1:5000/api"


    try:
        # 1. New Game
        print('Testing /api/new-game...')
        ng_res = requests.post(f"{base_url}/new-game", json={})
        print(f"Status: {ng_res.status_code}")
        if ng_res.status_code != 200: return
        game_data = ng_res.json()
        # Try both possible FEN keys
        start_fen = game_data.get("fen") or game_data.get("board", {}).get("fen")
        print(f"FEN: {start_fen}")

        # 2. Play Turn
        print('\nTesting /api/play-turn (e2e4)...')
        pt_res = requests.post(f"{base_url}/play-turn", json={
            "fen": start_fen,
            "move": "e2e4",
            "engineEnabled": True,
            "engineColor": "black"
        })
        print(f"Status: {pt_res.status_code}")
        pt_data = pt_res.json() if pt_res.status_code == 200 else {}
        print(f"  playerMove: {pt_data.get('playerMove')}")
        print(f"  engineMove: {pt_data.get('engineMove')}")
        print(f"  turn: {pt_data.get('board', {}).get('turn')}")
        print(f"  result: {pt_data.get('board', {}).get('result')}")

        # 3. Replay
        print('\nTesting /api/replay...')
        rp_res = requests.post(f"{base_url}/replay", json={
            "fen": start_fen,
            "moves": ["e2e4"]
        })
        print(f"Status: {rp_res.status_code}")
        rp_data = rp_res.json() if rp_res.status_code == 200 else {}
        print(f"  turn: {rp_data.get('board', {}).get('turn')}")
        print(f"  result: {rp_data.get('board', {}).get('result')}")

        # 4. Engine Move
        print('\nTesting /api/engine-move...')
        em_res = requests.post(f"{base_url}/engine-move", json={
            "fen": start_fen,
            "engineColor": "white"
        })
        print(f"Status: {em_res.status_code}")
        em_data = em_res.json() if em_res.status_code == 200 else {}
        print(f"  engineMove: {em_data.get('engineMove')}")
        print(f"  turn: {em_data.get('board', {}).get('turn')}")
        print(f"  result: {em_data.get('board', {}).get('result')}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_endpoints()
        ng_res = requests.post(f'{base_url}/new-game', json={})
