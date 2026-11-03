"""Préparer le dictionnaire ESCO français complet, sans dépendance externe.

Depuis la racine : python src/esco/preparer_dictionnaire_esco.py
Entrées : sources locales ESCO v1.2.1 et table consolidée existante.
Les altLabels officiels, séparés par des sauts de ligne dans la source,
sont exportés en listes JSON. Aucun rapprochement France Travail n'est fait.
Un conflit autre que modifiedDate bloque l'export ; aucun choix silencieux.
Le CSV de sortie ne doit pas déjà exister (aucun écrasement).
"""

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/raw/skills_fr.csv"
CONSOLIDE = ROOT / "data/processed/esco_metiers_competences_fr.csv"
SORTIE = ROOT / "data/processed/esco_dictionnaire_competences_fr.csv"
COLONNES = ["skillUri", "competence", "type_competence", "altLabels"]


def lire(path):
    with path.open(encoding="utf-8-sig", newline="") as fichier:
        lecteur = csv.DictReader(fichier)
        lignes = list(lecteur)
        if any(None in ligne or None in ligne.values() for ligne in lignes):
            raise ValueError(f"Structure CSV incorrecte : {path}")
        return lecteur.fieldnames, lignes


def tableau(titre, colonnes, lignes):
    print(f"\n{titre}\n")
    print("| " + " | ".join(colonnes) + " |")
    print("| " + " | ".join("---" for _ in colonnes) + " |")
    for ligne in lignes:
        print("| " + " | ".join(str(v).replace("|", "\\|").replace("\n", " / ") for v in ligne) + " |")


