"""
Nettoyage des offres France Travail.

Lit un fichier d'offres, applique les règles du dictionnaire de données
(data/processed/dictionnaire_donnees.md) et écrit :
- un fichier d'offres propres ;
- un fichier des offres retirées, avec le motif de chaque retrait.

Utilisation (depuis la racine du dépôt) :
    python src/france_travail/nettoyage.py                  # vraies offres (JSON)
    python src/france_travail/nettoyage.py data/raw/offres_fictives.csv   # test
"""

import json
import sys
from pathlib import Path

import pandas as pd

# --- Chemins ---------------------------------------------------------------
DOSSIER = Path(__file__).resolve().parents[2]
FICHIER_ENTREE = DOSSIER / "data" / "raw" / "offres_france_travail_2026-10-31_13-43.json"
FICHIER_SORTIE = DOSSIER / "data" / "processed" / "offres_propres.csv"
FICHIER_RETIREES = DOSSIER / "data" / "processed" / "offres_retirees.csv"
DOSSIER_INSEE = DOSSIER / "data" / "raw" / "insee"

# --- Correspondance avec l'API (colonne « source API » du dictionnaire) -----
CHAMPS_API = {
    "job_id": "id",
    "date_creation": "dateCreation",
    "titre": "intitule",
    "description": "description",
    "code_rome": "romeCode",
    "intitule_rome": "romeLibelle",
    "entreprise": "entreprise.nom",
    "commune": "lieuTravail.commune",
    "lieu_libelle": "lieuTravail.libelle",
    "type_contrat": "typeContrat",
    "experience": "experienceExige",
    "formation": "formations",
    "competences": "competences",
    "date_actualisation": "dateActualisation",
    "alternance": "alternance",
    "salaire": "salaire.libelle",
}
NIVEAUX_EXPERIENCE = {"D": "débutant", "S": "souhaitée", "E": "exigée"}

# --- Règles du dictionnaire ------------------------------------------------
# Doit correspondre exactement aux colonnes « obligatoire = oui »
# des sections 1 et 2 du dictionnaire de données.
COLONNES_OBLIGATOIRES = ["job_id", "date_creation", "titre", "description",
                         "type_contrat", "date_collecte", "source"]
CONTRATS_GARDES = ["CDI", "CDD"]
COLONNES_DATES = ["date_creation", "date_actualisation", "date_collecte"]
COLONNES_DOUBLON_PROBABLE = ["titre", "entreprise", "description"]

# Fenêtre temporelle : on garde les offres créées dans l'année qui précède
# la date de référence. Si DATE_REFERENCE vaut None, on prend la date de
# collecte la plus récente du fichier.
DATE_REFERENCE = None
DUREE_FENETRE = pd.DateOffset(years=1)

# Stages : l'API les classe souvent en CDI ou CDD, on les repère par le titre.
MOTIF_STAGE = r"\bstage\b|stagiaire"

# Codes ROME du cœur du périmètre Data/IA (liste à valider par l'équipe) :
# data engineer, data analyst, data scientist, ingénieur IA, spécialiste IA
# embarquée, Chief Data Officer. Une offre hors de cette liste est signalée
# dans metier_a_verifier, mais n'est pas retirée.
CODES_ROME_PERIMETRE = ["M1811", "M1419", "M1405", "M1889", "M1873", "M1423"]


def convertir_json(chemin):
    """Convertit le JSON de la collecte au format du dictionnaire. Seules les
    colonnes de CHAMPS_API sont gardées : les contacts ne sont pas repris."""
    with open(chemin, encoding="utf-8") as f:
        brut = json.load(f)

    offres = pd.json_normalize(brut["offres_uniques"])
    df = offres.reindex(columns=list(CHAMPS_API.values()))
    df.columns = list(CHAMPS_API.keys())

    # Les valeurs multiples sont gardées en texte JSON, [] si l'offre n'en a pas.
    for col in ["formation", "competences"]:
        df[col] = df[col].apply(
            lambda v: json.dumps(v if isinstance(v, list) else [], ensure_ascii=False)
        )
    df["alternance"] = df["alternance"].astype(str)
    df["experience"] = df["experience"].map(NIVEAUX_EXPERIENCE)

    # Les métadonnées sont communes à tout le fichier, pas propres à chaque offre.
    metadata = brut["metadata"]
    df["date_collecte"] = metadata["date_collecte"]
    df["source"] = f"{metadata['source']} - {metadata['api']}"
    return df.replace("", pd.NA)


