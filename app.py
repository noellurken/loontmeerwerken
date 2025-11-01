import streamlit as st

st.title("Loont het om meer te werken? 💰")

# -------------------------------
# Functie voor Nederlandse notatie
# -------------------------------
def format_nl(x):
    return f"€{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# -------------------------------
# Rekenhulp brutojaarsalaris
# -------------------------------
st.subheader("Rekenhulp brutojaarsalaris")
maandsalaris = st.number_input("Brutomaandsalaris (€):", min_value=0.0, step=100.0, format="%.2f")
heeft_13e_maand = st.checkbox("13e maand ontvangen?")
vakantiegeld_percentage = st.number_input("Vakantiegeld (%):", min_value=0.0, max_value=20.0, value=8.0, step=0.1)

# Berekening brutojaarsalaris
brutojaarsalaris = maandsalaris * 12
if heeft_13e_maand:
    brutojaarsalaris += maandsalaris
brutojaarsalaris += brutojaarsalaris * (vakantiegeld_percentage / 100)
st.write(f"Brutojaarsalaris: {format_nl(brutojaarsalaris)}")

# -------------------------------
# Extra werkuren per week
# -------------------------------
st.subheader("Rekenhulp extra werkuren")
basis_werkuren = st.number_input("Aantal reguliere werkuren per week:", min_value=1.0, max_value=60.0, value=36.0, step=0.5)
extra_werkuren = st.number_input("Aantal extra werkuren per week:", min_value=0.0, max_value=40.0, value=0.0, step=0.5)

if basis_werkuren > 0:
    bruto_maand_per_uur = maandsalaris / basis_werkuren
    extra_bruto_maand = extra_werkuren * bruto_maand_per_uur
    extra_bruto_jaar = extra_bruto_maand * 12
else:
    extra_bruto_jaar = 0

# Extra bruto jaar inclusief 13e maand en vakantiegeld
extra_bruto_jaar_correct = extra_bruto_jaar
if heeft_13e_maand:
    extra_bruto_jaar_correct += extra_bruto_jaar  # 13e maand over extra inkomen
extra_bruto_jaar_correct += extra_bruto_jaar_correct * (vakantiegeld_percentage / 100)

st.write(f"Geschat extra bruto jaarinkomen bij {extra_werkuren:.1f} uur extra per week: {format_nl(extra_bruto_jaar_correct)}")

# -------------------------------
# Persoonlijke gegevens en toeslagpartner
# -------------------------------
st.subheader("Persoonlijke gegevens")
huidig_inkomen = st.number_input("Huidig bruto jaarinkomen (€):", min_value=0.0, step=100.0, value=brutojaarsalaris)
st.write(f"Extra bruto inkomen dat wordt gebruikt voor berekening: {format_nl(extra_bruto_jaar_correct)}")

leeftijd = st.number_input("Leeftijd:", min_value=0, max_value=120, step=1)
aow_leeftijd = 67
heeft_aow_leeftijd = leeftijd >= aow_leeftijd

st.subheader("Toeslagen")
st.info("""
**Toeslagpartner:** iemand met wie u samenwoont en een gezamenlijke huishouding voert, bijvoorbeeld uw echtgenoot, geregistreerd partner of iemand met wie u een notarieel samenlevingscontract heeft. 
Het inkomen en vermogen van uw toeslagpartner tellen mee voor toeslagen zoals huurtoeslag en zorgtoeslag.
""")
toeslagpartner = st.checkbox("Heeft een toeslagpartner?")
if toeslagpartner:
    partner_inkomen = st.number_input("Bruto jaarinkomen toeslagpartner (€):", min_value=0.0, step=100.0)
    partner_vermogen = st.number_input("Vermogen toeslagpartner (€):", min_value=0.0, step=100.0)
else:
    partner_inkomen = 0.0
    partner_vermogen = 0.0

huur = st.number_input("Huur per maand (€):", min_value=0.0, step=50.0)
aantal_kinderen = st.number_input("Aantal kinderen jonger dan 12:", min_value=0, step=1)
kinderopvang_maand = st.number_input("Kinderopvang per maand (€):", min_value=0.0, step=50.0)
vermogen = st.number_input("Totaal vermogen huishouden (€):", min_value=0.0, step=1000.0)

# -------------------------------
# Belasting box 1
# -------------------------------
def belasting_box1(inkomen, aow_leeftijd=False):
    if aow_leeftijd:
        schijf1_max = 38441
        tarief1 = 0.1792
        tarief2 = 0.3748
        tarief3 = 0.4950
    else:
        schijf1_max = 38441
        tarief1 = 0.3582
        tarief2 = 0.3748
        tarief3 = 0.4950

    if inkomen <= schijf1_max:
        return inkomen * tarief1
    elif inkomen <= 76817:
        return schijf1_max * tarief1 + (inkomen - schijf1_max) * tarief2
    else:
        return schijf1_max * tarief1 + (76817 - schijf1_max) * tarief2 + (inkomen - 76817) * tarief3

