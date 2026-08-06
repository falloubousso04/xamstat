import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .nlu import RegionCatalog, interpret
from .responder import SUGGESTED_QUESTIONS, build_response
from .schemas import AskRequest, AskResponse

DATA_DIR = Path(__file__).parent / "data"
STATIC_DIR = Path(__file__).parent / "static"

with open(DATA_DIR / "regions.json", encoding="utf-8") as f:
    REGIONS_DATA = json.load(f)

CATALOG = RegionCatalog(REGIONS_DATA)

app = FastAPI(title="XamStat API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/regions")
def regions():
    return REGIONS_DATA


@app.get("/api/geojson")
def geojson():
    return FileResponse(DATA_DIR / "senegal_regions.geojson", media_type="application/geo+json")


@app.get("/api/suggestions")
def suggestions():
    return {"suggestions": SUGGESTED_QUESTIONS}


@app.post("/api/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    intent = interpret(payload.question, CATALOG)
    return build_response(intent, REGIONS_DATA)


# Sert le build React (npm run build -> ../frontend/dist copié ici) une fois déployé.
# En développement local, ce dossier n'existe pas encore : on l'ignore silencieusement.
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
