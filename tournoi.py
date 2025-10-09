import streamlit as st
import random
import pandas as pd

# =========================
#   INITIALISATION
# =========================
if "joueurs" not in st.session_state:
    st.session_state.joueurs = {}
if "matchs" not in st.session_state:
    st.session_state.matchs = []
if "scores" not in st.session_state:
    st.session_state.scores = {}
if "phases_finales" not in st.session_state:
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
if "classement_calcule" not in st.session_state:
    st.session_state.classement_calcule = False

st.set_page_config(page_title="🎾 Tournoi de Padel", page_icon="🎾", layout="wide")

# =========================
#   PARAMÈTRES SIDEBAR
# =========================
st.sidebar.header("⚙️ Paramètres du tournoi")

hommes_input = st.sidebar.text_area("Liste des hommes (un par ligne)", height=150)
femmes_input = st.sidebar.text_area("Liste des femmes (un par ligne)", height=150)

hommes = [h.strip() for h in hommes_input.splitlines() if h.strip()]
femmes = [f.strip() for f in femmes_input.splitlines() if f.strip()]

st.sidebar.markdown("---")
st.sidebar.markdown(f"👨 **Hommes :** {len(hommes)}")
st.sidebar.markdown(f"👩 **Femmes :** {len(femmes)}")
st.sidebar.markdown(f"🎯 **Total :** {len(hommes) + len(femmes)}")
st.sidebar.markdown("---")

nb_terrains = st.sidebar.number_input("Nombre de terrains", 1, 10, 4)
max_matchs = st.sidebar.number_input("Max matchs par joueur", 1, 20, 4)

if st.sidebar.button("🔄 Reset Tournoi"):
    for k in ["joueurs", "matchs", "scores", "phases_finales", "classement_calcule"]:
        st.session_state.pop(k, None)
    st.rerun()

# =========================
#   STYLE TABLEAUX COMPACTS
# =========================
st.markdown("""
<style>
.small-table td, .small-table th {
    padding: 4px 8px !important;
    font-size: 0.85rem !important;
    text-align: center !important;
}
div[data-testid="stDataFrame"] table {
    width: 75% !important;
    margin: auto !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
#   SYNCHRONISATION JOUEURS
# =========================
def sync_joueurs():
    current = set(st.session_state.joueurs.keys())
    new = set(hommes + femmes)
    for j in current - new:
        del st.session_state.joueurs[j]
    for h in hommes:
        if h not in st.session_state.joueurs:
            st.session_state.joueurs[h] = {"Points": 0.0, "Jeux": 0, "Matchs": 0, "Sexe": "H"}
    for f in femmes:
        if f not in st.session_state.joueurs:
            st.session_state.joueurs[f] = {"Points": 0.0, "Jeux": 0, "Matchs": 0, "Sexe": "F"}

sync_joueurs()

# =========================
#   CLASSEMENT
# =========================
def maj_classement():
    for j in st.session_state.joueurs:
        st.session_state.joueurs[j].update({"Points": 0.0, "Jeux": 0, "Matchs": 0})

    for r, matchs in enumerate(st.session_state.matchs):
        for m, (e1, e2) in enumerate(matchs):
            score = st.session_state.scores.get(f"score_{r}_{m}", "")
            if not score or "-" not in score:
                continue
            try:
                s1, s2 = map(int, score.split("-"))
            except:
                continue
            gagnants, perdants, js_g, js_p = (e1, e2, s1, s2) if s1 > s2 else (e2, e1, s2, s1)
            for j in gagnants:
                st.session_state.joueurs[j]["Points"] += 3 + js_g * 0.1
                st.session_state.joueurs[j]["Jeux"] += js_g
                st.session_state.joueurs[j]["Matchs"] += 1
            for j in perdants:
                st.session_state.joueurs[j]["Points"] += 0.5
                st.session_state.joueurs[j]["Jeux"] += js_p
                st.session_state.joueurs[j]["Matchs"] += 1

def _df_classement():
    df = pd.DataFrame.from_dict(st.session_state.joueurs, orient="index").reset_index()
    df.rename(columns={"index": "Joueur"}, inplace=True)
    df["Points"] = df["Points"].round(1)  # ✅ arrondi 1 décimale
    df["Jeux"] = df["Jeux"].astype(int)
    df["Matchs"] = df["Matchs"].astype(int)
    df.sort_values(by=["Points", "Jeux"], ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

def afficher_classement():
    df = _df_classement()
    df.insert(0, "Rang", df.index + 1)
    df["Points"] = df["Points"].map(lambda x: f"{x:.1f}")  # ✅ format strict à 1 décimale
    st.dataframe(df.style.set_table_attributes('class="small-table"'), use_container_width=True)

def afficher_top8():
    df = _df_classement()
    topH = df[df["Sexe"] == "H"].head(8)[["Joueur", "Points", "Jeux", "Matchs"]]
    topF = df[df["Sexe"] == "F"].head(8)[["Joueur", "Points", "Jeux", "Matchs"]]
    topH["Points"] = topH["Points"].map(lambda x: f"{x:.1f}")
    topF["Points"] = topF["Points"].map(lambda x: f"{x:.1f}")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🥇 Top 8 Hommes")
        st.dataframe(topH.style.set_table_attributes('class="small-table"'), use_container_width=True)
    with c2:
        st.subheader("🏅 Top 8 Femmes")
        st.dataframe(topF.style.set_table_attributes('class="small-table"'), use_container_width=True)

# =========================
#   INTERFACE PRINCIPALE
# =========================
st.title("🎾 Tournoi de Padel - Rétro Padel")

if st.button("📊 Calculer le classement"):
    maj_classement()
    st.session_state.classement_calcule = True
    st.rerun()

if st.session_state.joueurs:
    st.header("📈 Classement général")
    maj_classement()
    afficher_classement()
    st.markdown("---")
    afficher_top8()
