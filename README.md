# FastAPI-SQLMap 扫描服务

基于FastAPI的分布式SQL注入扫描服务，整合SQLMap API和Celery任务队列，提供RESTful接口管理扫描任务。

## 技术栈
- **Web框架**: FastAPI 
- **任务队列**: Celery + RabbitMQ + Redis
- **数据库**: PostgreSQL（异步SQLAlchemy ORM）
- **包管理**: UV (Python 3.12)

# SQLMAP
需要自备一个sqlmap的docker容器。以API模式启动