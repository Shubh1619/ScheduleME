from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth ,account,meta_posts  # Add more in phases
from app.core.database import engine, Base ,create_database_if_not_exists
import asyncio
import logging

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
app.include_router(meta_posts.router)

@app.on_event("startup")
async def startup_event():
    # 1) Ensure database exists
    await create_database_if_not_exists()

    # 2) Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("[INFO] Tables created successfully.")
    
    # if your app variable is named `app`, otherwise adjust
def print_routes(app: FastAPI):
    for route in app.routes:
        methods = ",".join(sorted(route.methods)) if getattr(route, "methods", None) else "N/A"
        logging.warning(f"ROUTE: {route.path}  methods={methods}")

print_routes(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)