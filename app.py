import streamlit as st
import requests
import pandas as pd
import urllib.parse
import re
import io
from datetime import datetime, timedelta

# ==========================================
# 1. JOUW THEMA'S & ZOEKWOORDEN
# ==========================================
THEMAS = {
    THEMAS = {
    "Onbegrepen gedrag": [
        "onbegrepen gedrag", "verwarde personen", "verward gedrag", "onbegrepen personen",
        "LVB", "licht verstandelijke beperking", "psychische kwetsbaarheid", "psychiatrie",
        "veiligheidsrisico's", "gedwongen zorg", "zorgmijdend gedrag",
        "openbare orde en veiligheid", "maatschappelijke impact", "crisisdienst",
        "WVGGZ", "WZD", "E33", "bemoeizorg", "straattriage", "GGZ"
    ],
    "Dak- en thuisloosheid": [
        "dakloos", "thuisloos", "maatschappelijke opvang", "beschermd wonen",
        "nachtopvang", "skaeve huse", "housing first"
    ],
    "Mensenhandel": [
        "mensenhandel", "loverboy", "seksuele uitbuiting", "criminele uitbuiting",
        "uitbuiting", "gedwongen prostitutie", "mensensmokkel", "arbeidsuitbuiting",
        "ondermijning", "criminele organisaties"
    ],
    "PGA (Persoonsgerichte Aanpak)": [
        "persoonsgerichte aanpak", "pga", "veelpleger", "top600", "top400", "ISD",
        "zorg- en veiligheidshuis", "casusregie", "procesregie", "top1000",
        "brusjesaanpak", "HIC", "levensloopaanpak",
        "toekomstscenario kind- en gezinsbescherming"
    ],
    "Detentie & Terugkeer": [
        "detentie", "reclassering", "gevangeniswezen", "tbs", "re-integratie",
        "terugkeerbeleid", "na-zorg", "ex-gedetineerden", "forensische zorg",
        "wfz", "recidive", "bestuurlijk akkoord", "voorwaardelijke straf",
        "bijzondere voorwaarden", "enkelband", "elektronische controle",
        "voorwaardelijke invrijheidsstelling", "penitentiair programma", "ISD",
        "inrichting stelselmatige daders", "veelplegers", "re integratieplan",
        "recidiverisico", "risicotaxatie", "reclasseringsadvies",
        "reclasseringstoezicht", "5 basisvoorwaarden", "adolescentenstrafrecht"
    ],
    "Suïcidepreventie": [
        "suïcide", "zelfdoding", "113", "zelfmoord", "suïcidaliteit"
    ],
    "Verslaving": [
        "verslaving", "verslavingszorg", "alcohol", "drugs", "crack",
        "middelengebruik", "middelenmisbruik", "afhankelijkheid",
        "drugscriminaliteit", "vermogensdelicten", "veelplegers",
        "alcoholgerelateerd geweld", "drugsbeleid", "dubbele diagnose",
        "overlast", "gebruikersruimte"
    ],
    "Jeugdcriminaliteit": [
        "jeugdcriminaliteit", "jeugdbescherming", "jeugdreclassering",
        "adolescentenstrafrecht", "criminele jeugdnetwerken", "ondermijning",
        "jonge aanwas", "preventie met gezag", "jeugdzorg"
    ],
    "Seksueel Geweld & Femicide": [
        "seksueel geweld", "zeden", "zedendelict", "risicotaxatie",
        "maatschappelijke impact", "hands on", "hands off", "femicide",
        "vrouwenmoord", "huiselijk geweld", "kindermishandeling",
        "partnergeweld", "intieme terreur", "eergerelateerd geweld", "eerwraak"
    ]
}

EXACTE_WOORDEN = [
    "pga", "isd", "hic", "113", "lvb", "wzd", "wvggz", "e33", "wfz", "ggz"
]
}

EXACTE_WOORDEN = ["pga", "isd", "hic", "113", "lvb", "wzd", "wvggz", "e33", "wfz"]

def check_tekst_voor_themas(tekst):
    gevonden_themas = set()
    gevonden_woorden = set()
    tekst_lower = tekst.lower()
    for thema, woorden in THEMAS.items():
        for w in woorden:
            w_lower = w.lower()
            if w_lower in EXACTE_WOORDEN:
                if re.search(rf'\b{re.escape(w_lower)}\b', tekst_lower):
                    gevonden_themas.add(thema)
                    gevonden_woorden.add(w)
            else:
                if w_lower in tekst_lower:
                    gevonden_themas.add(thema)
                    gevonden_woorden.add(w)
    return gevonden_themas, gevonden_woorden

# ==========================================
# 2. STREAMLIT INTERFACE
# ==========================================
st.set_page_config(page_title="Z&V Monitor", page_icon="🏛️", layout="wide")

st.title("🏛️ Politieke Monitor: Zorg & Veiligheid")
st.write("Welkom! Hieronder vind je de geplande Tweede Kamerdebatten rondom Zorg & Veiligheid. Op het scherm zie je de planning voor de **komende 30 dagen**. Nieuwe toevoegingen van de afgelopen **7 dagen** worden groen gemarkeerd. Via de knop onderaan kun je het complete **halfjaar-overzicht** downloaden als Excel.")

