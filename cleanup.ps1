Write-Host "正在清理项目..." -ForegroundColor Cyan

# 1. 清理 Python 缓存 (__pycache__, .pyc)
Get-ChildItem -Path . -Include __pycache__ -Recurse -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Include *.pyc -Recurse -File | Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "Python 缓存已清理" -ForegroundColor Green

# 2. 清理前端依赖 (node_modules) 和构建产物 (dist)
if (Test-Path "frontend/node_modules") { 
    Write-Host "正在删除 frontend/node_modules (可能需要一点时间)..."
    Remove-Item -Path "frontend/node_modules" -Recurse -Force -ErrorAction SilentlyContinue 
}
if (Test-Path "frontend/dist") { Remove-Item -Path "frontend/dist" -Recurse -Force -ErrorAction SilentlyContinue }
Write-Host "前端依赖已清理" -ForegroundColor Green

# 3. 清理 Python 虚拟环境 (image-management)
if (Test-Path "image-management") { 
    Write-Host "正在删除虚拟环境..."
    Remove-Item -Path "image-management" -Recurse -Force -ErrorAction SilentlyContinue 
}
Write-Host "虚拟环境已清理" -ForegroundColor Green

# 4. 清理本地数据库 (db.sqlite3)
if (Test-Path "backend/db.sqlite3") { Remove-Item -Path "backend/db.sqlite3" -Force -ErrorAction SilentlyContinue }
Write-Host "数据库文件已清理" -ForegroundColor Green

# 5. 清理上传的媒体文件 (backend/media)
# 保留 media 目录结构，但删除里面的图片和缩略图
if (Test-Path "backend/media/images") { 
    Get-ChildItem -Path "backend/media/images" -Recurse | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}
if (Test-Path "backend/media/thumbnails") { 
    Get-ChildItem -Path "backend/media/thumbnails" -Recurse | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Host "媒体文件已清理" -ForegroundColor Green

# 6. 清理敏感配置 (.env)
if (Test-Path "backend/.env") { Remove-Item -Path "backend/.env" -Force -ErrorAction SilentlyContinue }
Write-Host "配置文件(.env)已清理" -ForegroundColor Green

Write-Host "清理完成！现在可以打包了。" -ForegroundColor Cyan