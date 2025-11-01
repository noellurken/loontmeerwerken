import streamlit as st
import pandas as pd

st.title("Loont het om meer te werken? 💰")

# -------------------------------
# Helper: Nederlandse notatie
# -------------------------------
def format_nl(x):
    return f"€{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# -------------------------------
# Belasting, heffingskortingen en toeslagen (zoals eerder)
# -------------------------------
# [Hier komen alle functies: belasting_box1, algemene_heffingskorting, arbeidskorting,
# huurtoeslag, zorgtoeslag, kinderopvangtoeslag, netto_inkomen]
# (Exact dezelfde als in de vorige versie)
# -------------------------------

# -------------------------------
# Gebruiker inputs
# -------------------------------
st.subheader("Gebruiker en extra werk")
maandsalaris = st.number_input("Maandsalaris (€)", 0.0, 20000.0, 2500.0, 100.0)
heeft_13e_maand = st.checkbox("13e maand?", True)
vakantiegeld = st.number_input("Vakantiegeld (%)", 0.0, 20.0, 8.0, 0.1)
basis_uren = st.number_input("Werkuren per week", 1.0, 60.0, 36.0, 0.5)
extra_uren = st.number_input("Extra werkuren per week", 0.0, 40.0, 0.0, 0.5)

# Bereken huidig bruto jaar
huidig_brutojaar = maandsalaris*12
if heeft_13e_maand:
    huidig_brutojaar += maandsalaris
huidig_brutojaar += huidig_brutojaar*(vakantiegeld/100)
bruto_per_uur = maandsalaris/basis_uren
extra_brutojaar = extra_uren*bruto_per_uur*12
if heeft_13e_maand:
    extra_brutojaar *= 13/12
extra_brutojaar *= (1+vakantiegeld/100)

# -------------------------------
# Overige gegevens
# -------------------------------
leeftijd = st.number_input("Leeftijd gebruiker", 16, 120, 35)
aow_leeftijd = 67
heeft_aow = leeftijd >= aow_leeftijd
huur = st.number_input("Huur per maand (€)", 0.0, 5000.0, 800.0)
vermogen = st.number_input("Totaal vermogen huishouden (€)", 0.0, 1000000.0, 20000.0)
kinderopvang_maand = st.number_input("Kinderopvang per maand (€)", 0.0, 2000.0, 0.0)
aantal_kinderen = st.number_input("Aantal kinderen <12 jaar", 0, 10, 0)

# -------------------------------
# Toeslagpartner
# -------------------------------
st.subheader("Toeslagpartner")
toeslagpartner = st.checkbox("Heeft toeslagpartner?")
partner_inkomen = 0.0
partner_vermogen = 0.0
if toeslagpartner:
    partner_inkomen = st.number_input("Bruto jaar toeslagpartner (€)", 0.0, 500000.0, 0.0, 1000.0)
    partner_vermogen = st.number_input("Vermogen toeslagpartner (€)", 0.0, 500000.0, 0.0, 1000.0)

# -------------------------------
# Netto berekening
# -------------------------------
huidig_netto = netto_inkomen(huidig_brutojaar, huur, leeftijd, partner_inkomen, partner_vermogen, vermogen, kinderopvang_maand, aantal_kinderen, heeft_aow)
nieuw_netto = netto_inkomen(huidig_brutojaar + extra_brutojaar, huur, leeftijd, partner_inkomen, partner_vermogen, vermogen, kinderopvang_maand, aantal_kinderen, heeft_aow)
extra_netto = nieuw_netto - huidig_netto
marginale_druk = 1 - (extra_netto / extra_brutojaar) if extra_brutojaar > 0 else 0

# Componenten
delta_belasting = -(belasting_box1(huidig_brutojaar + extra_brutojaar, heeft_aow) - belasting_box1(huidig_brutojaar, heeft_aow))
delta_ahk = algemene_heffingskorting(huidig_brutojaar + extra_brutojaar, heeft_aow) - algemene_heffingskorting(huidig_brutojaar, heeft_aow)
delta_arbeidskorting = arbeidskorting(huidig_brutojaar + extra_brutojaar, heeft_aow) - arbeidskorting(huidig_brutojaar, heeft_aow)
delta_huur = huurtoeslag(huidig_brutojaar + extra_brutojaar, huur, leeftijd, partner_inkomen, partner_vermogen, vermogen) - huurtoeslag(huidig_brutojaar, huur, leeftijd, partner_inkomen, partner_vermogen, vermogen)
delta_zorg = zorgtoeslag(huidig_brutojaar + extra_brutojaar, vermogen, partner_inkomen, partner_vermogen) - zorgtoeslag(huidig_brutojaar, vermogen, partner_inkomen, partner_vermogen)
delta_kinderopvang = kinderopvangtoeslag(huidig_brutojaar + extra_brutojaar, kinderopvang_maand, aantal_kinderen) - kinderopvangtoeslag(huidig_brutojaar, kinderopvang_maand, aantal_kinderen)

components = {
    "Extra belasting (verlies)": delta_belasting,
    "Algemene heffingskorting effect": delta_ahk,
    "Arbeidskorting effect": delta_arbeidskorting,
    "Huurtoeslag effect": delta_huur,
    "Zorgtoeslag effect": delta_zorg,
    "Kinderopvangtoeslag effect": delta_kinderopvang
}

# -------------------------------
# Resultaten
# -------------------------------
st.subheader("Resultaten")
st.write(f"Huidig netto inkomen (incl. toeslagen): {format_nl(huidig_netto)}")
st.write(f"Netto inkomen bij extra werk (incl. toeslagen): {format_nl(nieuw_netto)}")
st.write(f"Extra netto inkomen: {format_nl(extra_netto)}")
st.write(f"Extra bruto inkomen: {format_nl(extra_brutojaar)}")
st.write(f"Marginale druk: {marginale_druk*100:.1f}%")

st.markdown("**Gedetailleerde componenten van extra netto-inkomen:**")
for label, waarde in components.items():
    kleur = "green" if waarde >= 0 else "red"
    st.markdown(f"<span style='color:{kleur}'>{label}: {format_nl(waarde)}</span>", unsafe_allow_html=True)

# -------------------------------
# Grafiek: Extra netto-inkomen vs extra werkuren
# -------------------------------
st.subheader("Extra netto-inkomen vs extra werkuren")
uren_range = list(range(0, int(max(40, extra_uren + 1)), 1))
netto_extra_list = []
for u in uren_range:
    if u == 0:
        netto_extra_list.append(0)
        continue
    extra_bruto = u * bruto_per_uur * 12
    if heeft_13e_maand:
        extra_bruto *= 13/12
    extra_bruto *= (1 + vakantiegeld/100)
    netto_extra = netto_inkomen(huidig_brutojaar + extra_bruto, huur, leeftijd, partner_inkomen, partner_vermogen, vermogen, kinderopvang_maand, aantal_kinderen, heeft_aow) - huidig_netto
    netto_extra_list.append(netto_extra)

df = pd.DataFrame({"Extra werkuren": uren_range, "Extra netto inkomen": netto_extra_list})
st.line_chart(df.set_index("Extra werkuren"))
