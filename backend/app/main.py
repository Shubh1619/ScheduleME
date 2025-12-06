from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth ,account  # Add more in phases
from app.core.database import engine, Base ,create_database_if_not_exists
import asyncio

app = FastAPI(title="SchedulMe API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(account.router)

@app.on_event("startup")
async def startup_event():
    # 1) Ensure database exists
    await create_database_if_not_exists()

    # 2) Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("[INFO] Tables created successfully.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)