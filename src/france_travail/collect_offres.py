# ============================================================
# TER M1 MIASHS - France Travail x ESCO
# Collecte des offres d'emploi Data / IA
# ============================================================

import os
import json
import requests

from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv


# ============================================================
# 1. CHARGEMENT DES IDENTIFIANTS API
# ============================================================

# Charge les variables présentes dans le fichier .env
# Le CLIENT_ID et le CLIENT_SECRET ne sont donc pas écrits
# directement dans le code ni envoyés sur GitHub.
load_dotenv(override=True)

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")


# ============================================================
# 2. PARAMÈTRES DE NOTRE ÉTUDE
# ============================================================

# Métiers Data / IA définis dans le périmètre du TER
METIERS = [
    "Data Analyst",
    "Data Scientist",
    "Data Engineer",
    "Machine Learning Engineer",
    "Développeur IA"
]

# Types de contrats étudiés
CONTRATS = [
    "CDI",
    "CDD",
    "Alternance"
]

# Endpoint officiel de recherche des offres
API_URL = (
    "https://api.francetravail.io/"
    "partenaire/offresdemploi/v2/offres/search"
)

# URL permettant d'obtenir le token OAuth2
AUTH_URL = (
    "https://entreprise.francetravail.fr/"
    "connexion/oauth2/access_token"
)

# Période souhaitée : 1 an
date_maximum = datetime.now(timezone.utc)
date_minimum = date_maximum - timedelta(days=365)

DATE_MINIMUM = date_minimum.strftime("%Y-%m-%dT%H:%M:%SZ")
DATE_MAXIMUM = date_maximum.strftime("%Y-%m-%dT%H:%M:%SZ")

# ============================================================
# 3. AUTHENTIFICATION FRANCE TRAVAIL
# ============================================================

def get_token():
    """
    Récupère un token OAuth2 permettant d'appeler
    l'API Offres d'emploi de France Travail.
    """

    params = {
        "realm": "/partenaire"
    }

    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "api_offresdemploiv2 o2dsoffre"
    }

    headers = {
        "Content-Type":
            "application/x-www-form-urlencoded"
    }

    response = requests.post(
        AUTH_URL,
        params=params,
        data=data,
        headers=headers,
        timeout=30
    )

    # Arrête le programme si l'authentification échoue
    response.raise_for_status()

    # On récupère uniquement le token
    return response.json()["access_token"]


# ============================================================
# 4. RECHERCHE DES OFFRES AVEC PAGINATION
# ============================================================

def rechercher_offres(token, metier, contrat=None):
    """
    Recherche toutes les offres correspondant à un métier.

    Si contrat est renseigné :
        recherche uniquement CDI ou CDD.

    La fonction gère automatiquement la pagination.
    """

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    toutes_les_offres = []

    # L'API permet maximum 150 résultats par page
    taille_page = 150

    # Premier résultat demandé
    debut = 0

    while True:

        fin = debut + taille_page - 1

        params = {
            "motsCles": metier,
            "range": f"{debut}-{fin}",
            "minCreationDate": DATE_MINIMUM,
            "maxCreationDate": DATE_MAXIMUM
        }

        # Le filtre contrat est facultatif
        if contrat is not None:
            params["typeContrat"] = contrat

        response = requests.get(
            API_URL,
            headers=headers,
            params=params,
            timeout=30
        )

        # 200 = tous les résultats demandés
        # 206 = résultats partiels à cause de la pagination
        if response.status_code not in (200, 206):
            print(
                f"Erreur : {metier} - {contrat} "
                f"(HTTP {response.status_code})"
            )
            print(response.text)
    
            break

        data = response.json()

        offres = data.get("resultats", [])

        toutes_les_offres.extend(offres)

        # Si moins de 150 offres sont retournées,
        # cela signifie qu'il n'y a plus de page suivante.
        if len(offres) < taille_page:
            break

        # Page suivante
        debut += taille_page

        # Limite imposée par l'API
        if debut > 3000:
            print(
                f"Limite de pagination atteinte "
                f"pour {metier}"
            )
            break

    return toutes_les_offres


# ============================================================
# 5. RECHERCHE DES OFFRES EN ALTERNANCE
# ============================================================

def rechercher_alternance(token, metier):
    """
    Recherche toutes les offres correspondant au métier
    puis conserve uniquement celles marquées
    alternance = True par France Travail.
    """

    # On récupère toutes les offres du métier
    offres = rechercher_offres(
        token=token,
        metier=metier,
        contrat=None
    )

    # On conserve seulement les alternances
    offres_alternance = [
        offre
        for offre in offres
        if offre.get("alternance") is True
    ]

    return offres_alternance


# ============================================================
# 6. SUPPRESSION DES DOUBLONS
# ============================================================

def dedoublonner(offres):
    """
    Supprime les doublons grâce à l'identifiant unique
    France Travail : id.
    """

    offres_uniques = {}

    for offre in offres:

        identifiant = offre.get("id")

        if identifiant:
            offres_uniques[identifiant] = offre

    return list(offres_uniques.values())


# ============================================================
# 7. LANCEMENT DE LA COLLECTE
# ============================================================

