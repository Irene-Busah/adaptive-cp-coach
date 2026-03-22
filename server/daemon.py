from fastapi import FastAPI, Request
import json
import uvicorn
import os

app = FastAPI(title="DevToolbox Local Daemon")

CACHE_FILE = "/tmp/dev_toolbox_last_request.json"

@app.post("/store-request")
async def store_request(request: Request):
    """
    Stores the incoming request data (URL, headers, body) to be replayed later.
    Expected to be hit by a browser extension.
    """
    data = await request.json()
    
    # data should look like {"method": "POST", "url": "...", "headers": {...}, "body": {...}}
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)
        
    return {"status": "stored", "cache": CACHE_FILE}

@app.get("/health")
def health():
    return {"status": "ok"}

def run_daemon():
    print("Starting DevToolbox Daemon on http://localhost:9999...")
    uvicorn.run(app, host="127.0.0.1", port=9999)

if __name__ == "__main__":
    run_daemon()
