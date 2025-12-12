from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from .db import Base, engine
from .routers import auth_routes, categories_routes, transactions_routes

app = FastAPI(
    title="Finance Tracker API",
    description="Учет личных доходов и расходов по категориям",
)
STATIC_DIR = Path(__file__).resolve().parent / "static"


@app.on_event("startup")
async def on_startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Ресурс не найден"},
    )


app.include_router(auth_routes.router)
app.include_router(categories_routes.router)
app.include_router(transactions_routes.router)

if STATIC_DIR.exists():
    app.mount(
        "/ui",
        StaticFiles(directory=STATIC_DIR, html=True),
        name="ui",
    )