# Nettoyage des offres France Travail

## Objectif dans le TER

Transformer les offres d'emploi récupérées depuis France Travail en une base propre et structurée, conforme au dictionnaire de données (`data/processed/dictionnaire_donnees.md`). Cette base servira à l'analyse des données (phase 3) et à l'extraction des compétences (phase 4).

**État actuel :** l'accès à l'API France Travail n'est pas encore obtenu. Le script est donc développé et testé sur un fichier d'offres fictives (`data/raw/offres_fictives.csv`). Quand les vraies offres seront disponibles, une étape de conversion du JSON de l'API sera ajoutée au début du script ; les règles de nettoyage resteront les mêmes.

## Fichiers

```text
data/
  raw/
    offres_fictives.csv          # offres de test, avec cas pièges
    insee/                       # tables géographiques (à télécharger, voir ci-dessous)
      v_commune_2026.csv
      v_departement_2026.csv
      v_region_2026.csv
  processed/
    dictionnaire_donnees.md      # schéma de la base et règles de nettoyage
    offres_propres.csv           # généré par le script
src/
  france_travail/
    nettoyage.py
    README.md
```

## Récupérer les tables INSEE

Le script déduit le département et la région de chaque offre à partir du code commune, grâce au **Code officiel géographique (COG) 2026** de l'INSEE. Ces fichiers ne sont pas dans le dépôt.

1. Ouvrir la [page de téléchargement du COG 2026](https://www.insee.fr/fr/information/8740222).
2. Télécharger les trois fichiers CSV : `v_commune_2026.csv`, `v_departement_2026.csv`, `v_region_2026.csv`.
3. Les placer dans `data/raw/insee/` en conservant exactement leurs noms.

## Lancer le script

Il faut Python avec **pandas** :

```bash
python -m pip install pandas
python src/france_travail/nettoyage.py
```

Le script retrouve ses fichiers à partir de son propre emplacement : il peut être lancé depuis n'importe quel dossier.

## Ce que fait le script

Les règles détaillées sont dans le dictionnaire de données. Dans l'ordre :

1. **Lecture** du fichier d'offres (tout en texte, pour garder les codes comme `01001` ou `2A004`).
2. **Typage** des dates et du booléen `alternance`.
3. **Périmètre** : `type_contrat` devient « alternance » si `alternance` = vrai ; CDI et CDD sont gardés ; le reste est exclu (ex. intérim).
4. **Géographie** : département (code) et région (nom) déduits du code commune.
5. **Doublons exacts** : même `job_id` → on garde la version la plus récente (`date_actualisation`).
6. **Offres incomplètes** : un champ obligatoire manquant → l'offre est supprimée.
7. **Doublons probables** : même titre + entreprise + description → signalés dans `doublon_suspect`, non supprimés.
8. **Écriture** de `data/processed/offres_propres.csv` et affichage d'un petit rapport qualité.

## Résultat sur le fichier fictif

| Étape | Résultat |
| --- | --- |
| Offres lues | 12 |
| Hors périmètre exclues | 1 (FT005, intérim) |
| Doublons exacts retirés | 1 (FT002, version la plus ancienne) |
| Incomplètes supprimées | 1 (FT011, titre manquant) |
| **Offres finales** | **9** |
| Doublons suspects | FT009, FT010 |

Les cas particuliers de géographie sont vérifiés : Corse (`2A004` → 2A, Corse), outre-mer (`97411` → 974, La Réunion), commune manquante (département et région laissés vides).

## Reste à faire

- Remplir la colonne « source API » du dictionnaire à partir d'une vraie réponse de l'API.
- Ajouter la conversion du JSON de l'API vers le format du dictionnaire.
- Lancer le script sur les vraies offres collectées.
