# Exploration et préparation des données ESCO

## Objectif dans le TER

Explorer le référentiel européen ESCO pour comprendre les métiers, les compétences et leurs relations, puis préparer une base locale avec leurs intitulés français. Cette base servira aux futures expérimentations d'alignement avec les compétences présentes dans les offres d'emploi, notamment pour les métiers Data/IA. Le notebook ne réalise pas encore cet alignement.

## Récupérer les données officielles

Les données proviennent d'ESCO, la classification européenne des métiers et des compétences publiée par la Commission européenne.

1. Ouvrir la [page officielle de téléchargement ESCO](https://esco.ec.europa.eu/en/use-esco/download).
2. Choisir une version du jeu de données, le contenu **classification**, la langue **français (fr)** et le format **CSV**.
3. Ajouter le jeu au paquet à télécharger et suivre les instructions du portail : acceptation de la déclaration de confidentialité, saisie d'une adresse électronique et réception du lien de téléchargement.
4. Extraire l'archive et copier les trois fichiers ci-dessous dans `data/raw/`, à la racine du dépôt, en conservant exactement leurs noms.

| Fichier | Contenu utilisé |
| --- | --- |
| `skills_fr.csv` | Compétences et connaissances : identifiants, intitulés français, types et dates de modification |
| `occupations_fr.csv` | Métiers : identifiants, intitulés français et dates de modification |
| `occupationSkillRelations_fr.csv` | Relations entre métiers et compétences, essentielles ou optionnelles |

La [documentation officielle des fichiers ESCO](https://esco.ec.europa.eu/en/structure-esco-downloadable-datasets) décrit leur organisation. La version exacte des fichiers utilisés n'est pas renseignée dans le notebook : les résultats ci-dessous correspondent aux données locales étudiées et peuvent varier avec une autre version. Conserver le nom de l'archive et sa version lors d'un nouveau téléchargement pour faciliter la reproduction.

```text
data/
  raw/
    skills_fr.csv
    occupations_fr.csv
    occupationSkillRelations_fr.csv
  processed/
    esco_metiers_competences_fr.csv  # généré par le notebook
src/
  esco/
    exploration_esco.ipynb
    README.md
```

Ces quatre CSV sont exclus de Git par des règles ciblées dans le `.gitignore` racine. Ils ne sont pas téléchargés avec le dépôt. Les autres CSV du groupe ne sont pas exclus par ces règles.

## Ouvrir et exécuter le notebook

Utiliser Python avec **pandas**, **matplotlib** et un environnement Jupyter. Par exemple, dans un environnement Python dédié, depuis la racine du dépôt :

```powershell
python -m pip install pandas matplotlib notebook
cd src/esco
python -m notebook exploration_esco.ipynb
```

Sélectionner le noyau Python de cet environnement, puis exécuter toutes les cellules dans l'ordre, du début à la fin. Le répertoire de travail du noyau doit être `src/esco/` : la première cellule affiche le répertoire courant et son contenu. Les chemins `../../data/raw/...` et `../../data/processed/...` sont corrects depuis ce répertoire, mais pas depuis la racine du dépôt.

Le dossier `data/processed/` doit exister avant l'exécution : le notebook ne le crée pas. Il est présent dans la structure du dépôt.

La dernière cellule écrit `data/processed/esco_metiers_competences_fr.csv`, sans index et en encodage `utf-8-sig`. Une nouvelle exécution réécrit ce fichier final ; les trois CSV sources restent inchangés. Aucun téléchargement automatique n'est effectué par le notebook.

## Traitements et résultats vérifiés dans le notebook

- Exploration des dimensions, des types de compétences, des niveaux de réutilisation, des identifiants et des valeurs manquantes.
- Déduplication des compétences : **13 960 lignes** initiales, dont **21 occurrences supplémentaires** sur `conceptUri`. Les enregistrements concernés ne diffèrent que par `modifiedDate`. Le tri sur cette date, suivi de `drop_duplicates(subset="conceptUri", keep="last")`, conserve la version la plus récente : **13 939 compétences et connaissances distinctes**.
- Même traitement pour les métiers : **3 043 lignes** initiales deviennent **3 039 métiers distincts**.
- Exploration des **126 051 relations**, de leur caractère essentiel ou optionnel, et visualisation de leur répartition. Vérification que tous les identifiants référencés existent dans les tables nettoyées.
- Deux jointures à gauche ajoutent les intitulés français des métiers et des compétences sans perdre ni multiplier les relations.

La table finale contient **126 051 lignes et 6 colonnes** : `occupationUri`, `metier`, `skillUri`, `competence`, `type_relation`, `type_competence`. Les effectifs de 3 039 métiers et 13 939 compétences décrivent les référentiels nettoyés.

Cinq compétences numériques ont un type absent dans les sources ; elles sont conservées. Dans la table finale, cela concerne **59 relations** : les valeurs manquantes de `type_competence` sont remplacées par **« non renseigné »**, sans attribuer arbitrairement un type. Les manques observés dans `reuseLevel` ne sont pas imputés : cette colonne n'est pas retenue dans la table finale. Le contrôle final `df_esco.isna().sum()` indique **zéro valeur manquante dans les six colonnes**.
