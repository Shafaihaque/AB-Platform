from fastapi import FastAPI

app = FastAPI(title="AB Platform API")


@app.get("/health")
def health():
    return {"status": "ok", "service": "api"}
