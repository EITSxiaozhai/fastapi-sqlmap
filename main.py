from fastapi import FastAPI
from app.apis.sqlmap_api import router as sqlmap_router
from app.apis.admin_api import router as admin_router
from app.apis.db_health import router as db_router
from app.middleware.celery_app import celery_app

app = FastAPI(title="FastAPI SQLMap Manager")

app.include_router(sqlmap_router)
app.include_router(admin_router)
app.include_router(db_router)


@app.get("/")
def root():
    print("BROKER =", celery_app.conf.broker_url)
    return {"status": "running"}
