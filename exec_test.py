import requests

base_url = "http://127.0.0.1:5000/api"

def run_test():
    try:
        # 1. New game
        ng = requests.post(f"{base_url}/new-game", json={}).json()
        start_fen = ng["board"]["fen"]
        
        # 2. Play turn WITH engine
        payload1 = {"fen": start_fen, "move": "e2e4", "engineEnabled": True, "engineColor": "black"}
        res1 = requests.post(f"{base_url}/play-turn", json=payload1)
        data1 = res1.json() if res1.status_code == 200 else {}
        print(f"Test 1 (Engine ON):")
        print(f"Status: {res1.status_code}")
        print(f"playerMove: {data1.get('playerMove')}")
        print(f"engineMove: {data1.get('engineMove')}")
        print(f"engineError: {data1.get('engineError')}")
        print(f"board.turn: {data1.get('board', {}).get('turn')}")
        
        # 3. Play turn WITHOUT engine
        payload2 = {"fen": start_fen, "move": "e2e4", "engineEnabled": False, "engineColor": "black"}
        res2 = requests.post(f"{base_url}/play-turn", json=payload2)
        data2 = res2.json() if res2.status_code == 200 else {}
        print(f"\nTest 2 (Engine OFF):")
        print(f"Status: {res2.status_code}")
        print(f"board.turn: {data2.get('board', {}).get('turn')}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_test()
