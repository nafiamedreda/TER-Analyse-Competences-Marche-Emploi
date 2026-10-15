# TER — France Travail et ESCO

Projet universitaire mené en groupe de 4 autour de l’analyse des compétences du marché de l’emploi à partir de France Travail et d’ESCO.

## Objectif général

Constituer une base d’offres d’emploi structurée et étudier comment les métiers et les compétences décrits dans ESCO peuvent contribuer à l’analyse des compétences recherchées sur le marché de l’emploi.

## Périmètre initial

Le projet se concentre dans un premier temps sur les métiers Data/IA suivants :

- Data Scientist
- Data Engineer
- ML Engineer
- développeur IA
- Data Analyst

**Contrats :** CDI, CDD, alternance.

**Fenêtre temporelle : 1 an.**

## Sources et référentiels

- **France Travail** : source des offres d’emploi à collecter et à structurer.
- **ESCO** : classification européenne des métiers et des compétences. Son étude permettra d’expliquer son modèle et les relations entre ses concepts, notamment entre métiers et compétences.

## Livrables pour le prochain rendez-vous

- Une base d’offres France Travail structurée + un MCD/MOD.
- Une explication du modèle ESCO et de ses relations.

## Organisation du groupe

Les quatre rôles à répartir sont :

1. Collecte France Travail.
2. Structuration/nettoyage des données + MCD/MOD.
3. Étude du modèle ESCO.
4. Intégration GitHub / documentation.

## Structure du dépôt

```text
TER-FranceTravail-ESCO/
├── data/
│   ├── raw/
│   └── processed/
├── src/
│   ├── france_travail/
│   └── esco/
├── reports/
│   └── weekly/
│       └── semaine_01.md
├── slides/
├── README.md
└── .gitignore
```

Le dépôt contient pour l’instant uniquement la structure et la documentation initiales. Les analyses exploratoires, embeddings, LLM et modèles d’IA relèvent des phases suivantes.
