# Agrosys Chatbot — Frontend

Ceci est une interface simple pour le chatbot Agrosys, construite avec Next.js + Tailwind.

## Fonctionnalités
- UI de chat minimaliste et responsive
- Route API `/api/chat` qui proxie vers un backend (par défaut `http://localhost:8000/chat`)

## Installation et exécution
1. Ouvrir un terminal et se placer dans `frontend` :

```powershell
cd frontend
```

2. Installer les dépendances :

```powershell
npm install
```

3. Lancer en développement :

```powershell
npm run dev
```

L'application s'exécute par défaut sur http://localhost:3000

## Configuration
- Pour définir une URL backend différente, en PowerShell :

```powershell
$env:BACKEND_URL = 'http://localhost:8000/chat'
npm run dev
```

Note: le backend dans ce dépôt expose l'endpoint `/ask` (POST JSON { "query": "..." }) — le frontend mappe automatiquement votre message vers ce format. Si vous utilisez un backend différent, pointez `BACKEND_URL` vers l'URL complète de l'endpoint (par ex. `http://localhost:8000/ask`).

Si aucun backend n'est disponible, la route renverra une réponse de secours `Echo: <votre_message>`.

Note sur les embeddings : si le backend utilise le fallback local pour les embeddings (quand Google embeding est indisponible), installez `sentence-transformers` côté backend pour permettre la recherche locale (voir README à la racine).

Fichiers importants :
- `app/page.tsx` : page principale
- `components/ChatBox.tsx` : composant de conversation
- `app/api/chat/route.ts` : route API proxy
