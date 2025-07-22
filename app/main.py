from fastapi import FastAPI
from app.api import vector, recommend

app = FastAPI()

app.include_router(vector.router, prefix="/api")
app.include_router(recommend.router, prefix="/api")

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}