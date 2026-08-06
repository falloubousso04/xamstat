# XamStat

Assistant conversationnel pour explorer les données statistiques de l'ANSD (population, pauvreté) par région du Sénégal — prototype réalisé pour le Hackathon ANSD 20 ans.

## Données

- Population par région : ANSD, RGPH-5 (2023), rapport définitif, Tableau I-21, p. 45.
- Taux de pauvreté par région : ANSD, EHCVM II (2021/2022), rapport final, Tableau III-2, p. 34.
- Contours géographiques des régions : [geoBoundaries.org](https://www.geoboundaries.org) (ADM1 Sénégal, CC BY 4.0) — géométrie uniquement, distincte des données statistiques ANSD.

Toutes les valeurs affichées proviennent de ces rapports ; le prototype ne calcule ni n'invente aucune statistique.

## Lancer en local

**Backend (FastAPI)**

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend (React + Vite)**

```bash
cd frontend
npm install
npm run dev
```

Le frontend proxy automatiquement `/api` vers `http://127.0.0.1:8000` en développement (voir `vite.config.ts`).

## Déploiement (Render)

Le `Dockerfile` à la racine construit le frontend puis sert l'API et les fichiers statiques depuis un seul service FastAPI (une seule URL, pas de configuration CORS à gérer en production).

1. Créer un dépôt GitHub et y pousser ce projet.
2. Sur [render.com](https://render.com), créer un compte (gratuit, inscription par email) puis **New > Web Service**.
3. Connecter le dépôt GitHub — Render détecte automatiquement le `Dockerfile` (ou utiliser `render.yaml` via **New > Blueprint**).
4. Plan **Free**, laisser les commandes par défaut (elles viennent du Dockerfile).
5. Déployer : Render fournit une URL publique du type `https://xamstat.onrender.com`.

Le endpoint `/api/health` sert de health check pour Render.

## Architecture

```
backend/app/
  main.py        API FastAPI (/api/ask, /api/regions, /api/geojson)
  nlu.py         extraction d'indicateur + région à partir de la question
  responder.py   construit la réponse texte + la spécification de graphique
  data/          regions.json (données sourcées) + senegal_regions.geojson
frontend/src/
  App.tsx                composant principal (chat + panneau de visualisation)
  components/             ChatBubble, ChartPanel (Recharts), MapPanel (Leaflet)
```
