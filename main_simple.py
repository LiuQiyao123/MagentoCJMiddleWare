import uvicorn
from fastapi import FastAPI

app = FastAPI(title="Magento-CJ Middleware API")

@app.get("/")
async def root():
    return {"message": "API正常运行", "status": "success"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
