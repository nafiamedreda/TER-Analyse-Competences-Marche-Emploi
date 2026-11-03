import json


FICHIER_ENTREE = "data/raw/offres_france_travail_2026-10-31_13-43.json"

FICHIER_SORTIE = "data/raw/offres_france_travail_public_2026-10-31_13-43.json"


def supprimer_donnees_contact(obj):
    """
    Supprime récursivement les champs de contact
    inutiles pour notre analyse scientifique.
    """

    if isinstance(obj, dict):

        resultat = {}

        for cle, valeur in obj.items():

            # Champs que nous ne voulons pas publier
            if cle in ["contact", "agence"]:
                continue

            resultat[cle] = supprimer_donnees_contact(valeur)

        return resultat

    elif isinstance(obj, list):

        return [
            supprimer_donnees_contact(element)
            for element in obj
        ]

    else:
        return obj


with open(FICHIER_ENTREE, "r", encoding="utf-8") as f:
    data = json.load(f)


data_nettoyee = supprimer_donnees_contact(data)


with open(FICHIER_SORTIE, "w", encoding="utf-8") as f:
    json.dump(
        data_nettoyee,
        f,
        ensure_ascii=False,
        indent=2
    )


print("JSON public créé :", FICHIER_SORTIE)