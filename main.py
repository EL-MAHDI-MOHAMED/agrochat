import os
import sys

# Vérification simple: prévenir l'utilisateur si l'environnement virtuel n'est pas activé
if not os.getenv("VIRTUAL_ENV"):
    print()
    print("⚠️  L'environnement virtuel ne semble pas activé.")
    print("Activez-le (PowerShell) : & .\\.venv\\Scripts\\Activate.ps1")
    print("Puis installez les dépendances : pip install -r requirements.txt")
    print("Ensuite lancez le serveur : uvicorn main:app --reload\n")
    sys.exit(1)

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import uvicorn

from rag_utils import get_answer
import logging

logger = logging.getLogger(__name__)
from image_predictor import predict_plant_disease

app = FastAPI()

# ✔️ Route d'accueil (évite l'erreur 404 sur Render)
@app.get("/")
async def root():
    return {"message": "✅ Felah est opérationnel"}

# 📩 Schéma pour la question texte
class Question(BaseModel):
    query: str

# 🔍 Endpoint pour poser une question texte
@app.post("/ask")
async def ask_question(q: Question):
    try:
        response = get_answer(q.query)
    except Exception as e:
        # Log exception and return a friendly message instead of 500
        logger.exception("Error while answering query: %s", e)
        response = (
            "Une erreur est survenue en traitant la requete. "
            "Verifiez les clefs API et la disponibilite du service (logs cote serveur)."
        )
    return JSONResponse(content={"answer": response})

# 🌿 Endpoint pour prédiction d'image de plante
@app.post("/predict-image")
async def predict_image(file: UploadFile = File(...)):
    return await predict_plant_disease(file)

# 🖥️ Lancement local
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
