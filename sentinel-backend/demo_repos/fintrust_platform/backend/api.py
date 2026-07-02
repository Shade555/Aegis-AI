import requests
from fastapi import FastAPI

app = FastAPI()


@app.get("/fetch")
def fetch_url(url: str):
    # SSRF
    return requests.get(url).content
