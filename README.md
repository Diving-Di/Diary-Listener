# Diary Listener

Diary Listener 是一个图片日记 / 图片管理网站 demo，用于上传、浏览和管理个人图片。项目支持用户注册登录、图片缩略图生成、EXIF 信息提取、标签管理、AI 图片打标、按标签筛选图片以及自定义轮播展示。

## 技术栈

- 后端：Python、Django、Django REST Framework
- 数据库：MySQL 8.0
- 图片处理：Pillow
- 前端：React、TypeScript、Vite、Ant Design
- 容器化：Docker、Docker Compose

## 功能

- 用户注册、登录和退出
- 图片上传、删除和列表展示
- 上传后自动生成缩略图
- 自动读取图片 EXIF 信息，包括拍摄时间、分辨率和 GPS 坐标
- 根据 EXIF 信息生成自动标签
- 支持自定义标签和标签筛选
- 支持调用通义千问视觉模型生成 AI 标签
- 支持选择图片加入首页轮播

## 目录结构

```text
.
├── backend/             # Django 后端
├── frontend/            # React + TypeScript 前端
├── docker-compose.yml   # 本地容器编排
└── README.md
```

## 快速启动

### 使用 Docker Compose

项目会启动 MySQL、Django 后端和 Vite 前端。后端容器启动时会自动执行迁移。

```bash
docker-compose up --build
```

启动后访问：

- 前端：http://localhost:5173
- 后端：http://localhost:8000
- API：http://localhost:8000/api/

### 本地开发启动

先启动后端：

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Windows PowerShell 激活虚拟环境：

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

再启动前端：

```bash
cd frontend
npm install
npm run dev
```

前端默认访问地址：

```text
http://localhost:5173
```

## AI 打标配置

AI 打标默认使用通义千问视觉模型。可以在 `backend/.env` 中配置，也可以参考 `backend/.env.example`。

```env
AI_TAGGING_PROVIDER=qwen
AI_VISION_API_KEY=<你的通义千问 API Key>
AI_VISION_MODEL=qwen-vl-max
AI_VISION_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
```

未配置 `AI_VISION_API_KEY` 时，普通图片上传、浏览和标签管理仍可使用，但 AI 打标接口会返回配置缺失错误。

## 常用命令

后端数据库迁移：

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

创建管理员账号：

```bash
cd backend
python manage.py createsuperuser
```

前端构建：

```bash
cd frontend
npm run build
```

## 远程仓库

```text
https://github.com/Diving-Di/Diary-Listener.git
```
