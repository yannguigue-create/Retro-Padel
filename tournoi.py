import streamlit as st
import pandas as pd
import random

# ===============================
# CONFIGURATION DE L'APP
# ===============================
st.set_page_config(page_title="Tournoi de Padel - The Retro Padel", layout="wide")

# Logo et titre
st.image("logo.png", width=250)
st.markdown("<h1 style='text-align: center; color: #1A237E;'>🎾 Tournoi de Padel</h1>", unsafe_allow_html=True)

# ===============================
# PARAMÈTRES DU TOURNOI
# ===============================
st.sidebar.header("⚙️ Paramètres")

hommes_input = st.sidebar.text_area("Liste des hommes (un par ligne)", "Yann\nRomuald\nMatthieu\nKarl\nFranck\nJean Pierre\nBruce\nDimitri\nRomain\nCharles")
femmes_input = st.sidebar.text_area("Liste des femmes (un par ligne)", "Sabine\nElyse\nGarance\nMonica\nCharlotte\nRose\nAline\nCelia\nSophie\nBenoite")

hommes = [h.strip() for h in hommes_input.split("\n") if h.strip()]
femmes = [f.strip() for f in femmes_input.split("\n") if f.strip()]

if "matches" not in st.session_state:
    st.session_state.matches = []
if "resultats" not in st.session_state:
    st.session_state.resultats = []
if "classement" not in st.session_state:
    st.session_state.classement = pd.DataFrame()

# ===============================
# FONCTIONS
# ===============================
def generer_matches():
    matches = []
    random.shuffle(hommes)
    random.shuffle(femmes)
    nb_equipes = min(len(hommes), len(femmes))

    for i in range(0, nb_equipes, 2):
        if i+1 < nb_equipes:
            equipeA = f"{hommes[i]} + {femmes[i]}"
            equipeB = f"{hommes[i+1]} + {femmes[i+1]}"
            matches.append([equipeA, equipeB, ""])
    return matches

def calculer_classement():
    joueurs = {}
    for match in st.session_state.resultats:
        equipeA, equipeB, score = match
        if score:
            try:
                sA, sB = map(int, score.split("-"))
            except:
                continue

            if sA > sB:
                pointsA, pointsB = 3, 0.5
            elif sB > sA:
                pointsA, pointsB = 0.5, 3
            else:
                pointsA, pointsB = 1, 1

            for joueur in equipeA.split(" + "):
                if joueur not in joueurs:
                    joueurs[joueur] = {"Points": 0, "Jeux": 0}
                joueurs[joueur]["Points"] += pointsA
                joueurs[joueur]["Jeux"] += sA

            for joueur in equipeB.split(" + "):
                if joueur not in joueurs:
                    joueurs[joueur] = {"Points": 0, "Jeux": 0}
                joueurs[joueur]["Points"] += pointsB
                joueurs[joueur]["Jeux"] += sB

    classement = pd.DataFrame(joueurs).T.reset_index()
    classement = classement.rename(columns={"index": "Joueur"})
    classement = classement.sort_values(by=["Points", "Jeux"], ascending=[False, False]).reset_index(drop=True)
    return classement

def generer_phase_finale(classement, phase="Quart de finale"):
    st.markdown(f"## 🏆 {phase}")
    qualifies = list(classement.head(8)["Joueur"])
    random.shuffle(qualifies)
    matches = []
    for i in range(0, len(qualifies), 2):
        if i+1 < len(qualifies):
            equipeA = qualifies[i]
            equipeB = qualifies[i+1]
            matches.append([equipeA, equipeB, ""])
    return matches

# ===============================
# GÉNÉRER LES MATCHS
# ===============================
if st.button("🎲 Générer les matchs"):
    st.session_state.matches = generer_matches()
    st.session_state.resultats = [[m[0], m[1], ""] for m in st.session_state.matches]

# ===============================
# AFFICHAGE MATCHS + SCORES
# ===============================
if st.session_state.matches:
    st.markdown("## 📋 Matchs en cours")
    for i, match in enumerate(st.session_state.resultats):
        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            st.write(f"Équipe A : **{match[0]}**")
        with col2:
            score = st.text_input(f"Score du match {i+1} (ex : 6-4)", value=match[2], key=f"score_{i}")
        with col3:
            st.write(f"Équipe B : **{match[1]}**")
        st.session_state.resultats[i][2] = score

# ===============================
# CLASSEMENT
# ===============================
if st.button("✅ Calculer le classement"):
    st.session_state.classement = calculer_classement()

if not st.session_state.classement.empty:
    st.markdown("## 📊 Classement général")
    st.dataframe(st.session_state.classement)

    # ===============================
    # PHASES FINALES
    # ===============================
    if st.button("🏅 Lancer les 1/4 de finale"):
        st.session_state.quarts = generer_phase_finale(st.session_state.classement, "1/4 de finale")
        st.session_state.demis = []
        st.session_state.finale = []

    if "quarts" in st.session_state and st.session_state.quarts:
        for i, match in enumerate(st.session_state.quarts):
            st.write(f"**Match {i+1}** : {match[0]} vs {match[1]}")

    if st.button("🔥 Lancer les 1/2 finales"):
        st.session_state.demis = generer_phase_finale(st.session_state.classement, "1/2 finale")

    if "demis" in st.session_state and st.session_state.demis:
        for i, match in enumerate(st.session_state.demis):
            st.write(f"**Demi {i+1}** : {match[0]} vs {match[1]}")

    if st.button("👑 Lancer la finale"):
        st.session_state.finale = generer_phase_finale(st.session_state.classement, "Finale")

    if "finale" in st.session_state and st.session_state.finale:
        st.markdown(f"### 🎉 Finale : {st.session_state.finale[0][0]} VS {st.session_state.finale[0][1]}")

  
