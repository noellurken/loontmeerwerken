import streamlit as st
import pandas as pd
import altair as alt
import plotly.graph_objects as go

st.title("Loont het om meer te werken? 💰")

# -------------------------------
# Helper: Nederlandse notatie
# -------------------------------
def format_nl(x):
    return f"€{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# -------------------------------
# Belasting en heffingskortingen
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
# Toeslagen (met huurgrenscheck)
# -------------------------------
def huurtoeslag_marge(inkomen, huur, leeftijd, toeslagpartner_inkomen=0, toeslagpartner_vermogen=0, vermogen=0):
    totaal_inkomen = inkomen + toeslagpartner_inkomen
    totaal_vermogen = vermogen + toeslagpartner_vermogen

    max_vermogen = 74790 if toeslagpartner_inkomen > 0 else 37395
    huurgrens = 477.20 if leeftijd < 23 else 900.07

    # ✅ Als huur hoger is dan huurgrens → geen recht → marginaal effect = 0
    if huur > huurgrens:
        return 0

    huur_effectief = min(huur, huurgrens)

    if totaal_vermogen > max_vermogen:
        return 0
    if totaal_inkomen <= 25000:
        return min(huur_effectief * 0.3 * 12, 5000)
    elif totaal_inkomen <= 45000:
        return min(huur_effectief * 0.3 * 12, 5000) * (1 - (totaal_inkomen - 25000)/20000)
    else:
        return 0

def zorgtoeslag_marge(inkomen, vermogen, toeslagpartner_inkomen=0, toeslagpartner_vermogen=0):
    totaal_inkomen = inkomen + toeslagpartner_inkomen
    totaal_vermogen = vermogen + toeslagpartner_vermogen
    max_vermogen = 179429 if toeslagpartner_inkomen > 0 else 141896
    if totaal_vermogen > max_vermogen:
        return 0
    if totaal_inkomen <= 30000:
        return 1000
    elif totaal_inkomen <= 45000:
        return 1000 * (1 - (totaal_inkomen - 30000)/15000)
    else:
        return 0

def kinderopvangtoeslag_marge(inkomen, maand_kosten, kinderen):
    max_vergoeding_per_kind = 0.33 * maand_kosten * 12
    if inkomen >= 120000:
        return 0
    else:
        afbouw = min(1, inkomen / 120000)
        return max(0, max_vergoeding_per_kind * (1 - afbouw) * kinderen)

# -------------------------------
# Netto inkomen berekening
# -------------------------------
def netto_inkomen(inkomen, huur, leeftijd, toeslagpartner_inkomen=0, toeslagpartner_vermogen=0,
                  vermogen=0, kinderopvang_maand=0, aantal_kinderen=0, aow_leeftijd=False):
    return (
        inkomen
        - belasting_box1(inkomen, aow_leeftijd)
        + algemene_heffingskorting(inkomen, aow_leeftijd)
        + arbeidskorting(inkomen, aow_leeftijd)
        + huurtoeslag_marge(inkomen, huur, leeftijd, toeslagpartner_inkomen, toeslagpartner_vermogen, vermogen)
        + zorgtoeslag_marge(inkomen, vermogen, toeslagpartner_inkomen, toeslagpartner_vermogen)
        + kinderopvangtoeslag_marge(inkomen, kinderopvang_maand, aantal_kinderen)
    )

# -------------------------------
# Inputs
# -------------------------------
st.subheader("Gegevens")
maandsalaris = st.number_input("Wat is je huidige brutomaandsalaris (€)?", 0.0, 20000.0, 0.0, 100.0)
heeft_13e_maand = st.checkbox("Heb je recht op een 13e maand?", False)
vakantiegeld = st.number_input("Op hoeveel vakantiegeld heb je recht (%)?", 0.0, 20.0, 8.0, 0.1)
basis_uren = st.number_input("Hoeveel uur werk je op dit moment per week?", 0.0, 60.0, 0.0, 0.5)
extra_uren = st.number_input("Hoeveel uur per week wil je extra gaan werken?", 0.0, 40.0, 0.0, 0.5)

# ✅ leeftijd start op 0 zoals gevraagd
leeftijd = st.number_input("Wat is je leeftijd?", 0, 120, 0)

aow_leeftijd = 67
heeft_aow = leeftijd >= aow_leeftijd
huur = st.number_input("Wat betaal je per maand aan huur (€)?", 0.0, 5000.0, 0.0)
vermogen = st.number_input("Wat is je totale vermogen (€)?", 0.0, 1000000.0, 0.0)
kinderopvang_maand = st.number_input("Hoeveel ben je per maand kwijt aan kinderopvang (€)?", 0.0, 2000.0, 0.0)
aantal_kinderen = st.number_input("Hoeveel kinderen jonger dan 12 jaar heb je?", 0, 10, 0)

