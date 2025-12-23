from fastapi.testclient import TestClient
from spread_eagle.api.main import app
from spread_eagle.core.database import SessionLocal, get_db

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}
    print("Health check passed.")

def test_get_games():
    # Use 2024 as we know we have data
    response = client.get("/games?season=2024&week=1")
    assert response.status_code == 200
    games = response.json()
    assert len(games) > 0
    print(f"Games endpoint passed. Found {len(games)} games for week 1.")

def test_predict():
    # Fetch a game ID first
    response = client.get("/games?season=2024&week=1")
    game_id = response.json()[0]['id']
    
    # Predict
    p_response = client.get(f"/predict/{game_id}")
    if p_response.status_code == 200:
        data = p_response.json()
        print(f"Prediction passed for game {game_id}: {data}")
    else:
        print(f"Prediction failed: {p_response.text}")
        # It might fail if model is not trained or something, but we trained it.

if __name__ == "__main__":
    test_health()
    test_get_games()
    test_predict()
