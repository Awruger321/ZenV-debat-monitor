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
    "Onbegrepen gedrag": ["onbegrepen gedrag", "verwarde personen", "verward gedrag", "onbegrepen personen", "LVB", "licht verstandelijke beperking", "psychische kwetsbaarheid", "crisisdienst", "WVGGZ", "WZD", "E33", "bemoeizorg", "straattriage", "ggz"],
    "Dak- en thuisloosheid": ["dakloos", "thuisloos", "maatschappelijke opvang", "beschermd wonen", "nachtopvang", "skaeve huse", "housing first"],
    "Mensenhandel": ["mensenhandel", "loverboy", "seksuele uitbuiting", "criminele uitbuiting", "uitbuiting", "gedwongen prostitutie", "mensensmokkel", "arbeidsuitbuiting"],
    "PGA (Persoonsgerichte Aanpak)": ["persoonsgerichte aanpak", "pga", "veelpleger", "top600", "top400", "ISD", "zorg- en veiligheidshuis", "casusregie", "procesregie", "top1000", "brusjesaanpak", "HIC"],
    "Detentie & Terugkeer": ["detentie", "reclassering", "gevangeniswezen", "tbs", "re-integratie", "terugkeerbeleid", "na-zorg", "ex-gedetineerden", "forensische zorg", "wfz", "recidive", "bestuurlijk akkoord"],
    "Suïcidepreventie": ["suïcide", "zelfdoding", "113", "zelfmoord", "suïcidaliteit"],
    "Verslaving": ["verslaving", "verslavingszorg", "drugs", "crack", "middelengebruik", "drugsbeleid", "dubbele diagnose", "overlast", "gebruikersruimte"],
    "Jeugdcriminaliteit": ["jeugdcriminaliteit", "jeugdbescherming", "jeugdreclassering", "criminele jeugdnetwerken", "ondermijning", "jonge aanwas", "preventie met gezag", "jeugdzorg"],
    "Seksueel Geweld & Femicide": ["seksueel geweld", "zeden", "zedendelict", "femicide", "vrouwenmoord", "huiselijk geweld", "partnergeweld", "intieme terreur", "eergerelateerd geweld"]
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
st.set_page_config(page_title="Z&V Monitor", page_icon="🏛️", layout="centered")

st.title("🏛️ Politieke Monitor: Zorg & Veiligheid")
st.write("Welkom! Klik op de knop hieronder om de geplande Tweede Kamerdebatten van de komende 30 dagen te scannen op onderwerpen rondom Zorg en Veiligheid.")

if st.button("Start de Scan & Genereer Excel", type="primary"):
    with st.spinner('De Tweede Kamer agenda wordt nu uitgelezen en geanalyseerd. Dit duurt ongeveer 10 tot 20 seconden...'):
        
        # Data Ophalen
        vandaag = datetime.now()
        volgende_maand = vandaag + timedelta(days=30)
        start_datum = vandaag.strftime("%Y-%m-%dT00:00:00Z")
        eind_datum = volgende_maand.strftime("%Y-%m-%dT23:59:59Z")
        
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
                    "Datum": datum_str, "Soort Activiteit": soort, "Commissie / Ministerie": commissie,
                    "Thema's": ", ".join(list(match_themas)), "Titel": volledige_titel,
                    "Gevonden Trefwoorden": ", ".join(list(match_woorden)),
                    "Relevante Agendapunten": "\n- ".join(relevante_agendapunten) if relevante_agendapunten else "(Titel is relevant)",
                    "Link naar Debat": link
                })

    if not export_data:
        st.warning("Er zijn geen relevante debatten gevonden in de komende 30 dagen.")
    else:
        st.success(f"🎉 Klaar! Er zijn {len(export_data)} relevante debatten gevonden.")
        
        # Excel genereren in het geheugen van de web-app
        df = pd.DataFrame(export_data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Debatten')
        excel_data = output.getvalue()
        
        # Een grote downloadknop maken
        st.download_button(
            label="📥 Download Excel Overzicht",
            data=excel_data,
            file_name=f"ZorgVeiligheid_Agenda_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
