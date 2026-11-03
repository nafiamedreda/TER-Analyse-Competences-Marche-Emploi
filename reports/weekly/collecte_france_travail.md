# Collecte des offres d’emploi France Travail

## 1. Objectif

Cette collecte s’inscrit dans le cadre du TER de Master 1 MIASHS portant sur l’analyse des compétences demandées dans les offres d’emploi Data / IA et leur comparaison avec des référentiels de compétences, notamment ESCO.

L’objectif de cette partie est de constituer un premier corpus d’offres d’emploi issues de France Travail afin de fournir des données brutes exploitables pour les étapes suivantes du projet : préparation du dataset, nettoyage, extraction des compétences et alignement avec ESCO.

## 2. Source des données

Les données sont récupérées à partir de l’API officielle **Offres d’emploi v2 de France Travail**.

L’authentification utilise le protocole OAuth2 avec le flux `client_credentials`.

Les identifiants `CLIENT_ID` et `CLIENT_SECRET` sont stockés dans un fichier `.env` qui n’est pas versionné sur GitHub.

## 3. Périmètre de la collecte

Les métiers sélectionnés sont :

- Data Analyst
- Data Scientist
- Data Engineer
- Machine Learning Engineer
- Développeur IA

Les types de contrats étudiés sont :

- CDI
- CDD
- Alternance

La période de recherche utilisée correspond à environ **un an**, avec les paramètres `minCreationDate` et `maxCreationDate`.

## 4. Méthode de collecte

Le script principal est :

`src/france_travail/collect_offres.py`

Le processus réalisé est le suivant :

1. Chargement des identifiants depuis le fichier `.env`.
2. Authentification auprès de France Travail.
3. Obtention d’un token OAuth2.
4. Recherche des offres pour chacun des cinq métiers.
5. Séparation des offres selon les catégories CDI, CDD et alternance.
6. Gestion automatique de la pagination de l’API.
7. Regroupement de toutes les offres collectées.
8. Suppression des doublons à partir de l’identifiant unique de l’offre.
9. Organisation des résultats par métier et par type de contrat.
10. Sauvegarde du corpus dans un fichier JSON.

## 5. Résultats de la collecte

La collecte réalisée le 31 octobre 2026 a donné les résultats suivants :

| Métier | CDI | CDD | Alternance |
|---|---:|---:|---:|
| Data Analyst | 118 | 11 | 12 |
| Data Scientist | 59 | 5 | 1 |
| Data Engineer | 316 | 19 | 7 |
| Machine Learning Engineer | 29 | 1 | 1 |
| Développeur IA | 65 | 5 | 15 |

Nombre total d’occurrences collectées avant dédoublonnage : **664**

Nombre d’offres uniques après suppression des doublons : **615**

Le corpus public disponible dans le dépôt est :

`data/raw/offres_france_travail_public_2026-10-31_13-43.json`

Il conserve les 615 offres uniques et la structure de la collecte. Les champs `contact` et `agence` ont été supprimés récursivement par `src/france_travail/nettoyer_json_public.py` avant publication. Le JSON brut utilisé en entrée de ce script n'est pas inclus dans la version actuelle du dépôt.

## 6. Structure du fichier JSON

Le fichier final contient quatre parties principales :

- `metadata` : informations concernant la source et la collecte ;
- `resume` : nombre d’offres par métier et par contrat ;
- `resultats_par_metier` : offres organisées selon le métier et le type de contrat ;
- `offres_uniques` : corpus global après suppression des doublons.

La partie `offres_uniques` pourra notamment être utilisée pour construire le futur dataset nettoyé.

## 7. Champs vérifiés

Un deuxième script :

`src/france_travail/verifier_collecte.py`

a été utilisé pour contrôler la présence des principales variables nécessaires au projet.

Pour vérifier le corpus public, lancer depuis la racine du dépôt :

```bash
python src/france_travail/verifier_collecte.py
```

Les principaux champs étudiés sont notamment :

- `id`
- `intitule`
- `description`
- `dateCreation`
- `dateActualisation`
- `romeCode`
- `romeLibelle`
- `entreprise`
- `lieuTravail`
- `typeContrat`
- `experienceLibelle`
- `formations`
- `competences`
- `alternance`

Les champs principaux d’identification et de description sont bien renseignés dans la majorité des offres.

En revanche, deux champs présentent une complétude plus faible :

- `formations` : 60 offres sur 615, soit environ **9,8 %** ;
- `competences` : 114 offres sur 615, soit environ **18,5 %**.

Cette observation montre qu’il sera nécessaire, dans les prochaines étapes, d’exploiter également le texte libre du champ `description` pour identifier des compétences qui ne sont pas directement renseignées dans le champ structuré `competences`.

## 8. Limites de la collecte

La recherche par mots-clés peut récupérer certaines offres qui ne correspondent pas parfaitement au métier recherché. Une étape de nettoyage et de validation du périmètre sera donc nécessaire.

Une même offre peut également apparaître dans plusieurs recherches. Les doublons sont supprimés grâce au champ `id`.

Enfin, l’API France Travail expose principalement les offres encore disponibles au moment de la collecte. La période d’un an constitue donc un filtre sur la date de création des offres accessibles, mais ne garantit pas la récupération exhaustive de toutes les offres publiées au cours des douze derniers mois.

## 9. Suite du travail

Le corpus public est transmis à la personne chargée de la préparation du dataset. Son script doit lire `data/raw/offres_france_travail_public_2026-10-31_13-43.json`, en utilisant `offres_uniques` pour les offres dédoublonnées et `metadata` pour les informations de collecte. La suppression des champs de contact ne remplace pas le nettoyage métier du dataset.

Les prochaines étapes sont notamment :

- analyse de la structure des données ;
- gestion des valeurs manquantes ;
- contrôle des doublons ;
- sélection des variables utiles ;
- préparation du dataset exploitable ;
- extraction des compétences depuis les descriptions ;
- rapprochement avec le référentiel ESCO.

Les fichiers bruts présents dans `data/raw/` doivent être conservés sans modification afin d’assurer la traçabilité des données sources.
