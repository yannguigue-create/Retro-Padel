import streamlit as st
import pandas as pd
import random

# ============================
# PAGE CONFIGURATION
# ============================
st.set_page_config(
    page_title="Tournoi de Padel - Rétro Padel",
    page_icon="🎾",
    layout="wide"
)

# ============================
# LOGO + TITRE
# ============================
st.markdown(
    """
    <div style="text-align: center;">
        <img src="https://raw.githubusercontent.com/yannguigue-create/Retro-Padel/main/logo_retro_padel.png" width="250">
        <h1 style="color:#1E3A8A; font-family: Arial, sans-serif;">
            🎾 Tournoi de Padel - Retro Padel
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)

# ============================
# INITIALISATION SESSION
# ============================
if "rounds" not in st.session_state:
    st.session_state.rounds = []
if "classement" not in st.session_state:
    st.session_state.classement = pd.DataFrame(columns=["Joueur", "Points", "Jeux", "Matchs"])
if "phases_finales" not in st.session_state:
    st.session_state.phases_finales = {}

# ============================
# SIDEBAR : PARAMÈTRES
# ============================
with st.sidebar:
    st.header("⚙️ Paramètres du tournoi")

    hommes_input = st.text_area("Liste des hommes (un par ligne)", "Yann\nRomuald\nMatthieu\nKarl")
    femmes_input = st.text_area("Liste des femmes (un par ligne)", "Sabine\nElyse\nGarance\nMonica")

    hommes = [h.strip() for h in hommes_input.split("\n") if h.strip()]
    femmes = [f.strip() for f in femmes_input.split("\n") if f.strip()]

    st.session_state.hommes = hommes
    st.session_state.femmes = femmes

    st.markdown(f"👨 Hommes : **{len(hommes)}**")
    st.markdown(f"👩 Femmes : **{len(femmes)}**")
    st.markdown(f"📊 Total joueurs : **{len(hommes) + len(femmes)}**")

    terrains = st.number_input("Nombre de terrains disponibles", 1, 10, 2)
    max_matchs = st.number_input("Nombre maximum de matchs par joueur", 1, 20, 4)

    if st.button("♻️ Reset Tournoi"):
        st.session_state.rounds = []
        st.session_state.classement = pd.DataFrame(columns=["Joueur", "Points", "Jeux", "Matchs"])
        st.session_state.phases_finales = {}
        st.success("Tournoi réinitialisé ✅")

# ============================
# FONCTION : GÉNÉRER MATCHS
# ============================
def generer_round(hommes, femmes, terrains, max_matchs):
    joueurs = hommes + femmes
    random.shuffle(joueurs)

    # Ne pas dépasser le maximum autorisé
    matchs_joues = st.session_state.classement.groupby("Joueur")["Matchs"].max() if not st.session_state.classement.empty else {}
    joueurs_dispo = [j for j in joueurs if (joueurs.count(j) == 1 and (j not in matchs_joues or matchs_joues[j] < max_matchs))]

    matchs = []
    for i in range(0, min(len(joueurs_dispo), terrains*4), 4):
        if i+3 < len(joueurs_dispo):
            equipeA = [joueurs_dispo[i], joueurs_dispo[i+1]]
            equipeB = [joueurs_dispo[i+2], joueurs_dispo[i+3]]
            matchs.append((equipeA, equipeB))
    return matchs

# ============================
# GESTION DES MATCHS
# ============================
st.subheader("🎲 Gestion des matchs")

if st.button("➕ Générer un nouveau round"):
    nouveau_round = generer_round(hommes, femmes, terrains, max_matchs)
    if nouveau_round:
        st.session_state.rounds.append(nouveau_round)
        st.success(f"✅ Round {len(st.session_state.rounds)} généré !")
    else:
        st.warning("⚠️ Impossible de générer de nouveaux matchs (maximum atteint).")

for i, round_matchs in enumerate(st.session_state.rounds, 1):
    st.markdown(f"### 🏆 Round {i}")
    for j, (equipeA, equipeB) in enumerate(round_matchs, 1):
        score = st.text_input(f"{' + '.join(equipeA)} vs {' + '.join(equipeB)} (Score Round {i} Terrain {j})")
        if score:
            try:
                sA, sB = map(int, score.split("-"))
                for joueur in equipeA:
                    st.session_state.classement.loc[st.session_state.classement["Joueur"] == joueur, "Points"] = st.session_state.classement.get("Points", 0) + (sA > sB) * 3
                    st.session_state.classement.loc[st.session_state.classement["Joueur"] == joueur, "Jeux"] = st.session_state.classement.get("Jeux", 0) + sA
                for joueur in equipeB:
                    st.session_state.classement.loc[st.session_state.classement["Joueur"] == joueur, "Points"] = st.session_state.classement.get("Points", 0) + (sB > sA) * 3
                    st.session_state.classement.loc[st.session_state.classement["Joueur"] == joueur, "Jeux"] = st.session_state.classement.get("Jeux", 0) + sB
            except:
                st.error("⚠️ Format incorrect (ex: 6-4)")

# ============================
# CLASSEMENT GÉNÉRAL
# ============================
if st.button("📊 Calculer le classement"):
    joueurs = hommes + femmes
    classement = []
    for j in joueurs:
        if j not in st.session_state.classement["Joueur"].values:
            classement.append([j, 0, 0, 0])
    df = pd.concat([st.session_state.classement, pd.DataFrame(classement, columns=["Joueur","Points","Jeux","Matchs"])])
    df = df.groupby("Joueur").sum().reset_index()
    df = df.sort_values(by=["Points","Jeux"], ascending=[False,False])
    df["Matchs"] = df["Matchs"].astype(int)
    st.session_state.classement = df
    st.subheader("🏅 Classement Général")
    st.dataframe(df, use_container_width=True)

# ============================
# PHASES FINALES
# ============================
st.subheader("🏆 Phases Finales")

def generer_matchs_elimination(df_h, df_f, phase):
    matchs = []
    if phase == "quarts":
        for i in range(min(4, len(df_h)//2)):
            j1, j2 = df_h.iloc[i]["Joueur"], df_h.iloc[-(i+1)]["Joueur"]
            matchs.append((j1,j2))
        for i in range(min(4, len(df_f)//2)):
            j1, j2 = df_f.iloc[i]["Joueur"], df_f.iloc[-(i+1)]["Joueur"]
            matchs.append((j1,j2))
    return matchs

if st.button("⚡ Générer les phases finales"):
    if not st.session_state.classement.empty:
        hommes = st.session_state.classement[st.session_state.classement["Joueur"].isin(st.session_state.hommes)].head(8)
        femmes = st.session_state.classement[st.session_state.classement["Joueur"].isin(st.session_state.femmes)].head(8)
        st.session_state.phases_finales["quarts"] = generer_matchs_elimination(hommes,femmes,"quarts")
        st.success("Phases finales générées ✅")

if "quarts" in st.session_state.phases_finales:
    st.markdown("### Quarts de finale")
    for i, (j1,j2) in enumerate(st.session_state.phases_finales["quarts"],1):
        st.text_input(f"{j1} vs {j2} (Score quart {i})")