def charger(chemin):
    """1. Lire le fichier (JSON de la collecte, ou CSV de test). Tout est lu en
    texte pour ne pas perdre les zéros au début des codes (ex. commune 01001)."""
    if Path(chemin).suffix == ".json":
        return convertir_json(chemin)
    return pd.read_csv(chemin, dtype=str, keep_default_na=False, na_values=[""])


def typer(df):
    """2. Donner le bon type aux colonnes : dates (en UTC) et booléen."""
    for col in COLONNES_DATES:
        df[col] = pd.to_datetime(df[col], format="ISO8601", utc=True, errors="coerce")
    df["alternance"] = df["alternance"].str.lower().map({"true": True, "false": False})
    return df


def retirer(df, a_retirer, motif, retirees):
    """Retire les lignes indiquées et les ajoute aux offres retirées avec leur motif."""
    sortie = df[a_retirer].assign(motif=motif)
    retirees.append(sortie)
    return df[~a_retirer].copy()


def motif_incomplet(ligne):
    manquants = [c for c in COLONNES_OBLIGATOIRES if pd.isna(ligne[c])]
    return "champ obligatoire manquant : " + ", ".join(manquants)


def retirer_incompletes(df, retirees):
    """3. Une offre à laquelle il manque un champ obligatoire est retirée.
    Fait avant le dédoublonnage, pour ne jamais garder une version
    incomplète à la place d'une version complète."""
    incomplete = df[COLONNES_OBLIGATOIRES].isna().any(axis=1)
    sortie = df[incomplete].copy()
    sortie["motif"] = sortie.apply(motif_incomplet, axis=1)
    retirees.append(sortie)
    return df[~incomplete].copy()


def appliquer_perimetre(df, retirees):
    """4. Type de contrat : alternance si alternance = vrai,
    CDI / CDD gardés, tout le reste exclu (ex. intérim). Les stages sont
    retirés d'après le titre."""
    df.loc[df["alternance"] == True, "type_contrat"] = "alternance"
    hors_contrat = ~df["type_contrat"].isin(CONTRATS_GARDES + ["alternance"])
    df = retirer(df, hors_contrat, "contrat hors périmètre", retirees)

    stage = df["titre"].str.contains(MOTIF_STAGE, case=False, regex=True)
    return retirer(df, stage, "stage hors périmètre", retirees)


def appliquer_fenetre(df, retirees):
    """5. Fenêtre d'un an avant la date de référence (sur date_creation)."""
    reference = pd.Timestamp(DATE_REFERENCE, tz="UTC") if DATE_REFERENCE else df["date_collecte"].max()
    debut = reference - DUREE_FENETRE
    hors_fenetre = (df["date_creation"] < debut) | (df["date_creation"] > reference)
    return retirer(df, hors_fenetre, "hors fenêtre d'un an", retirees), debut, reference


