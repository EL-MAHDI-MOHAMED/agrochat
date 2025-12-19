# Utiliser une image Python officielle légère
FROM python:3.9-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires 
# (build-essential peut être requis pour certaines libs Python)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python
# On upgrade pip pour éviter les warnings
RUN pip install --no-cache-dir --upgrade pip

# Installer PyTorch (CPU only) pour réduire la taille de l'image et accélérer le build
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copier le fichier des dépendances
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code de l'application backend
COPY . .

# Exposer le port (par défaut 8000 pour FastAPI/Uvicorn)
EXPOSE 8000

# Commande de démarrage
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
