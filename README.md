# AI 记账小程序

基于 FastAPI + PostgreSQL + Vue 3 的 AI 智能记账应用，支持小票图片 AI 识别。

## 功能特性

- 🔐 **用户认证** - JWT 令牌认证，支持注册/登录
- 💼 **账户管理** - 多账户支持（银行卡、支付宝、微信、现金等）
- 📂 **分类管理** - 支出/收入分类，支持自定义
- 📝 **记录管理** - 手动记账 + AI 截图识别记账
- 🤖 **AI 识别** - Qwen3.5-plus 视觉理解自动识别收据
- ⏳ **待确认流程** - AI 置信度低时进入待确认列表
- 📊 **统计报表** - 月度统计、分类占比、趋势分析
- 📤 **数据导出** - 支持 CSV/JSON 格式导出
- 🔄 **转账功能** - 账户间资金转移

## 快速开始

### 1. 环境要求

- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose（可选）

### 2. 本地开发

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 复制环境变量
cp .env.example .env
# 编辑 .env 填入你的配置

# 创建数据库（PostgreSQL）
createdb accounting

# 运行服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Docker 部署

```bash
# 在项目根目录
cd ~/projects/accounting-ai

# 复制环境变量并编辑（必须填入 QWEN_API_KEY）
cp .env.example .env

# 启动所有服务（db + backend + frontend）
docker compose up --build -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f backend
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL 连接字符串 | postgresql://postgres:postgres@localhost:5432/accounting |
| `SECRET_KEY` | JWT 密钥（生产环境必须修改） | - |
| `QWEN_API_KEY` | Qwen API 密钥 | - |
| `QWEN_API_BASE` | Qwen API 地址 | https://dashscope.aliyuncs.com/compatible-mode/v1 |
| `QWEN_MODEL` | Qwen 视觉模型 | qwen-vl-plus |
| `AI_CONFIDENCE_THRESHOLD` | AI 自动确认阈值 | 0.85 |

## API 接口

### 认证
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取当前用户

### 账户
- `GET /api/v1/wallets` - 获取账户列表
- `POST /api/v1/wallets` - 创建账户
- `PUT /api/v1/wallets/{id}` - 更新账户
- `DELETE /api/v1/wallets/{id}` - 删除账户
- `POST /api/v1/wallets/transfer` - 转账

### 分类
- `GET /api/v1/categories` - 获取分类列表
- `POST /api/v1/categories` - 创建分类
- `PUT /api/v1/categories/{id}` - 更新分类
- `DELETE /api/v1/categories/{id}` - 删除分类

### 记录
- `GET /api/v1/records` - 获取记录列表
- `POST /api/v1/records` - 创建记录
- `GET /api/v1/records/pending` - 获取待确认记录
- `POST /api/v1/records/{id}/confirm` - 确认记录
- `POST /api/v1/records/{id}/reject` - 拒绝记录
- `GET /api/v1/records/export` - 导出记录

### AI 识别
- `POST /api/v1/ai/recognize` - 上传小票图片，异步识别（立即返回 job_id）
- `GET /api/v1/ai/recognize/{job_id}` - 轮询识别任务状态和结果
- `GET /api/v1/ai/jobs` - 列出当前用户所有识别记录
- `GET /api/v1/ai/jobs/{job_id}` - 查看识别记录详情

### 统计
- `GET /api/v1/stats/monthly` - 月度统计
- `GET /api/v1/stats/category-breakdown` - 分类占比
- `GET /api/v1/stats/trend` - 趋势分析

## 项目结构

```
.
├── docker-compose.yml        # 全栈 Docker 部署
├── .env.example              # 环境变量模板
├── backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── api/              # API 路由
│   │   │   ├── auth.py
│   │   │   ├── wallets.py
│   │   │   ├── categories.py
│   │   │   ├── records.py
│   │   │   ├── ai.py
│   │   │   ├── stats.py
│   │   │   └── export.py
│   │   ├── core/             # 核心配置
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── models/           # 数据库模型
│   │   ├── schemas/          # Pydantic 模型
│   │   ├── services/         # 业务服务
│   │   │   └── ai_service.py
│   │   ├── database.py
│   │   └── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
└── frontend/                 # Vue 3 前端
    ├── src/
    │   ├── api/              # API 调用层（axios）
    │   ├── views/            # 页面组件
    │   ├── stores/           # Pinia 状态管理
    │   └── router/           # Vue Router 配置
    ├── e2e/                  # Playwright E2E 测试
    │   └── test_e2e.py
    ├── Dockerfile            # 多阶段构建（Node → nginx）
    └── nginx.conf            # SPA 反向代理配置
```

## 数据库模型

```
User ─┬─ Wallet (账户)
      ├─ Category (分类)
      └─ Record (消费/收入记录)
```

## 后续开发

- [x] 前端 Web
- [ ] 前端小程序
- [ ] iOS Shortcuts 集成
- [ ] 预算提醒功能
- [ ] WebSocket 实时通知
