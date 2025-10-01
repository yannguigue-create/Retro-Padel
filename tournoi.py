import streamlit as st
import random
import pandas as pd

st.set_page_config(page_title="Tournoi de Padel", layout="wide")

st.title("🎾 Tournoi de Padel")

# ----------------------------
# Initialisation session state
# ----------------------------
if "joueurs_h" not in st.session_state:
    st.session_state.joueurs_h = ["Yann", "Romuald", "Jean Pierre", "Franck", "Romain", "Karl", "Bruce", "Matthieu"]
if "joueurs_f" not in st.session_state:
    st.session_state.joueurs_f = ["Charlotte", "Monica", "Garance", "Benoite", "Sabine", "Caroline", "Elyse", "Rose"]
if "matchs" not in st.session_state:
    st.session_state.matchs = []
if "scores" not in st.session_state:
    st.session_state.scores = {}

# ----------------------------
# Saisie des joueurs
# ----------------------------
st.sidebar.header("⚙️ Paramètres")
joueurs_hommes = st.sidebar.text_area("Liste des hommes (un par ligne)", "\n".join(st.session_state.joueurs_h)).split("\n")
joueurs_femmes = st.sidebar.text_area("Liste des femmes (un par ligne)", "\n".join(st.session_state.joueurs_f)).split("\n")

st.session_state.joueurs_h = [j.strip() for j in joueurs_hommes if j.strip()]
st.session_state.joueurs_f = [j.strip() for j in joueurs_femmes if j.strip()]

# ----------------------------
# Tirage des matchs
# ----------------------------
if st.button("🎲 Générer les matchs"):
    random.shuffle(st.session_state.joueurs_h)
    random.shuffle(st.session_state.joueurs_f)
    equipes = [(h, f) for h, f in zip(st.session_state.joueurs_h, st.session_state.joueurs_f)]
    random.shuffle(equipes)

    matchs = []
    for i in range(0, len(equipes), 2):
        if i + 1 < len(equipes):
            matchs.append((equipes[i], equipes[i+1]))

    st.session_state.matchs = matchs
    st.session_state.scores = {}

# ----------------------------
# Affichage des matchs + saisie score
# ----------------------------
if st.session_state.matchs:
    st.subheader("📋 Matchs en cours")

    for idx, ((h1, f1), (h2, f2)) in enumerate(st.session_state.matchs, start=1):
        col1, col2, col3 = st.columns([3,1,3])
        with col1:
            st.markdown(f"**Équipe A : {h1} + {f1}**")
        with col2:
            score = st.text_input(f"Score match {idx} (ex: 6-4)", key=f"score_{idx}")
            st.session_state.scores[idx] = score
        with col3:
            st.markdown(f"**Équipe B : {h2} + {f2}**")

# ----------------------------
# Classement
# ----------------------------
if st.button("✅ Calculer classement"):
    points = {}
    jeux = {}

    for idx, ((h1, f1), (h2, f2)) in enumerate(st.session_state.matchs, start=1):
        score = st.session_state.scores.get(idx, "")
        if "-" in score:
            try:
                sA, sB = map(int, score.split("-"))
            except:
                continue

            # Victoire/défaite
            if sA > sB:
                gagnants, perdants = [(h1, f1)], [(h2, f2)]
                ptsA, ptsB = 3, 0.5
            else:
                gagnants, perdants = [(h2, f2)], [(h1, f1)]
                ptsA, ptsB = 0.5, 3

            # Points et jeux
            for h, f in gagnants[0]:
                pass
            for player in [h1, f1]:
                points[player] = points.get(player, 0) + ptsA
                jeux[player] = jeux.get(player, 0) + sA
            for player in [h2, f2]:
                points[player] = points.get(player, 0) + ptsB
                jeux[player] = jeux.get(player, 0) + sB

    # Classement DataFrame
    data = []
    for j in st.session_state.joueurs_h + st.session_state.joueurs_f:
        data.append([j, points.get(j, 0), jeux.get(j, 0)])
    df = pd.DataFrame(data, columns=["Joueur", "Points", "Jeux"]).sort_values(by=["Points", "Jeux"], ascending=[False, False])

    st.subheader("🏆 Classement")
    st.dataframe(df, use_container_width=True)

    # Sauvegarde classement
    st.session_state.classement = df

# ----------------------------
# Phases finales
# ----------------------------
if "classement" in st.session_state:
    if st.button("⚡ Générer 1/4 de finale"):
        qualifiés = list(st.session_state.classement.head(8)["Joueur"])
        random.shuffle(qualifiés)
        quarts = [(qualifiés[i], qualifiés[i+1]) for i in range(0, 8, 2)]
        st.session_state.quarts = quarts

    if "quarts" in st.session_state:
        st.subheader("1/4 de finale")
        for i, (j1, j2) in enumerate(st.session_state.quarts, 1):
            st.write(f"Match {i} : {j1} vs {j2}")
