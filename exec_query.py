import requests
base_url = "http://127.0.0.1:5000/api"
def run_test():
    try:
        ng_res = requests.post(f"{base_url}/new-game", json={})
        if ng_res.status_code != 200:
            print(f"New game failed: {ng_res.status_code}")
            return
        start_fen = ng_res.json().get("fen")
        pt_res = requests.post(f"{base_url}/play-turn", json={
            "fen": start_fen,
            "move": "e2e4",
            "engineEnabled": True,
            "engineColor": "black"
        })
        print(f"Status Code: {pt_res.status_code}")
        if pt_res.status_code == 200:
            data = pt_res.json()
            print(f"playerMove: {data.get('playerMove')}")
            print(f"engineMove: {data.get('engineMove')}")
            print(f"engineError: {data.get('engineError')}")
            print(f"board.turn: {data.get('board', {}).get('turn')}")
        else:
            print(pt_res.text)
    except Exception as e:
        print(f"Error: {e}")
if __name__ == '__main__':
    run_test()
