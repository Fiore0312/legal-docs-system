from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.endpoints import auth, documenti, ai

app = FastAPI(title="Liquidazione IA API")

# Configurazione CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Includi i router
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(documenti.router, prefix="/documenti", tags=["documenti"])
app.include_router(ai.router, prefix="/ai", tags=["ai"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Il server è attivo e funzionante!"} 