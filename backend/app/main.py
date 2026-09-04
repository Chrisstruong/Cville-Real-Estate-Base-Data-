from fastapi import FastAPI

app = FastAPI(
    title = "Charlottesville Real Estate AI API"
)

@app.get("/health")
async def health():
    return {"status": "healthy"}