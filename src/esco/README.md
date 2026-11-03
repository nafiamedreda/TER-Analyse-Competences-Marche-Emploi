# Exploration et préparation des données ESCO

## Objectif dans le TER

Explorer le référentiel européen ESCO pour comprendre les métiers, les compétences et leurs relations, puis préparer une base locale avec leurs intitulés français. Cette base servira aux futures expérimentations d'alignement avec les compétences présentes dans les offres d'emploi, notamment pour les métiers Data/IA. Le notebook ne réalise pas encore cet alignement.

## Récupérer les données officielles

Les données utilisées proviennent d'**ESCO version 1.2.1**, la classification européenne des métiers et des compétences publiée par la Commission européenne, en **français (fr)** et au format **CSV**. L'archive d'origine est `ESCO dataset - v1.2.1 - classification - fr - csv.zip`. Elle est déjà conservée localement et n'a pas à être déplacée ni copiée dans le dépôt.

1. Ouvrir la [page officielle de téléchargement ESCO](https://esco.ec.europa.eu/en/use-esco/download).
2. Sélectionner précisément la version **ESCO dataset - v1.2.1**, le contenu **classification**, la langue **français (fr)** et le format **CSV**.
3. Ajouter le jeu au paquet à télécharger et suivre les instructions du portail : acceptation de la déclaration de confidentialité, saisie d'une adresse électronique et réception du lien de téléchargement.
4. Extraire l'archive et copier les trois fichiers ci-dessous dans `data/raw/`, à la racine du dépôt, en conservant exactement leurs noms.

| Fichier | Contenu utilisé |
| --- | --- |
| `skills_fr.csv` | Compétences et connaissances : identifiants, intitulés français, types et dates de modification |
| `occupations_fr.csv` | Métiers : identifiants, intitulés français et dates de modification |
| `occupationSkillRelations_fr.csv` | Relations entre métiers et compétences, essentielles ou optionnelles |

La [documentation officielle des fichiers ESCO](https://esco.ec.europa.eu/en/structure-esco-downloadable-datasets) décrit leur organisation. La [présentation officielle d'ESCO 1.2.1](https://esco.ec.europa.eu/en/about-esco/escopedia/escopedia/esco-v121) confirme la disponibilité de cette version dans la section de téléchargement. Les résultats ci-dessous correspondent aux données locales issues de cette archive et peuvent varier avec une autre version. Pour les reproduire, conserver la version **1.2.1** et les filtres indiqués ci-dessus.

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

Le notebook crée le dossier `data/processed/` si nécessaire avant l’export.

La cellule d’export écrit `data/processed/esco_metiers_competences_fr.csv`, sans index et en encodage `utf-8-sig`. Une nouvelle exécution réécrit ce fichier final ; les trois CSV sources restent inchangés. Aucun téléchargement automatique n'est effectué par le notebook.

## Traitements et résultats vérifiés dans le notebook

- Exploration des dimensions, des types de compétences, des niveaux de réutilisation, des identifiants et des valeurs manquantes.
- Déduplication des compétences : **13 960 lignes** initiales, dont **21 occurrences supplémentaires** sur `conceptUri`. Les enregistrements concernés ne diffèrent que par `modifiedDate`. Le tri sur cette date, suivi de `drop_duplicates(subset="conceptUri", keep="last")`, conserve la version la plus récente : **13 939 compétences et connaissances distinctes**.
- Même traitement pour les métiers : **3 043 lignes** initiales deviennent **3 039 métiers distincts**.
- Exploration des **126 051 relations**, de leur caractère essentiel ou optionnel, et visualisation de leur répartition. Vérification que tous les identifiants référencés existent dans les tables nettoyées.
- Deux jointures à gauche ajoutent les intitulés français des métiers et des compétences sans perdre ni multiplier les relations.

La table finale contient **126 051 lignes et 6 colonnes** : `occupationUri`, `metier`, `skillUri`, `competence`, `type_relation`, `type_competence`. Les effectifs de 3 039 métiers et 13 939 compétences décrivent les référentiels nettoyés.

Cinq compétences numériques ont un type absent dans les sources ; elles sont conservées. Dans la table finale, cela concerne **59 relations** : les valeurs manquantes de `type_competence` sont remplacées par **« non renseigné »**, sans attribuer arbitrairement un type. Les manques observés dans `reuseLevel` ne sont pas imputés : cette colonne n'est pas retenue dans la table finale. Le contrôle final `df_esco.isna().sum()` indique **zéro valeur manquante dans les six colonnes**.


## Modèle ESCO : entités et cardinalités

Les métiers de `occupations_fr.csv` et les compétences/connaissances de `skills_fr.csv` sont identifiés par `conceptUri` dans leurs fichiers respectifs. Ces identifiants sont nommés `occupationUri` et `skillUri` dans `occupationSkillRelations_fr.csv` et dans la table consolidée. La table de relations matérialise chaque association entre un métier et une compétence.

```text
Métier (occupation) 1 — N Association métier-compétence N — 1 Compétence (skill)
```

Les deux relations 1—N représentent ensemble une relation **plusieurs-à-plusieurs** : un métier peut avoir plusieurs compétences et une compétence peut être associée à plusieurs métiers. Ce sont des cardinalités conceptuelles ; aucune contrainte de cardinalité minimale du modèle officiel n’est ici présentée comme vérifiée.

Les effectifs observés sont distincts de ces cardinalités : les référentiels nettoyés contiennent **3 039 métiers** et **13 939 compétences/connaissances**. Les associations présentes dans les données concernent **3 039 métiers** et **13 475 compétences/connaissances** ; toutes les compétences du référentiel ne figurent donc pas dans cette table de relations.

`type_relation` reprend `relationType` :

| Catégorie observée | Signification selon le référentiel | Associations |
| --- | --- | ---: |
| `essential` | Compétence considérée comme essentielle pour ce métier | 67 600 |
| `optional` | Compétence considérée comme optionnelle pour ce métier | 58 451 |

Ces deux catégories couvrent les **126 051 relations**, sans valeur manquante.

`type_competence` reprend `skillType` du fichier des relations : `knowledge` désigne une connaissance (**34 384 relations**) et `skill/competence` une compétence pratique (**91 608 relations**). Les **59 valeurs manquantes** ont été explicitement remplacées par **« non renseigné »**. Elles concernent cinq compétences numériques également sans type dans `skills_fr.csv` ; ce remplacement conserve les associations sans inventer de classification.

## Validation pour la revue

Une exécution complète a été réalisée avec **Python 3.14.6**, **pandas 3.0.3** et un **nouveau noyau `python3`**, depuis `src/esco/`, via `nbclient` (`allow_errors=False`). Les **39 cellules de code** ont été exécutées dans l’ordre, avec des compteurs continus de 1 à 39 et sans erreur. Les sorties de cette exécution sont enregistrées dans le notebook.

| DataFrame | Lignes | Colonnes |
| --- | ---: | ---: |
| `df_skills` après dédoublonnage | 13 939 | 13 |
| `df_occupations` après dédoublonnage | 3 039 | 15 |
| `df_relations` | 126 051 | 6 |
| `df_esco` | 126 051 | 6 |

Le fichier `data/processed/esco_metiers_competences_fr.csv` a été exporté puis relu avec pandas. La cellule finale vérifie son existence, les six colonnes attendues dans leur ordre (`occupationUri`, `metier`, `skillUri`, `competence`, `type_relation`, `type_competence`), ses dimensions, puis l’égalité de **toutes les valeurs et de l’ordre des lignes** avec `df_esco` par `pd.testing.assert_frame_equal`. Aucune troncature n’a été observée. Chaque colonne contient **0 valeur manquante**. Les contrôles vérifient aussi la conservation du nombre de relations, les catégories, l’unicité des identifiants nettoyés et l’absence d’identifiants référencés inconnus.

Les empreintes SHA-256 des trois CSV sources sont identiques avant et après l’exécution. Les quatre fichiers de données restent exclus de Git. Tous les chiffres de l’exploration précédente sont confirmés.

Pour reproduire cette validation automatisée dans un environnement disposant des données et des dépendances (`pandas`, `matplotlib`, `nbformat`, `nbclient`, `ipykernel`), depuis la racine du dépôt :

```powershell
python -c "from pathlib import Path; import nbformat; from nbclient import NotebookClient; p=Path('src/esco/exploration_esco.ipynb'); n=nbformat.read(p, as_version=4); NotebookClient(n, kernel_name='python3', timeout=300, allow_errors=False, resources={'metadata': {'path': str(p.parent.resolve())}}).execute(); nbformat.write(n, p)"
```

Cette commande démarre un nouveau noyau et réexécute toutes les cellules ; la cellule finale interrompt l’exécution si les contrôles échouent. Le noyau `python3` doit correspondre à l’environnement contenant les dépendances.

## Dictionnaire complet des compétences

`preparer_dictionnaire_esco.py` prépare une ligne par compétence ou connaissance
à partir du référentiel complet **ESCO v1.2.1 français**, `data/raw/skills_fr.csv`.
Il utilise également `data/processed/esco_metiers_competences_fr.csv` pour
contrôler la correspondance avec les relations préparées par le notebook.
Ces deux entrées locales doivent donc être présentes. Le script ne télécharge
rien, ne modifie pas les entrées et ne réalise aucun alignement France Travail.

Depuis la **racine du dépôt**, avec Python 3.10 ou supérieur, sans dépendance externe :

```powershell
python src/esco/preparer_dictionnaire_esco.py
```

La sortie est `data/processed/esco_dictionnaire_competences_fr.csv`, sans index,
en UTF-8 avec BOM, triée par URI. Ce CSV généré est ignoré par une règle ciblée
du `.gitignore` ; le script Python reste destiné au versionnement.

Le script refuse d'écraser une sortie existante. Pour la régénérer, déplacer
d'abord le CSV existant vers une sauvegarde, puis relancer la commande depuis
la racine. Comparer les fichiers avant de supprimer la sauvegarde. Avec les
mêmes entrées, la régénération a produit un fichier identique octet par octet.

| Colonne | Source et traitement |
| --- | --- |
| `skillUri` | `conceptUri`, identifiant du concept ; une seule ligne par URI |
| `competence` | `preferredLabel`, libellé français officiel conservé sans reformulation |
| `type_competence` | `skillType` : `knowledge` ou `skill/competence` ; absence conservée vide |
| `altLabels` | Synonymes officiels de `altLabels`, sous forme de liste JSON ; `[]` en l'absence de synonymes |

Les synonymes sont séparés sur les sauts de ligne du champ source, jamais sur
les virgules. Leur ordre et leurs libellés sont conservés, sans traduction,
normalisation ni ajout. Les éventuelles répétitions sont comptées et conservées.
Une cellule contenant `[]` n'est pas vide, mais signifie qu'aucun synonyme n'est fourni.

### Doublons et anomalies

Le script vérifie les colonnes nécessaires, les URI, les libellés principaux
et la présence et la validité de chaque `modifiedDate` (date-heure avec fuseau).
Pour les URI répétées, toutes les colonnes source sont comparées. Si les lignes
diffèrent uniquement par la date, la plus récente est retenue. Les lignes
strictement identiques peuvent également être dédupliquées. Tout conflit sur
une autre colonne ou toute date absente/invalide bloque l'export et est signalé.
Les libellés principaux identiques associés à des URI différentes ne sont pas fusionnés.

### Contrôles et résultats obtenus

Les tableaux sont affichés dans le terminal ; aucun rapport supplémentaire n'est créé.

| Contrôle | Résultat sur les fichiers locaux v1.2.1 |
| --- | ---: |
| Lignes source / dates présentes et valides | 13 960 / 13 960 |
| URI répétées / occurrences supplémentaires | 21 / 21 |
| Conflits hors `modifiedDate` | 0 |
| Concepts exportés / doublons d'URI en sortie | 13 939 / 0 |
| URI ou libellés principaux absents | 0 |
| Concepts `skill/competence` / `knowledge` | 10 715 / 3 219 |
| Concepts sans type, conservés | 5 |
| Concepts avec synonymes / sans synonymes | 1 928 / 12 011 |
| Mentions de synonymes / listes avec répétitions | 6 616 / 0 |
| Libellés principaux partagés par plusieurs URI | 4 |
| Relations du consolidé contrôlées | 126 051 |
| URI distinctes du consolidé retrouvées | 13 475 |
| URI inconnues / écarts de libellé ou de type | 0 / 0 |
| Concepts absents du consolidé, conservés dans le dictionnaire | 464 |

Les cinq types manquants ne sont pas imputés. Pour la comparaison uniquement,
le script tient compte de leur représentation par `non renseigné` dans le
consolidé. Les quatre libellés partagés sont « biologie marine », « contrôler
la qualité de vins », « distribuer des tracts » et « mélanger des produits
alimentaires », chacun associé à deux URI distinctes.

Après export, le script relit le CSV, vérifie les quatre colonnes et l'égalité
de toutes les valeurs avec les données préparées, puis la validité des listes
JSON. Les empreintes SHA-256 des deux entrées sont comparées avant et après.
Une incohérence avec le consolidé bloque l'export. Les effectifs ci-dessus sont
des résultats observés, pas des valeurs imposées au script pour une autre version.