# -------------------------------
# Toeslagpartner
# -------------------------------
st.subheader("Toeslagpartner")
toeslagpartner = st.checkbox("Heb je een toeslagpartner?")

partner_inkomen = 0.0
partner_vermogen = 0.0

if toeslagpartner:
    partner_maandsalaris = st.number_input("Maandsalaris toeslagpartner (€)", 0.0, 20000.0, 0.0, 100.0)
    partner_heeft_13e_maand = st.checkbox("13e maand toeslagpartner?", True)
    partner_vakantiegeld = st.number_input("Vakantiegeld toeslagpartner (%)", 0.0, 20.0, 8.0, 0.1)
    partner_basis_uren = st.number_input("Werkuren per week toeslagpartner", 0.0, 60.0, 0.0, 0.5)
    partner_extra_uren = st.number_input("Extra werkuren per week toeslagpartner", 0.0, 40.0, 0.0, 0.5)
    partner_vermogen = st.number_input("Vermogen toeslagpartner (€)", 0.0, 500000.0, 0.0, 1000.0)

    partner_brutojaar = partner_maandsalaris*12
    if partner_heeft_13e_maand:
        partner_brutojaar += partner_maandsalaris
    partner_brutojaar += partner_brutojaar*(partner_vakantiegeld/100)
    bruto_per_uur_partner = partner_maandsalaris/partner_basis_uren if partner_basis_uren>0 else 0
    extra_bruto_partner = partner_extra_uren*bruto_per_uur_partner*12
    if partner_heeft_13e_maand:
        extra_bruto_partner *= 13/12
    extra_bruto_partner *= (1+partner_vakantiegeld/100)
    partner_inkomen = partner_brutojaar + extra_bruto_partner

# -------------------------------
# Berekeningen
# -------------------------------
huidig_brutojaar = maandsalaris*12
if heeft_13e_maand:
    huidig_brutojaar += maandsalaris
huidig_brutojaar += huidig_brutojaar*(vakantiegeld/100)

bruto_per_uur = maandsalaris/basis_uren if basis_uren > 0 else 0
extra_brutojaar = extra_uren*bruto_per_uur*12
if heeft_13e_maand:
    extra_brutojaar *= 13/12
extra_brutojaar *= (1+vakantiegeld/100)

huidig_netto = netto_inkomen(huidig_brutojaar, huur, leeftijd, partner_inkomen, partner_vermogen, vermogen,
                             kinderopvang_maand, aantal_kinderen, heeft_aow)
nieuw_netto = netto_inkomen(huidig_brutojaar + extra_brutojaar, huur, leeftijd,
                            partner_inkomen, partner_vermogen, vermogen, kinderopvang_maand,
                            aantal_kinderen, heeft_aow)

extra_netto = nieuw_netto - huidig_netto
marginale_druk = 1 - (extra_netto / extra_brutojaar) if extra_brutojaar > 0 else 0

# -------------------------------
# Resultaten tekst
# -------------------------------
st.subheader("Resultaten")
st.write(f"Huidig netto inkomen: {format_nl(huidig_netto)}")
st.write(f"Netto na extra werk: {format_nl(nieuw_netto)}")
st.write(f"Extra netto: {format_nl(extra_netto)}")
st.write(f"Extra bruto: {format_nl(extra_brutojaar)}")
st.write(f"Marginale druk: {marginale_druk*100:.1f}%")

# -------------------------------
# Plot zonder hover cijfers
# -------------------------------
st.subheader("Extra netto-inkomen vs extra werkuren")

max_extra_uren = max(0, 40 - basis_uren)
uren_range = list(range(0, int(max_extra_uren) + 1))
netto_extra_list = []

for u in uren_range:
    if u == 0:
        netto_extra_list.append(0)
        continue
    extra_bruto = u * bruto_per_uur * 12
    if heeft_13e_maand:
        extra_bruto *= 13/12
    extra_bruto *= (1 + vakantiegeld/100)
    netto_extra = netto_inkomen(
        huidig_brutojaar + extra_bruto, huur, leeftijd, partner_inkomen,
        partner_vermogen, vermogen, kinderopvang_maand, aantal_kinderen, heeft_aow
    ) - huidig_netto
    netto_extra_list.append(netto_extra)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=uren_range,
    y=netto_extra_list,
    mode='lines+markers',
    line=dict(color='blue'),
    marker=dict(size=6),
    hoverinfo='skip'
))
fig.update_layout(
    xaxis_title="Extra werkuren per week",
    yaxis_title="Extra netto inkomen",
    template="simple_white"
)
st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# Tabel
# -------------------------------
st.subheader("Tabel (€1.234,56)")
df_chart_nl = pd.DataFrame({"Extra werkuren": uren_range, "Extra netto inkomen": netto_extra_list})
df_chart_nl["Extra netto inkomen"] = df_chart_nl["Extra netto inkomen"].apply(format_nl)
st.dataframe(df_chart_nl.set_index("Extra werkuren"))