# -------------------------------
# Heffingskortingen
# -------------------------------
def algemene_heffingskorting(inkomen, aow_leeftijd=False):
    if aow_leeftijd:
        max_ahk = 1536
        afbouw_start = 28406
        afbouw_percentage = 0.0317
    else:
        max_ahk = 3068
        afbouw_start = 28406
        afbouw_percentage = 0.06337
    if inkomen <= afbouw_start:
        return max_ahk
    else:
        korting = max_ahk - afbouw_percentage * (inkomen - afbouw_start)
        return max(0, korting)

def arbeidskorting(arbeidsinkomen, aow_leeftijd=False):
    if aow_leeftijd:
        if arbeidsinkomen <= 10000:
            return 0.14 * arbeidsinkomen
        elif arbeidsinkomen <= 50000:
            return 1400 + 0.05 * (arbeidsinkomen - 10000)
        else:
            return max(0, 2802 - 0.051 * (arbeidsinkomen - 50000))
    else:
        if arbeidsinkomen <= 12169:
            return 0.08053 * arbeidsinkomen
        elif arbeidsinkomen <= 26288:
            return 980 + 0.3003 * (arbeidsinkomen - 12169)
        elif arbeidsinkomen <= 43071:
            return 5220 + 0.02258 * (arbeidsinkomen - 26288)
        elif arbeidsinkomen <= 129078:
            return max(0, 5599 - 0.0651 * (arbeidsinkomen - 43071))
        else:
            return 0

# -------------------------------
# Toeslagen
# -------------------------------
def huurtoeslag(inkomen, huur, leeftijd, toeslagpartner_inkomen=0, toeslagpartner_vermogen=0, vermogen=0):
    totaal_inkomen = inkomen + toeslagpartner_inkomen
    totaal_vermogen = vermogen + toeslagpartner_vermogen
    max_vermogen = 74790 if toeslagpartner_inkomen > 0 else 37395
    if totaal_vermogen > max_vermogen:
        return 0
    huurgrens = 477.20 if leeftijd < 23 else 900.07
    huur_effectief = min(huur, huurgrens)
    if totaal_inkomen >= 45000:
        return 0
    elif totaal_inkomen <= 25000:
        return min(huur_effectief * 0.3 * 12, 5000)
    else:
        return min(huur_effectief * 0.3 * 12, 5000) * (1 - (totaal_inkomen - 25000)/20000)

def zorgtoeslag(inkomen, vermogen, toeslagpartner_inkomen=0, toeslagpartner_vermogen=0):
    totaal_inkomen = inkomen + toeslagpartner_inkomen
    totaal_vermogen = vermogen + toeslagpartner_vermogen
    max_vermogen = 179429 if toeslagpartner_inkomen > 0 else 141896
    if totaal_vermogen > max_vermogen:
        return 0
    if totaal_inkomen >= 45000:
        return 0
    elif totaal_inkomen <= 30000:
        return 1000
    else:
        return 1000 * (1 - (totaal_inkomen - 30000)/15000)

def kinderopvangtoeslag(inkomen, maand_kosten, kinderen):
    max_vergoeding_per_kind = 0.33 * maand_kosten * 12
    if inkomen >= 120000:
        return 0
    else:
        afbouw = inkomen/120000
        return max(0, max_vergoeding_per_kind * (1 - afbouw) * kinderen)

# -------------------------------
# Netto berekening
# -------------------------------
def netto_inkomen(inkomen):
    return (inkomen
            - belasting_box1(inkomen, heeft_aow_leeftijd)
            + algemene_heffingskorting(inkomen, heeft_aow_leeftijd)
            + arbeidskorting(inkomen, heeft_aow_leeftijd)
            + huurtoeslag(inkomen, huur, leeftijd, partner_inkomen, partner_vermogen, vermogen)
            + zorgtoeslag(inkomen, vermogen, partner_inkomen, partner_vermogen)
            + kinderopvangtoeslag(inkomen, kinderopvang_maand, aantal_kinderen))

huidig_netto = netto_inkomen(huidig_inkomen)
nieuw_netto = netto_inkomen(huidig_inkomen + extra_bruto_jaar_correct)

st.subheader("Resultaten")
st.write(f"Huidig netto inkomen (incl. toeslagen): {format_nl(huidig_netto)}")
st.write(f"Netto inkomen bij extra werk (incl. toeslagen): {format_nl(nieuw_netto)}")
st.write(f"Extra netto inkomen: {format_nl(nieuw_netto - huidig_netto)}")
