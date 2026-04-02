# CLAUDE.md — AdScreen

> Hérite de toutes les règles globales : `C:\Users\shaba\CLAUDE.md`
> En cas de conflit, les règles globales prévalent.

## Projet

- **Nom** : AdScreen
- **Stack** : Flask + Python + Node
- **GitHub** : https://github.com/moa-digitalagency/AdScreen
- **VPS** : 31.97.154.192 — Port 5010
- **Clé SSH** : id_ed25519_srv826792

---

## 🚫 RÈGLE ABSOLUE — WORKFLOW VPS

**JAMAIS modifier des fichiers directement sur le VPS.**

```text
1. DIAGNOSTIQUER sur le VPS (SSH — lecture seule)
   - pm2 logs AdScreen / tail -f logs/error.log
   - cat [fichier] pour lire — JAMAIS nano/vim/sed/echo >

2. MODIFIER en local (VSCode)
   - Toutes les corrections dans ce dossier local

3. COMMIT + PUSH local → GitHub
   - git add [fichiers modifiés]
   - git commit -m "fix: description"
   - git push origin main

4. DÉPLOYER sur le VPS
   - ssh -i ~/.ssh/id_ed25519_srv826792 root@31.97.154.192
   - cd /root/AdScreen && git pull origin main
   - pm2 restart AdScreen

5. VÉRIFIER
   - curl http://localhost:5010
   - pm2 logs AdScreen
```

---

## Git — Règles

- **JAMAIS** push sur `main` directement (sauf si user demande explicitement)
- **TOUJOURS** créer une branche + PR pour les features
- **JAMAIS** committer : `.env`, `venv/`, `screenshots/`, `node_modules/`, `*.db`
- Attendre validation explicite avant tout push

---

## Stack & Conventions

Flask + Python + Node

- Backend : Flask + Gunicorn (si Python)
- Base de données : PostgreSQL (localhost:5432)
- Frontend : HTML + Tailwind CSS + JS vanilla
- Tests : Playwright (Node.js)
- Process manager : PM2 sur VPS

---

## UI — Style obligatoire

- Interface **glassmorphism premium** — jamais fond blanc basique
- Background gradient sombre (dark theme)
- Google Font Inter (300/400/600/700/800)
- Gradient text sur titres principaux
- Boutons arrondis avec hover lift effect
- Animations subtiles (scroll-reveal, float, transitions)
- Responsive mobile-first obligatoire
- Scrollbar custom

---

## Workflow après chaque changement

```text
1. Modifier le code en local
2. /validate-and-push
   a. Lance l'app en arrière-plan
   b. Playwright capture desktop + mobile
   c. Présente captures → STOP, attendre validation
   d. Si OK → commit → push GitHub → git pull VPS → pm2 restart
```

---

## Actions interdites

- Modifier des fichiers directement sur le VPS
- Push sur main sans validation
- DEBUG=True en production
- Committer .env ou credentials
- Supposer une config VPS sans vérifier avec cat/grep
