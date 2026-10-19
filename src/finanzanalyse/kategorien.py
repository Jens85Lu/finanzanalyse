
KATEGORIEN = {
    "Lebensmittel": [
        "rewe",
        "edeka",
        "aldi",
        "lidl",
        "kaufland",
        "aho.bio",
        "topfruits",
        "restaurant",
        "cafe",
        "bäckerei",
        "bio markt",
        "supermarkt",
        "drogerie"
    ],
    "LifePlus": [
        "lifeplus"
    ],
    "Gesundheit": [
        "apotheke",
        "sport",
        "zahnarzt",
        "krankenkasse"
    ],
    "Reisen": [
        "reise"
    ],
    "Garten": [
        "tria terra",
        "obi sagt danke",
        "hornbach",
        "Marko Heckel",
        "garten"
    ],
    "Wohnen": [
        "miete",
        "kjg",
        "vermieter",
        "nebenkosten",
        "vodafone",
        "eprimo",
        "handwerker",
        "stadt dresden"
    ],
    "Handy": [
        "drillisch"
    ],
    "Mobilität": [
        "shell",
        "aral",
        "deutsche bahn",
        "db vertrieb",
        "dvb ag",
        "monatskarte",
        "carlundcarla",
        "pitstop",
        "tankstelle"
    ],
    "Freizeit": [
        "kino",
        "museum",
        "schwimmbad",
        "fun",
        "amzn mktp",
        "amazon",
        "ablefy",  
        "fahrrad",
        "rosebikes",
        "bike",
        "fetzer",
        "thalia",
        "bibliothek",
        "buchhandlung",
        "streaming",
        "musik",
        
    ],
    "Versicherung": [
        "interrisk",
        "allianz",
        "huk-coburg",
        "versicherung"
    ],
    "Einkommen": [
        "bundesagentur",
        "hauptkasse",
        "arbeitgeber"
    ],
    "Umbuchung": [
        "Sparen"
    ],
    "Familie/Freunde": [
        "Gisela Ludwig",
        "Lars Ludwig",
        "Tobias Ludwig"
    ],
    "Bar": [
        "bargeldauszahlung"
    ]   
    
}

def kategorisiere_buchung(row):
    empfaenger = str(
        row["auftraggeber_empfaenger"]
    ).casefold()

    verwendungszweck = str(row["verwendungszweck"]).casefold()

    # Regel für ING-Kontoführungsgebühren
    if ("ing" in empfaenger and "kontofuehrungsentgelt" in verwendungszweck):
        return "Kontoführungsgebühr"

    text = f"{empfaenger} {verwendungszweck}"

    for kategorie, stichwoerter in KATEGORIEN.items():
        if any(
            stichwort.casefold() in text
            for stichwort in stichwoerter
        ):
            return kategorie

    return "Unkategorisiert"