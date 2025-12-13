# Agrosys Chatbot — Backend

Avant de lancer le serveur (`main.py`), activez l'environnement virtuel et installez les dépendances :

PowerShell (Windows) :

```powershell
& .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

Si vous lancez `python main.py` sans activer l'environnement virtuel, le programme s'arrêtera avec un message vous rappelant d'activer la venv afin d'éviter des erreurs d'import de paquets.

Remarques :
- Pour que les réponses du bot fonctionnent pleinement, vous devez configurer les clefs d'API (par ex. `GOOGLE_API_KEY`, `PINECONE_API_KEY`) dans un fichier `.env` ou dans vos variables d'environnement. Sans ces clefs, l'endpoint `/ask` peut répondre avec une erreur 500 ou une réponse de secours.

Fallback local d'embeddings
- Si votre quota Google embeddings est épuisé, le backend essaiera d'utiliser un modèle local `sentence-transformers/all-MiniLM-L6-v2` pour calculer des embeddings et continuer la recherche localement. Pour activer ce fallback, installez :

```powershell
pip install sentence-transformers numpy
```

Note: `sentence-transformers` installe souvent `torch` comme dépendance (taille importante). Si vous préférez éviter d'installer `torch`, vous pouvez tester l'API sur un plan payant ou exécuter la recherche en mode mock (me demander d'ajouter le mode mock si utile).

Affichage sous PowerShell (encodage)
- Si vous voyez des caracteres accentues mal affiches (ex: "DÃ©solÃ©"), votre console PowerShell n'utilise pas UTF-8. Pour corriger cela temporairement dans la session PowerShell :

```powershell
chcp 65001
$OutputEncoding = [System.Text.Encoding]::UTF8
```

Après cela, relancez la commande `Invoke-RestMethod` ou votre serveur pour que les caracteres accentues s'affichent correctement.
