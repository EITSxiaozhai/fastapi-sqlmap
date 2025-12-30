from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

db_password = os.getenv("REDIS_DB_PASSWORD")
redis_host = os.getenv("REDIS_DB_HOSTNAME")
redis_port = os.getenv("REDIS_DB_PORT")
redis_db = os.getenv("REDIS_DB_NAME")
redis_user = os.getenv("REDIS_USER_NAME")
mq_password = os.getenv("MQ_USERPASSWORD")
mq_username = os.getenv("MQ_USERNAME")
mq_host = os.getenv("MQ_HOSTNAME")
mq_dbname = os.getenv("MQ_DBNAME")
mq_port = os.getenv("MQ_DBPORT")


celery_app = Celery(
    "fastapi_sqlmap",
    broker=f"amqp://{mq_username}:{mq_password}@{mq_host}:{mq_port}/{mq_dbname}",
    backend=f"redis://:{db_password}@{redis_host}:{redis_port}/{redis_db}",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=False,
)
