import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, SessionLocal, engine
from app.routes import partidos, predicciones
from app.services.partido_service import sincronizar_thesportsdb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)


async def _sync_thesportsdb_background():
    """Sincroniza TheSportsDB en background al iniciar la app."""
    await asyncio.sleep(2)  # Esperar a que la app esté lista
    db = SessionLocal()
    try:
        logger.info("Sincronizando partidos internacionales (TheSportsDB)...")
        partidos = await sincronizar_thesportsdb(db, date.today())
        logger.info(f"TheSportsDB: {len(partidos)} partidos sincronizados al iniciar")
    except Exception as e:
        logger.warning(f"Error sincronizando TheSportsDB al iniciar: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: sincronizar TheSportsDB en background
    task = asyncio.create_task(_sync_thesportsdb_background())
    yield
    task.cancel()


app = FastAPI(
    title="Prediccion Futbol API",
    description="API para prediccion de resultados de partidos de futbol",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(partidos.router, prefix="/api/partidos", tags=["Partidos"])
app.include_router(predicciones.router, prefix="/api/predicciones", tags=["Predicciones"])


@app.get("/")
def root():
    return {"message": "Prediccion Futbol API", "version": "0.1.0"}
