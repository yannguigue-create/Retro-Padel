import streamlit as st
import pandas as pd
import random

# =========================
# CONFIGURATION PAGE
# =========================
st.set_page_config(
    page_title="Tournoi de Padel - Rétro Padel",
    page_icon="🎾",
    layout="wide"
)

# =========================
# LOGO + TITRE
# =========================
st.markdown(
    f"""
    <div style="text-align: center;">
        <img src="https://raw.githubusercontent.com/yannguigue-create/Retro-Padel/main/logo_retro_padel.png" width="300">
        <h1 style="color:#1E3A8A; font-family: Arial, sans-serif;">🎾 Tournoi de Padel - Retro Padel</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# =========================
# PARAMÈTRES
# =========================
with st.sidebar:
    st.header("⚙️ Paramètres du tournoi")
    hommes_input = st.text_area("Liste des hommes (un par ligne)", "Yann\nRomuald\nMatthieu\nKarl")
    femmes_input = st.text_area("Liste des femmes (un par ligne)", "Sabine\nElyse\nGarance\nMonica")

    hommes = [h.strip() for h in hommes_input.split("\n") if h.strip()]
    femmes = [f.strip() for f in femmes_input.split("\n") if f.strip()]

    st.markdown(f"👨 Hommes : **{len(hommes)}**")
    st.markdown(f"👩 Femmes : **{len(femmes)}**")
    st.markdown(f"📊 Total joueurs : **{len(hommes) + len(femmes)}**")

    nb_terrains = st.number_input("Nombre de terrains disponibles", 1, 10, 4)
    min_matchs = st.number_input("Nombre minimum de matchs par joueur", 1, 10, 4)

    if st.button("♻️ Reset Tournoi"):
        st.session_state.matches = []
        st.session_state.round = 0
        st.session_state.resultats = []
        st.session_state.finales = {}
        st.success("✅ Le tournoi a été réinitialisé !")

# Initialisation des variables globales
if "matches" not in st.session_state:
    st.session_state.matches = []
if "round" not in st.session_state:
    st.session_state.round = 0
if "resultats" not in st.session_state:
    st.session_state.resultats = []
if "finales" not in st.session_state:
    st.session_state.finales = {}

# =========================
# GÉNÉRATION DES MATCHS
# =========================
def generer_round():
    st.session_state.round += 1
    round_matches = []
    joueurs_h = hommes.copy()
    joueurs_f = femmes.copy()
    random.shuffle(joueurs_h)
    random.shuffle(joueurs_f)

    nb_matchs = min(len(joueurs_h), len(joueurs_f)) // 2 * 2
    terrains = list(range(1, nb_terrains+1))
    rotation = 1

    for i in range(0, nb_matchs, 2):
        if len(terrains) == 0:
            terrains = list(range(1, nb_terrains+1))
            rotation += 1
        terrain = terrains.pop(0)

        h1, h2 = joueurs_h[i], joueurs_h[i+1]
        f1, f2 = joueurs_f[i], joueurs_f[i+1]
        equipe_a = f"{h1} + {f1}"
        equipe_b = f"{h2} + {f2}"

        round_matches.append({
            "Round": st.session_state.round,
            "Rotation": rotation,
            "Terrain": terrain,
            "Equipe A": equipe_a,
            "Equipe B": equipe_b,
            "Score": "",
            "Vainqueur": ""
        })

    st.session_state.matches.extend(round_matches)

# =========================
# CLASSEMENT
# =========================
def calculer_classement():
    joueurs = {j: {"Points": 0, "Jeux": 0} for j in hommes + femmes}
    
    for match in st.session_state.matches:
        if match["Score"]:
            try:
                sc_a, sc_b = map(int, match["Score"].split("-"))
            except:
                continue
            if sc_a > sc_b:
                match["Vainqueur"] = "Equipe A"
                pts_a, pts_b = 3, 0.5
            elif sc_b > sc_a:
                match["Vainqueur"] = "Equipe B"
                pts_a, pts_b = 0.5, 3
            else:
                pts_a = pts_b = 1.5

            eqA = match["Equipe A"].split(" + ")
            eqB = match["Equipe B"].split(" + ")
            for j in eqA:
                joueurs[j]["Points"] += pts_a
                joueurs[j]["Jeux"] += sc_a
            for j in eqB:
                joueurs[j]["Points"] += pts_b
                joueurs[j]["Jeux"] += sc_b

    df = pd.DataFrame([
        {"Joueur": j, "Points": d["Points"], "Jeux": d["Jeux"]}
        for j, d in joueurs.items()
    ])

    df = df.sort_values(by=["Points", "Jeux"], ascending=[False, False]).reset_index(drop=True)
    df.index += 1  # Ajoute le rang
    return df

# =========================
# PHASES FINALES
# =========================
def generer_finales(classement):
    top8_h = classement[classement["Joueur"].isin(hommes)].head(8)["Joueur"].tolist()
    top8_f = classement[classement["Joueur"].isin(femmes)].head(8)["Joueur"].tolist()

    # Paires hommes/femmes
    random.shuffle(top8_h)
    random.shuffle(top8_f)
    equipes = [f"{h} + {f}" for h, f in zip(top8_h, top8_f)]

    finales = {"1/4": [], "1/2": [], "Finale": []}

    # 1/4 de finale
    for i in range(0, 8, 2):
        finales["1/4"].append({"Equipe A": equipes[i], "Equipe B": equipes[i+1], "Score": "", "Vainqueur": ""})

    st.session_state.finales = finales

def jouer_phase(phase):
    gagnants = []
    for match in st.session_state.finales[phase]:
        if match["Score"]:
            try:
                sc_a, sc_b = map(int, match["Score"].split("-"))
            except:
                continue
            if sc_a > sc_b:
                match["Vainqueur"] = match["Equipe A"]
                gagnants.append(match["Equipe A"])
            else:
                match["Vainqueur"] = match["Equipe B"]
                gagnants.append(match["Equipe B"])
    return gagnants

# =========================
# INTERFACE
# =========================
st.subheader("🎲 Gestion des matchs")
if st.button("➕ Générer un nouveau round"):
    generer_round()

# Affichage des matchs
for match in st.session_state.matches:
    col1, col2, col3 = st.columns([2,2,1])
    with col1:
        st.write(f"**{match['Equipe A']}**")
    with col2:
        st.write(f"**{match['Equipe B']}**")
    with col3:
        score = st.text_input(f"Score Round {match['Round']} Terrain {match['Terrain']}", value=match["Score"], key=f"score_{match['Round']}_{match['Terrain']}")
        match["Score"] = score

# Classement général
if st.button("📊 Calculer le classement"):
    classement = calculer_classement()
    st.subheader("🏆 Classement général")
    st.dataframe(classement)

    st.subheader("👨 Top 8 Hommes")
    st.dataframe(classement[classement["Joueur"].isin(hommes)].head(8))

    st.subheader("👩 Top 8 Femmes")
    st.dataframe(classement[classement["Joueur"].isin(femmes)].head(8))

    if st.button("⚡ Générer phases finales"):
        generer_finales(classement)
        st.success("Phases finales générées !")

# Phases finales
if st.session_state.finales:
    for phase in ["1/4", "1/2", "Finale"]:
        if phase in st.session_state.finales and st.session_state.finales[phase]:
            st.subheader(f"🏅 {phase}")
            gagnants = []
            for i, match in enumerate(st.session_state.finales[phase]):
                col1, col2, col3 = st.columns([2,2,1])
                with col1:
                    st.write(f"**{match['Equipe A']}**")
                with col2:
                    st.write(f"**{match['Equipe B']}**")
                with col3:
                    score = st.text_input(f"Score {phase} Match {i+1}", value=match["Score"], key=f"score_{phase}_{i}")
                    match["Score"] = score
            if st.button(f"✅ Valider {phase}"):
                gagnants = jouer_phase(phase)
                if phase == "1/4":
                    st.session_state.finales["1/2"] = [{"Equipe A": gagnants[i], "Equipe B": gagnants[i+1], "Score": "", "Vainqueur": ""} for i in range(0, len(gagnants), 2)]
                elif phase == "1/2":
                    st.session_state.finales["Finale"] = [{"Equipe A": gagnants[0], "Equipe B": gagnants[1], "Score": "", "Vainqueur": ""}]
                elif phase == "Finale":
                    st.success(f"🏆 Le grand vainqueur est : {gagnants[0]} !")
