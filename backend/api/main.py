from fastapi import FastAPI

app = FastAPI(
    title="SaaS Stock Deposit Control API",
    description="Backend API for the SaaS Stock Deposit Control system.",
    version="1.0.0",
)

@app.get("/health")
async def health():
    """
    Asynchronous health check endpoint returning a 200 OK response.
    """
    return {
        "status": "ok",
        "message": "Service is healthy",
    }