if st.button("Start de Scan", type="primary"):
    with st.spinner('De agenda van het komende halfjaar wordt uitgelezen en geanalyseerd...'):
        
        # Tijden instellen
        vandaag = datetime.now()
        komend_halfjaar = vandaag + timedelta(days=183)
        komende_30_dagen = vandaag + timedelta(days=30)
        zeven_dagen_geleden = vandaag - timedelta(days=7) # <-- Aangepast naar 7 dagen!
        
        start_datum = vandaag.strftime("%Y-%m-%dT00:00:00Z")
        eind_datum = komend_halfjaar.strftime("%Y-%m-%dT23:59:59Z")
        grens_30_dagen_str = komende_30_dagen.strftime("%Y-%m-%d")
        
        # API Uitlezen
        url = "https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0/Activiteit"
        alle_activiteiten = []
        skip = 0
        top = 250
        
        while True:
            params = {"$filter": f"Datum gt {start_datum} and Datum lt {eind_datum}", "$orderby": "Datum asc", "$top": top, "$skip": skip, "$expand": "Agendapunt"}
            try:
                response = requests.get(url, params=params)
                batch = response.json().get('value', [])
                alle_activiteiten.extend(batch)
                if len(batch) < top:
                    break
                skip += top
            except Exception:
                break
                
        # Data Filteren
        export_data = []
        for act in alle_activiteiten:
            naam = act.get('Naam') or ''
            korte_naam = act.get('KorteNaam') or ''
            onderwerp = act.get('Onderwerp') or ''
            omschrijving = act.get('Noot') or ''
            soort = act.get('Soort', 'Onbekend')
            
            volledige_titel = f"{naam} - {korte_naam} - {onderwerp}".strip(' -')
            if not volledige_titel:
                continue
                
            nummer = act.get('Nummer', '')
            link = f"https://www.tweedekamer.nl/zoeken?qry={nummer}" if nummer else f"https://www.tweedekamer.nl/zoeken?qry={urllib.parse.quote(volledige_titel)}"

            commissie = act.get('VoortouwCommissieNaam') or act.get('Voortouwnaam') or ""
            if not commissie:
                commissie = "Plenair (Volledige Kamer)" if "plenair" in soort.lower() else "Niet gespecificeerd"

            gewijzigd_op_str = act.get('GewijzigdOp', '')
            is_recent = False
            if gewijzigd_op_str:
                try:
                    datum_gewijzigd = datetime.strptime(gewijzigd_op_str[:10], "%Y-%m-%d")
                    # Check of de wijziging in de afgelopen 7 dagen was
                    if datum_gewijzigd >= zeven_dagen_geleden:
                        is_recent = True
                except Exception:
                    pass

            hoofd_tekst = f"{volledige_titel} {omschrijving}"
            match_themas, match_woorden = check_tekst_voor_themas(hoofd_tekst)
            
            relevante_agendapunten = []
            for ap in act.get('Agendapunt', []):
                ap_tekst = ap.get('Onderwerp') or ap.get('Naam') or ap.get('KorteNaam') or ''
                if ap_tekst:
                    ap_themas, ap_woorden = check_tekst_voor_themas(ap_tekst)
                    if ap_themas: 
                        match_themas.update(ap_themas)
                        match_woorden.update(ap_woorden)
                        relevante_agendapunten.append(ap_tekst.strip())
            
            if match_themas:
                raw_datum = act.get('Datum', '')
                datum_str = raw_datum.split('T')[0] if 'T' in raw_datum else raw_datum
                export_data.append({
                    "Nieuw/Gewijzigd (7 dgn)": "🟢 JA" if is_recent else "-", # <-- Aangepaste kolomnaam
                    "Datum": datum_str, 
                    "Soort Activiteit": soort, 
                    "Commissie / Ministerie": commissie,
                    "Thema's": ", ".join(list(match_themas)), 
                    "Titel": volledige_titel,
                    "Gevonden Trefwoorden": ", ".join(list(match_woorden)),
                    "Relevante Agendapunten": "\n- ".join(relevante_agendapunten) if relevante_agendapunten else "(Titel is relevant)",
                    "Link naar Debat": link
                })

    if not export_data:
        st.warning("Er zijn geen relevante debatten gevonden voor het komende halfjaar.")
    else:
        # Maak het grote dataframe voor Excel
        df_full = pd.DataFrame(export_data)
        
        # Maak een kleiner dataframe aan specifiek voor op het scherm (max 30 dagen)
        df_30_dagen = df_full[df_full['Datum'] <= grens_30_dagen_str]
        
        st.success(f"🎉 Klaar! Er zijn {len(df_full)} relevante debatten gevonden, waarvan {len(df_30_dagen)} in de komende maand.")
        
        st.write("---")
        st.subheader("📅 Binnenkort op de agenda (komende 30 dagen)")
        
        if not df_30_dagen.empty:
            # We tonen een schone selectie van kolommen op het scherm (nu met 7 dgn)
            st.dataframe(
                df_30_dagen[["Datum", "Nieuw/Gewijzigd (7 dgn)", "Thema's", "Titel", "Commissie / Ministerie", "Link naar Debat"]],
                column_config={
                    "Link naar Debat": st.column_config.LinkColumn("Bekijk online")
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Er staan momenteel geen Z&V debatten gepland in de aankomende 30 dagen.")

        st.write("---")
        st.subheader("📊 Volledig overzicht downloaden (6 maanden)")
        st.write(f"In de Excel vind je alle details, inclusief de specifieke agendapunten en de gevonden trefwoorden voor de volle {len(df_full)} debatten.")
        
        # Genereer het Excel bestand op basis van het VOLLEDIGE (df_full) dataframe
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_full.to_excel(writer, index=False, sheet_name='Debatten')
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 Download Compleet Excel Overzicht",
            data=excel_data,
            file_name=f"ZorgVeiligheid_Agenda_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
