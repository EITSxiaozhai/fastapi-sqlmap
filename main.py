from fastapi import FastAPI
from app.apis.sqlmap import router as sqlmap_router
from app.apis.admin import router as admin_router
from app.apis.db_health import router as db_router

app = FastAPI(title="FastAPI SQLMap Manager")

app.include_router(sqlmap_router)
app.include_router(admin_router)
app.include_router(db_router)

@app.get("/")
def root():
    return {"status": "running"}
