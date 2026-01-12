# FastAPI-SQLMap 扫描任务管理系统项目说明

## 项目概述
本项目是基于 FastAPI + Celery 构建的分布式 SQL 注入扫描任务管理系统(管理员端暂未实现。还没有加鉴权)，主要实现以下核心功能：

-  自动化调度 SQLMap 进行漏洞扫描
-  任务状态跟踪与结果可视化
-  扫描日志实时采集与分析
-  基于 Celery 的异步任务队列管理

## 技术栈说明
| 组件              | 用途说明                          |
|-------------------|---------------------------------|
| FastAPI           | REST API 接口开发框架            |
| Celery + Redis    | 分布式任务队列与消息中间件        |
| PostgreSQL        | 扫描结果与任务日志存储            |
| SQLAlchemy        | 异步/同步 ORM 数据库操作          |
| SQLMap API        | 集成 SQLMap 扫描引擎             |
| uv                | 项目依赖管理工具                  |

## 项目目录结构
```text
app/
├── apis/        # API 路由定义（Router）
├── core/        # 核心业务逻辑与公共工具
├── database/    # 数据库连接与会话管理
├── middleware/  # 中间件配置（含 Celery、鉴权等）
├── models/      # ORM 数据库模型
├── schema/      # Pydantic 数据校验模型
└── tasks/       # Celery 异步任务定义  
```

## 核心模块说明

### 1. 任务调度中心 (tasks/)
- `sqlmap_worker.py`：实现 Celery 任务队列管理
- `sqlmap_scheduler.py`：定时轮询任务状态
- 功能亮点：
  - 自动重试机制
  - SQLMap 日志实时采集
  - 扫描结果标准化处理

### 2. 数据库管理 (database/)
- 双引擎配置：
  - 异步接口：`database.py` (FastAPI 使用)
  - 同步接口：`celery_sync_database.py` (Celery 使用)


### 3. API 接口层 (apis/)

## 典型 API 接口示例
| 端点                        | 方法   | 功能说明       |
|-----------------------------|--------|-----------------|
| `/sqlmap/scan`               | POST   | 创建新的扫描任务|
| `/sqlmap/tasks/{task_id}`    | GET    | 获取指定任务状态|
| `/sqlmap/tasks/{task_id}/log`| GET    | 获取任务执行日志|

> 💡 提示：项目使用 `uv` 作为包管理工具，依赖安装命令为 `uv add [package-name]`