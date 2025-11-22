#!/usr/bin/env python3
"""
Magento-CJ Middleware 启动脚本
"""
import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=3000,
        reload=True,
        log_level="info"
    ) 