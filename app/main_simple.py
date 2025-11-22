"""
简化的Magento-CJ Dropshipping 中台服务主应用
"""
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# 创建FastAPI应用
app = FastAPI(
    title="Magento-CJ Middleware API",
    description="Magento 2 与 CJ Dropshipping 集成中台服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 模板和静态文件
templates = Jinja2Templates(directory="app/templates")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 健康检查端点
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "服务正常运行"}

# Web界面路由
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 测试端点
@app.get("/api/test")
async def test_api():
    return {"message": "API正常工作", "status": "success"}

# 产品同步测试端点
@app.post("/api/sync/product")
async def sync_product():
    return {
        "message": "产品同步功能",
        "status": "success",
        "note": "这是简化版本，实际同步功能需要完整配置"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    ) 