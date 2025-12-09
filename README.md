# Image-management-website

这是一个演示用的图片管理网站（demo），使用的技术栈：

- 后端：Python + Django + Django REST Framework
- 图片处理：Pillow（生成缩略图）
- 前端：Vue 3 + Vite
- 容器化：Docker + docker-compose

目录结构（将会添加）：

- backend/  （Django 项目）
- frontend/ （Vue 3 项目）
- docker-compose.yml

如何运行（开发模式）：

1. 使用 Docker Compose 启动（会在容器内自动 migrate）：

	docker-compose up --build

2. 后端: http://localhost:8000
	前端: http://localhost:5173

这是我的《BS体系软件设计》课程的期末大程。
