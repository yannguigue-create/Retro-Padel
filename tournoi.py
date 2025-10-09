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

st.set_page_config(page_title="🎾 Tournoi de Padel - Rétro Padel", page_icon="🎾", layout="wide")

# =========================
#   SIDEBAR PARAMÈTRES
# =========================
st.sidebar.header("⚙️ Paramètres du tournoi")

hommes_input = st.sidebar.text_area("Liste des hommes (un par ligne)", height=150)
femmes_input = st.sidebar.text_area("Liste des femmes (un par ligne)", height=150)

hommes = [h.strip() for h in hommes_input.splitlines() if h.strip()]
femmes = [f.strip() for f in femmes_input.splitlines() if f.strip()]

st.sidebar.markdown("---")
st.sidebar.markdown(f"<h3 style='color:#1f77b4'>👨 Hommes : {len(hommes)}</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"<h3 style='color:#ff69b4'>👩 Femmes : {len(femmes)}</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"<h3 style='color:#2ca02c'>🎯 Total : {len(hommes)+len(femmes)}</h3>", unsafe_allow_html=True)
st.sidebar.markdown("---")

nb_terrains = st.sidebar.number_input("Nombre de terrains disponibles", 1, 10, 2)
max_matchs = st.sidebar.number_input("Nombre maximum de matchs par joueur", 1, 20, 4)

st.sidebar.markdown("---")

if st.sidebar.button("🔄 Reset Tournoi Complet", type="primary"):
    st.session_state.joueurs = {}
    st.session_state.matchs = []
    st.session_state.scores = {}
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
    st.session_state.classement_calcule = False
    st.rerun()

# =========================
#   SYNC JOUEURS
# =========================
for j in list(st.session_state.joueurs.keys()):
    if j not in (hommes + femmes):
        del st.session_state.joueurs[j]

for h in hommes:
    if h not in st.session_state.joueurs:
        st.session_state.joueurs[h] = {"Points": 0.0, "Jeux": 0, "Matchs": 0, "Sexe": "H"}
for f in femmes:
    if f not in st.session_state.joueurs:
        st.session_state.joueurs[f] = {"Points": 0.0, "Jeux": 0, "Matchs": 0, "Sexe": "F"}

# =========================
#   STYLE COMPACT TABLEAUX
# =========================
st.markdown("""
<style>
.small-table thead th, .small-table tbody td {
    padding: 6px 10px !important;
    font-size: 0.9rem !important;
    text-align: center !important;
}
.dataframe {
    margin-left: auto !important;
    margin-right: auto !important;
    width: 80% !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
#   OUTILS
# =========================
def maj_classement():
    """Met à jour les scores et classements"""
    for j in st.session_state.joueurs:
        st.session_state.joueurs[j]["Points"] = 0.0
        st.session_state.joueurs[j]["Jeux"] = 0
        st.session_state.joueurs[j]["Matchs"] = 0

    for round_idx, matchs in enumerate(st.session_state.matchs):
        for match_idx, (equipe1, equipe2) in enumerate(matchs):
            key = f"score_{round_idx+1}_{match_idx}"
            score = st.session_state.scores.get(key, "")
            if not score or "-" not in score:
                continue
            try:
                s1, s2 = map(int, score.split("-"))
            except:
                continue

            gagnants, perdants = (equipe1, equipe2) if s1 > s2 else (equipe2, equipe1)
            js_g, js_p = max(s1, s2), min(s1, s2)

            for j in gagnants:
                st.session_state.joueurs[j]["Points"] += 3 + js_g * 0.1
                st.session_state.joueurs[j]["Jeux"] += js_g
                st.session_state.joueurs[j]["Matchs"] += 1
            for j in perdants:
                st.session_state.joueurs[j]["Points"] += 0.5
                st.session_state.joueurs[j]["Jeux"] += js_p
                st.session_state.joueurs[j]["Matchs"] += 1

def _df_classement():
    """Classement trié"""
    df = pd.DataFrame.from_dict(st.session_state.joueurs, orient="index").reset_index()
    df.rename(columns={"index": "Joueur"}, inplace=True)
    df["Points"] = df["Points"].round(1)  # ✅ 1 seule décimale
    df["Jeux"] = df["Jeux"].astype(int)
    df["Matchs"] = df["Matchs"].astype(int)
    df.sort_values(by=["Points", "Jeux"], ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

def afficher_classement():
    """Affiche le tableau général"""
    df = _df_classement()
    df.insert(0, "Rang", df.index + 1)
    df["Points"] = df["Points"].map(lambda x: f"{x:.1f}")  # ✅ Format 1 décimale à l’affichage
    st.table(df.style.set_table_attributes('class="small-table"'))

def afficher_top8():
    """Affiche les Top 8 par sexe"""
    df = _df_classement()
    topH = df[df["Sexe"] == "H"].head(8)[["Joueur", "Points", "Jeux", "Matchs"]].copy()
    topF = df[df["Sexe"] == "F"].head(8)[["Joueur", "Points", "Jeux", "Matchs"]].copy()
    topH["Points"] = topH["Points"].map(lambda x: f"{x:.1f}")
    topF["Points"] = topF["Points"].map(lambda x: f"{x:.1f}")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🥇 Top 8 Hommes")
        st.table(topH.style.set_table_attributes('class="small-table"'))
    with c2:
        st.subheader("🏅 Top 8 Femmes")
        st.table(topF.style.set_table_attributes('class="small-table"'))

# =========================
#   UI PRINCIPALE
# =========================
st.title("🎾 Tournoi de Padel - Rétro Padel")

# --- MATCHS ET CLASSEMENT ---
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