def main():

    print("=" * 60)
    print("COLLECTE FRANCE TRAVAIL - TER MIASHS")
    print("=" * 60)

    # --------------------------------------------------------
    # Authentification
    # --------------------------------------------------------

    print("\nAuthentification...")

    token = get_token()

    print("Authentification réussie.")


    # --------------------------------------------------------
    # Structure qui contiendra les résultats
    # --------------------------------------------------------

    resultats = {}

    toutes_les_offres = []


    # --------------------------------------------------------
    # Collecte métier par métier
    # --------------------------------------------------------

    for metier in METIERS:

        print("\n" + "-" * 60)
        print(metier)
        print("-" * 60)

        resultats[metier] = {
            "CDI": [],
            "CDD": [],
            "Alternance": []
        }


        # -------------------------------
        # CDI
        # -------------------------------

        offres_cdi = rechercher_offres(
            token,
            metier,
            "CDI"
        )

        # On évite de compter une alternance
        # une deuxième fois comme CDI
        offres_cdi = [
            offre
            for offre in offres_cdi
            if offre.get("alternance") is not True
        ]

        offres_cdi = dedoublonner(offres_cdi)

        resultats[metier]["CDI"] = offres_cdi

        toutes_les_offres.extend(offres_cdi)

        print(
            f"CDI          : {len(offres_cdi)}"
        )


        # -------------------------------
        # CDD
        # -------------------------------

        offres_cdd = rechercher_offres(
            token,
            metier,
            "CDD"
        )

        # Même logique :
        # alternance traitée séparément
        offres_cdd = [
            offre
            for offre in offres_cdd
            if offre.get("alternance") is not True
        ]

        offres_cdd = dedoublonner(offres_cdd)

        resultats[metier]["CDD"] = offres_cdd

        toutes_les_offres.extend(offres_cdd)

        print(
            f"CDD          : {len(offres_cdd)}"
        )


        # -------------------------------
        # Alternance
        # -------------------------------

        offres_alt = rechercher_alternance(
            token,
            metier
        )

        offres_alt = dedoublonner(offres_alt)

        resultats[metier]["Alternance"] = offres_alt

        toutes_les_offres.extend(offres_alt)

        print(
            f"Alternance   : {len(offres_alt)}"
        )


    # ========================================================
    # 8. SUPPRESSION DES DOUBLONS GLOBAUX
    # ========================================================

    nombre_avant = len(toutes_les_offres)

    offres_uniques = dedoublonner(
        toutes_les_offres
    )

    nombre_apres = len(offres_uniques)


    # ========================================================
    # 9. CRÉATION DU RÉSUMÉ
    # ========================================================

    resume = {}

    for metier in METIERS:

        resume[metier] = {
            "CDI":
                len(resultats[metier]["CDI"]),

            "CDD":
                len(resultats[metier]["CDD"]),

            "Alternance":
                len(resultats[metier]["Alternance"])
        }


    # ========================================================
    # 10. MÉTADONNÉES DE COLLECTE
    # ========================================================

    date_collecte_iso = datetime.now(
        timezone.utc
    ).isoformat()

    metadata = {

        "source":
            "France Travail",

        "api":
            "API Offres d'emploi v2",

        "endpoint":
            API_URL,

        "date_collecte":
            date_collecte_iso,

        "periode_recherche":
            "1 an maximum",

        "date_minimum":
            DATE_MINIMUM,

        "metiers":
            METIERS,

        "contrats":
            [
                "CDI",
                "CDD",
                "Alternance"
            ],

        "nombre_occurrences_avant_dedoublonnage":
            nombre_avant,

        "nombre_offres_uniques":
            nombre_apres
    }


    # ========================================================
    # 11. STRUCTURE DU JSON FINAL
    # ========================================================

    fichier_final = {

        "metadata":
            metadata,

        "resume":
            resume,

        "resultats_par_metier":
            resultats,

        "offres_uniques":
            offres_uniques
    }


    # ========================================================
    # 12. SAUVEGARDE
    # ========================================================

    date_fichier = datetime.now().strftime(
        "%Y-%m-%d_%H-%M"
    )

    nom_fichier = (
        "data/raw/"
        f"offres_france_travail_{date_fichier}.json"
    )

    with open(
        nom_fichier,
        "w",
        encoding="utf-8"
    ) as fichier:

        json.dump(
            fichier_final,
            fichier,
            ensure_ascii=False,
            indent=2
        )


    # ========================================================
    # 13. AFFICHAGE DU BILAN
    # ========================================================

    print("\n")
    print("=" * 60)
    print("RÉSUMÉ DE LA COLLECTE")
    print("=" * 60)

    for metier in METIERS:

        print(f"\n{metier}")

        print(
            "  CDI         :",
            resume[metier]["CDI"]
        )

        print(
            "  CDD         :",
            resume[metier]["CDD"]
        )

        print(
            "  Alternance  :",
            resume[metier]["Alternance"]
        )

    print("\n" + "-" * 60)

    print(
        "Occurrences collectées :",
        nombre_avant
    )

    print(
        "Offres uniques :",
        nombre_apres
    )

    print(
        "Fichier sauvegardé :",
        nom_fichier
    )

    print("=" * 60)


# ============================================================
# 14. POINT D'ENTRÉE DU PROGRAMME
# ============================================================

if __name__ == "__main__":
    main()