# Image-management-website
这是我的《BS体系软件设计》课程的期末大程，一个图片管理网站（demo）。
以下是该项目使用的技术栈：

- 后端：Python + Django + Django REST Framework
- 图片处理：Pillow（生成缩略图）
- 前端：Vue 3 + Vite
- 容器化：Docker + docker-compose

目录结构：

- backend/  （Django 项目）
- frontend/ （Vue 3 项目）
- docker-compose.yml

如何运行（开发模式）：

1. 使用 Docker Compose 启动（会在容器内自动 migrate）：
```bash
	docker-compose up --build
```

2. 或者 **后端 + 前端** 本地运行：
后端：
```bash
	cd backend
	pip install -r requirements.txt 
	python manage.py makemigrations && python manage.py migrate
	python manage.py init_admin # create admin
	python manage.py runserver 0.0.0.0:8000
``` 
后端页面：`http://localhost:8000` 
前端：
```bash
	cd frontend
	npm install
	npm run dev
```
前端页面：`打开：http://localhost:5173`

3. 自己创建 venv

创建并激活 venv：
```bash
	cd e:\Codebase\Image-management-website\backend
	py -m venv .venv
	.\.venv\Scripts\Activate.ps1
```
安装依赖：
```bash
pip install -r requirements.txt
```

然后运行同上：
```bash
	cd backend
	python migrate
	python init_admin # 创建管理员
	python runserver 0.0.0.0:8000
``` 

如果 images 里已经有图片文件：`python sync_images`