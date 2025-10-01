import streamlit as st
import pandas as pd
import random

# ======================
# CONFIGURATION PAGE
# ======================
st.set_page_config(
    page_title="Tournoi de Padel - Retro Padel",
    page_icon="🎾",
    layout="wide"
)

# ======================
# LOGO + TITRE
# ======================
st.image("https://raw.githubusercontent.com/ton-repo/logo/main/logo.png", width=250)
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🎾 Tournoi de Padel - The Retro Padel</h1>", unsafe_allow_html=True)
st.markdown("---")

# ======================
# PARAMÈTRES
# ======================
with st.sidebar:
    st.header("⚙️ Paramètres du tournoi")
    hommes_input = st.text_area("Liste des hommes (un par ligne)", "Yann\nRomuald\nMatthieu\nKarl")
    femmes_input = st.text_area("Liste des femmes (un par ligne)", "Sabine\nElyse\nGarance\nMonica")

    hommes = [h.strip() for h in hommes_input.split("\n") if h.strip()]
    femmes = [f.strip() for f in femmes_input.split("\n") if f.strip()]

    if st.button("🔄 Réinitialiser"):
        st.session_state.clear()
        st.experimental_rerun()

# ======================
# INITIALISATION
# ======================
if "matchs" not in st.session_state:
    st.session_state.matchs = []
if "scores" not in st.session_state:
    st.session_state.scores = {}
if "classement" not in st.session_state:
    st.session_state.classement = pd.DataFrame(columns=["Joueur", "Sexe", "Points", "Jeux"])

# ======================
# GÉNÉRATION MATCHS
# ======================
if st.button("🎲 Générer les matchs"):
    random.shuffle(hommes)
    random.shuffle(femmes)
    st.session_state.matchs = []
    for i in range(min(len(hommes), len(femmes)) // 2):
        h1, h2 = hommes[2*i], hommes[2*i+1]
        f1, f2 = femmes[2*i], femmes[2*i+1]
        st.session_state.matchs.append(((h1, f1), (h2, f2)))

# ======================
# AFFICHAGE MATCHS + SCORES
# ======================
if st.session_state.matchs:
    st.subheader("📋 Matchs en cours")
    cols = st.columns(2)
    for idx, (eqA, eqB) in enumerate(st.session_state.matchs, 1):
        with cols[idx % 2]:
            score = st.text_input(f"Score du match {idx} ({eqA[0]} + {eqA[1]} vs {eqB[0]} + {eqB[1]})", key=f"score_{idx}")
            st.session_state.scores[idx] = {"A": eqA, "B": eqB, "score": score}

# ======================
# CALCUL CLASSEMENT
# ======================
if st.button("📊 Calculer le classement"):
    data = []
    for match in st.session_state.scores.values():
        if match["score"]:
            try:
                scA, scB = map(int, match["score"].split("-"))
                if scA > scB:
                    gagnants, perdants = match["A"], match["B"]
                    ptsA, ptsB = 3, 0.5
                else:
                    gagnants, perdants = match["B"], match["A"]
                    ptsA, ptsB = 0.5, 3

                for j in match["A"]:
                    data.append([j, "H" if j in hommes else "F", ptsA, scA])
                for j in match["B"]:
                    data.append([j, "H" if j in hommes else "F", ptsB, scB])
            except:
                st.error(f"⚠️ Score invalide : {match['score']}")

    df = pd.DataFrame(data, columns=["Joueur", "Sexe", "Points", "Jeux"])
    classement = df.groupby(["Joueur", "Sexe"], as_index=False).sum()
    classement = classement.sort_values(by=["Points", "Jeux"], ascending=False)

    st.session_state.classement = classement

    st.success("✅ Classement mis à jour !")

# ======================
# AFFICHAGE CLASSEMENT
# ======================
if not st.session_state.classement.empty:
    st.subheader("🏆 Classement général")
    st.dataframe(st.session_state.classement)

    # TOP 8 hommes et femmes
    top_h = st.session_state.classement[st.session_state.classement["Sexe"]=="H"].head(8)
    top_f = st.session_state.classement[st.session_state.classement["Sexe"]=="F"].head(8)

    st.subheader("👨‍🦱 Top 8 Hommes")
    st.table(top_h)

    st.subheader("👩 Top 8 Femmes")
    st.table(top_f)

# ======================
# PHASES FINALES
# ======================
if st.button("⚡ Générer les phases finales"):
    if st.session_state.classement.empty:
        st.error("⚠️ Calcule d'abord le classement avant de générer les phases finales !")
    else:
        st.subheader("🎯 Phases Finales (1/4 - 1/2 - Finale)")

        qualifiés = list(st.session_state.classement.head(8)["Joueur"])
        random.shuffle(qualifiés)

        quarts = [(qualifiés[i], qualifiés[i+1]) for i in range(0, 8, 2)]
        st.write("### 🟢 Quarts de finale")
        for q in quarts: st.write(f"{q[0]} vs {q[1]}")

        demis = [(quarts[0][0], quarts[1][0]), (quarts[2][0], quarts[3][0])]
        st.write("### 🟠 Demi-finales")
        for d in demis: st.write(f"{d[0]} vs {d[1]}")

        finale = (demis[0][0], demis[1][0])
        st.write("### 🔴 Finale")
        st.write(f"{finale[0]} vs {finale[1]}")