def empreinte(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if SORTIE.exists():
        raise FileExistsError(f"Sortie déjà présente, aucun écrasement : {SORTIE}")
    avant = {p: empreinte(p) for p in (SOURCE, CONSOLIDE)}
    champs, sources = lire(SOURCE)
    requis = {"conceptUri", "preferredLabel", "skillType", "altLabels", "modifiedDate"}
    if not requis.issubset(champs):
        raise ValueError(f"Colonnes source absentes : {sorted(requis - set(champs))}")

    groupes = defaultdict(list)
    dates = {}
    anomalies = []
    for numero, ligne in enumerate(sources, start=2):
        uri = ligne["conceptUri"]
        url = urlsplit(uri)
        if url.scheme not in {"http", "https"} or not url.netloc or not uri.strip():
            anomalies.append((numero, uri, "URI absente ou invalide"))
        if not ligne["preferredLabel"].strip():
            anomalies.append((numero, uri, "Libellé français absent"))
        try:
            texte_date = ligne["modifiedDate"].replace("Z", "+00:00")
            # strptime accepte aussi les fractions à 1 ou 2 chiffres,
            # contrairement à fromisoformat sous Python 3.10.
            format_date = "%Y-%m-%dT%H:%M:%S.%f%z" if "." in texte_date else "%Y-%m-%dT%H:%M:%S%z"
            date = datetime.strptime(texte_date, format_date)
            if date.tzinfo is None:
                raise ValueError("Fuseau absent")
            dates[numero] = date
        except ValueError:
            anomalies.append((numero, uri, "modifiedDate absente ou invalide"))
        groupes[uri].append((numero, ligne))

    doublons = []
    conflits = []
    for uri, versions in groupes.items():
        if len(versions) > 1:
            differences = [c for c in champs if len({r[c] for _, r in versions}) > 1]
            doublons.append((uri, len(versions), ", ".join(differences) or "aucune"))
            if set(differences) - {"modifiedDate"}:
                conflits.append((uri, ", ".join(differences)))
    tableau("URI répétées dans la source", ["URI", "Lignes", "Colonnes différentes"], doublons)
    if anomalies or conflits:
        tableau("Anomalies bloquantes", ["Ligne", "URI", "Motif"], anomalies)
        tableau("Conflits bloquants", ["URI", "Colonnes"], conflits)
        raise ValueError("Export annulé : validation humaine nécessaire.")

    resultat = []
    for uri, versions in sorted(groupes.items()):
        _, ligne = max(versions, key=lambda v: dates[v[0]])
        # Ne pas découper sur les virgules : elles peuvent appartenir au libellé.
        synonymes = ligne["altLabels"].splitlines() if ligne["altLabels"] else []
        if any(not s.strip() for s in synonymes):
            raise ValueError(f"Synonyme vide dans la liste source : {uri}")
        resultat.append({
            "skillUri": uri,
            "competence": ligne["preferredLabel"],
            "type_competence": ligne["skillType"],
            "altLabels": json.dumps(synonymes, ensure_ascii=False),
        })

    champs_c, relations = lire(CONSOLIDE)
    if not {"skillUri", "competence", "type_competence"}.issubset(champs_c):
        raise ValueError("Colonnes nécessaires absentes de la table consolidée")
    index = {r["skillUri"]: r for r in resultat}
    inconnues = {r["skillUri"] for r in relations} - set(index)
    ecarts = []
    for r in relations:
        if r["skillUri"] in index:
            cible = index[r["skillUri"]]
            # Le notebook remplace explicitement les types absents par ce texte.
            if (r["competence"] != cible["competence"] or
                    r["type_competence"] != (cible["type_competence"] or "non renseigné")):
                ecarts.append(r)
    tableau("Correspondance avec le consolidé", ["Contrôle", "Résultat"], [
        ("Relations lues", len(relations)),
        ("URI distinctes du consolidé", len({r['skillUri'] for r in relations})),
        ("URI du consolidé absentes du dictionnaire", len(inconnues)),
        ("Relations avec écart de libellé ou de type", len(ecarts)),
        ("URI du dictionnaire absentes du consolidé, conservées", len(set(index) - {r['skillUri'] for r in relations})),
    ])
    if inconnues or ecarts:
        raise ValueError("Export annulé : incohérence avec le consolidé")

    listes = [json.loads(r["altLabels"]) for r in resultat]
    labels = Counter(r["competence"] for r in resultat)
    tableau("Effectifs et contrôles", ["Contrôle", "Résultat"], [
        ("Lignes source", len(sources)),
        ("Dates source présentes et valides", len(dates)),
        ("Groupes d'URI répétées", len(doublons)),
        ("Occurrences supplémentaires résolues par date", len(sources) - len(resultat)),
        ("Conflits hors date", len(conflits)),
        ("Compétences du dictionnaire", len(resultat)),
        ("Doublons d'URI en sortie", len(resultat) - len(index)),
        ("Concepts avec synonymes", sum(bool(s) for s in listes)),
        ("Concepts sans synonymes (liste vide)", sum(not s for s in listes)),
        ("Mentions de synonymes officiels", sum(map(len, listes))),
        ("Listes contenant des synonymes répétés, conservés", sum(len(s) != len(set(s)) for s in listes)),
        ("Libellés principaux partagés par plusieurs URI", sum(n > 1 for n in labels.values())),
    ])
    tableau("Valeurs manquantes", ["Colonne", "Cellules vides"], [
        (c, sum(not r[c].strip() for r in resultat)) for c in COLONNES
    ])
    tableau("Types de compétences", ["Type source", "Concepts"], sorted(
        ((t or "(absent, conservé vide)", n) for t, n in Counter(r["type_competence"] for r in resultat).items())
    ))
    tableau("Concepts sans type", ["URI", "Libellé"], [
        (r["skillUri"], r["competence"]) for r in resultat if not r["type_competence"]
    ])

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    with SORTIE.open("x", encoding="utf-8-sig", newline="") as fichier:
        ecrivain = csv.DictWriter(fichier, fieldnames=COLONNES)
        ecrivain.writeheader()
        ecrivain.writerows(resultat)
    champs_export, relu = lire(SORTIE)
    if champs_export != COLONNES or relu != resultat:
        raise ValueError("Échec du contrôle de relecture de l'export")
    for r in relu:
        if not isinstance(json.loads(r["altLabels"]), list):
            raise ValueError("altLabels n'est pas une liste JSON")
    if any(empreinte(p) != valeur for p, valeur in avant.items()):
        raise RuntimeError("Une entrée a changé pendant la préparation")
    tableau("Export", ["Contrôle", "Résultat"], [
        ("Fichier", SORTIE.relative_to(ROOT)),
        ("Encodage", "UTF-8 avec BOM"),
        ("Relecture identique", "oui"),
        ("Listes JSON valides", len(relu)),
        ("Empreintes SHA-256 des entrées inchangées", "oui"),
    ])


if __name__ == "__main__":
    main()