def ajouter_geographie(df):
    """6. Déduire département et région du code commune, sinon du libellé du lieu."""
    communes = pd.read_csv(DOSSIER_INSEE / "v_commune_2026.csv", dtype=str)
    regions = pd.read_csv(DOSSIER_INSEE / "v_region_2026.csv", dtype=str)

    # Les communes déléguées / associées n'ont pas de département :
    # on reprend celui de leur commune de rattachement (COMPARENT).
    infos = communes.set_index("COM")[["DEP", "REG"]]
    infos = infos[~infos.index.duplicated()]
    sans_dep = communes["DEP"].isna() & communes["COMPARENT"].notna()
    for _, ligne in communes[sans_dep].iterrows():
        if ligne["COMPARENT"] in infos.index:
            infos.loc[ligne["COM"]] = infos.loc[ligne["COMPARENT"]]

    nom_region = regions.set_index("REG")["LIBELLE"]
    df["departement"] = df["commune"].map(infos["DEP"])
    df["region"] = df["commune"].map(infos["REG"]).map(nom_region)

    # Sans commune reconnue, le libellé du lieu donne souvent le département
    # (ex. « 75 - Paris »). Un libellé sans code (« Île-de-France ») reste vide.
    region_du_dep = pd.read_csv(DOSSIER_INSEE / "v_departement_2026.csv", dtype=str).set_index("DEP")["REG"]
    code = df["lieu_libelle"].str.extract(r"^(\d{2,3}|2[AB]) - ", expand=False)
    a_completer = df["departement"].isna() & code.isin(region_du_dep.index)
    df.loc[a_completer, "departement"] = code[a_completer]
    df.loc[a_completer, "region"] = code[a_completer].map(region_du_dep).map(nom_region)
    return df


def retirer_doublons_exacts(df, retirees):
    """7. Même job_id : on garde la version la plus récente.
    Date utilisée : date_actualisation, ou date_creation si elle manque,
    puis date_collecte pour départager deux versions de même date."""
    df["_date_version"] = df["date_actualisation"].fillna(df["date_creation"])
    df = df.sort_values(["job_id", "_date_version", "date_collecte"])
    doublon = df.duplicated("job_id", keep="last")
    df = retirer(df, doublon, "doublon exact (version plus ancienne)", retirees)
    for r in retirees:
        r.drop(columns="_date_version", errors="ignore", inplace=True)
    return df.drop(columns="_date_version")


def signaler_doublons_probables(df):
    """8. Même titre + entreprise + description : on signale, on ne supprime pas."""
    df["doublon_suspect"] = df.duplicated(COLONNES_DOUBLON_PROBABLE, keep=False)
    return df


def signaler_metiers_a_verifier(df):
    """9. Code ROME hors du cœur du périmètre : on signale, on ne supprime pas."""
    df["metier_a_verifier"] = ~df["code_rome"].isin(CODES_ROME_PERIMETRE)
    return df


def main():
    entree = sys.argv[1] if len(sys.argv) > 1 else FICHIER_ENTREE
    df = charger(entree)
    nb_initial = len(df)
    retirees = []

    df = typer(df)
    df = retirer_incompletes(df, retirees)
    df = appliquer_perimetre(df, retirees)
    df, debut, reference = appliquer_fenetre(df, retirees)
    df = ajouter_geographie(df)
    df = retirer_doublons_exacts(df, retirees)
    df = signaler_doublons_probables(df)
    df = signaler_metiers_a_verifier(df)

    retirees = pd.concat(retirees)
    df.to_csv(FICHIER_SORTIE, index=False, date_format="%Y-%m-%d %H:%M:%S")
    retirees.to_csv(FICHIER_RETIREES, index=False, date_format="%Y-%m-%d %H:%M:%S")

    # --- 10. Petit rapport ---------------------------------------------------
    print(f"Offres lues      : {nb_initial}")
    print(f"Fenêtre retenue  : du {debut:%Y-%m-%d} au {reference:%Y-%m-%d} (date de référence)")
    print(f"Offres retirées  : {len(retirees)}")
    for _, l in retirees.iterrows():
        print(f"  - {l['job_id']} : {l['motif']}")
    print(f"Offres finales   : {len(df)}")
    print(f"Doublons suspects: {df['doublon_suspect'].sum()}")
    print(f"Métiers à vérifier: {df['metier_a_verifier'].sum()}")
    print("\nValeurs manquantes par colonne :")
    print(df.isna().sum()[lambda s: s > 0].to_string())
    print(f"\nFichiers écrits : {FICHIER_SORTIE.name}, {FICHIER_RETIREES.name}")


if __name__ == "__main__":
    main()
