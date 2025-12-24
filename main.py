from fastapi import FastAPI

app = FastAPI(title="FastAPI SQLMap Manager")

@app.get("/")
def root():
    return {"status": "running"}
