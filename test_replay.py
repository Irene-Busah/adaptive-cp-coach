import os
import json
from fastapi.testclient import TestClient
from server.daemon import app, CACHE_FILE
from typer.testing import CliRunner
from cli import app as cli_app

client = TestClient(app)
runner = CliRunner()

def test_daemon_store():
    print("Testing /store-request endpoint...")
    payload = {
        "method": "GET",
        "url": "https://jsonplaceholder.typicode.com/todos/1",
        "headers": {"Accept": "application/json"},
        "body": {}
    }
    response = client.post("/store-request", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "stored"
    
    assert os.path.exists(CACHE_FILE)
    with open(CACHE_FILE, "r") as f:
        saved = json.load(f)
        assert saved["url"] == payload["url"]
    print("Daemom store test passed!")

def test_cli_replay():
    print("Testing CLI replay command...")
    result = runner.invoke(cli_app, ["replay"])
    assert result.exit_code == 0
    assert "Replaying: GET https://jsonplaceholder.typicode.com/todos/1" in result.stdout
    assert "Status: 200" in result.stdout, f"Output was: {result.stdout}"
    assert "userId" in result.stdout
    print("CLI replay test passed!")
    
if __name__ == "__main__":
    test_daemon_store()
    test_cli_replay()
    print("All tests passed successfully! The CLI is fully functional.")
