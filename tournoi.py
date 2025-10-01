import streamlit as st
import random
import pandas as pd

# --- Initialisation ---
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
if "hommes_list" not in st.session_state:
    st.session_state.hommes_list = ""
if "femmes_list" not in st.session_state:
    st.session_state.femmes_list = ""

# --- Sidebar Paramètres ---
st.sidebar.header("⚙️ Paramètres du tournoi")

hommes_input = st.sidebar.text_area(
    "Liste des hommes (un par ligne)", 
    height=150, 
    key="hommes_input",
    value=st.session_state.hommes_list
)
femmes_input = st.sidebar.text_area(
    "Liste des femmes (un par ligne)", 
    height=150, 
    key="femmes_input",
    value=st.session_state.femmes_list
)

# Mise à jour mémoires
st.session_state.hommes_list = hommes_input
st.session_state.femmes_list = femmes_input

# Nettoyage des noms
hommes = [h.strip() for h in hommes_input.splitlines() if h.strip()]
femmes = [f.strip() for f in femmes_input.splitlines() if f.strip()]

# Compteurs
st.sidebar.markdown("---")
st.sidebar.markdown(f"<h3 style='color:#1f77b4;'>👨 Hommes : {len(hommes)}</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"<h3 style='color:#ff69b4;'>👩 Femmes : {len(femmes)}</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"<h3 style='color:#2ca02c;'>🎯 Total : {len(hommes)+len(femmes)}</h3>", unsafe_allow_html=True)
st.sidebar.markdown("---")

nb_terrains = st.sidebar.number_input("Nombre de terrains disponibles", 1, 10, 2, key="nb_terrains")
max_matchs = st.sidebar.number_input("Nombre maximum de matchs par joueur", 1, 20, 2, key="max_matchs")
st.sidebar.markdown("---")

if st.sidebar.button("🔄 Reset Tournoi Complet", type="primary"):
    st.session_state.joueurs = {}
    st.session_state.matchs = []
    st.session_state.scores = {}
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
    st.session_state.classement_calcule = False
    st.success("✅ Tournoi réinitialisé")
    st.rerun()

# --- Initialisation / mise à jour des joueurs ---
for j in list(st.session_state.joueurs.keys()):
    if j not in set(hommes+femmes):
        del st.session_state.joueurs[j]

for h in hommes:
    if h not in st.session_state.joueurs:
        st.session_state.joueurs[h] = {"Points": 0.0, "Jeux": 0, "Matchs": 0, "Sexe": "H"}
for f in femmes:
    if f not in st.session_state.joueurs:
        st.session_state.joueurs[f] = {"Points": 0.0, "Jeux": 0, "Matchs": 0, "Sexe": "F"}

# --- Comptage à jour des matchs PLANIFIÉS (pour respecter max_matchs dès la génération) ---
def scheduled_counts():
    counts = {j: 0 for j in st.session_state.joueurs}
    for rnd in st.session_state.matchs:
        for (e1, e2) in rnd:
            for p in e1 + e2:
                if p in counts:
                    counts[p] += 1
    return counts

# --- Génération d'un round (respect du plafond) ---
def generer_round():
    nb_terrains_dispo = st.session_state.get("nb_terrains", 2)
    max_matchs_joueur = st.session_state.get("max_matchs", 2)

    counts = scheduled_counts()
    joueurs_ok = [j for j in st.session_state.joueurs if counts[j] < max_matchs_joueur]
    hommes_dispo = [j for j in joueurs_ok if st.session_state.joueurs[j]["Sexe"] == "H"]
    femmes_dispo = [j for j in joueurs_ok if st.session_state.joueurs[j]["Sexe"] == "F"]

    random.shuffle(hommes_dispo)
    random.shuffle(femmes_dispo)

    matchs = []
    terrains_possibles = min(nb_terrains_dispo, len(hommes_dispo)//2, len(femmes_dispo)//2)

    for _ in range(terrains_possibles):
        if len(hommes_dispo) >= 2 and len(femmes_dispo) >= 2:
            h1 = hommes_dispo.pop()
            h2 = hommes_dispo.pop()
            f1 = femmes_dispo.pop()
            f2 = femmes_dispo.pop()
            matchs.append(([h1, f1], [h2, f2]))

    if matchs:
        st.session_state.matchs.append(matchs)
        return True, len(matchs)
    return False, 0

# --- Classement (recalcule depuis les scores) ---
def maj_classement():
    for j in st.session_state.joueurs:
        st.session_state.joueurs[j]["Points"] = 0.0
        st.session_state.joueurs[j]["Jeux"] = 0
        st.session_state.joueurs[j]["Matchs"] = 0

    for r_idx, matchs in enumerate(st.session_state.matchs):
        for m_idx, (e1, e2) in enumerate(matchs):
            key = f"score_{r_idx+1}_{m_idx}"
            score = st.session_state.scores.get(key, "")
            if not score or "-" not in score:
                continue
            try:
                s1, s2 = map(int, score.split("-"))
            except:
                continue

            if s1 > s2:
                gagnants, perdants, jg, jp = e1, e2, s1, s2
            else:
                gagnants, perdants, jg, jp = e2, e1, s2, s1

            for p in gagnants:
                st.session_state.joueurs[p]["Points"] += 3.0 + jg*0.1
                st.session_state.joueurs[p]["Jeux"] += jg
                st.session_state.joueurs[p]["Matchs"] += 1
            for p in perdants:
                st.session_state.joueurs[p]["Points"] += jp*0.1
                st.session_state.joueurs[p]["Jeux"] += jp
                st.session_state.joueurs[p]["Matchs"] += 1

# --- Affichage du classement (Points = 1 décimale) ---
def afficher_classement():
    if not st.session_state.joueurs:
        st.warning("Aucun joueur enregistré")
        return
    df = pd.DataFrame.from_dict(st.session_state.joueurs, orient="index").reset_index().rename(columns={"index":"Joueur"})
    df["Points_aff"] = df["Points"].map(lambda x: f"{x:.1f}")  # 1 décimale uniquement
    df = df.sort_values(by=["Points","Jeux"], ascending=False).reset_index(drop=True)
    df.insert(0,"Rang", df.index+1)
    df["Jeux"] = df["Jeux"].astype(int)
    df["Matchs"] = df["Matchs"].astype(int)
    df = df[["Rang","Joueur","Sexe","Points_aff","Jeux","Matchs"]].rename(columns={"Points_aff":"Points"})
    st.table(df)

# --- Top 8 Hommes / Femmes visibles en permanence ---
def afficher_top8_permanents():
    if not st.session_state.joueurs:
        return
    df = pd.DataFrame.from_dict(st.session_state.joueurs, orient="index").reset_index().rename(columns={"index":"Joueur"})
    df = df.sort_values(by=["Points","Jeux"], ascending=False).reset_index(drop=True)
    df["Points"] = df["Points"].map(lambda x: f"{x:.1f}")
    df["Jeux"] = df["Jeux"].astype(int)
    df["Matchs"] = df["Matchs"].astype(int)
    cols = ["Joueur","Points","Jeux","Matchs"]
    colH, colF = st.columns(2)
    with colH:
        st.subheader("👨 Top 8 Hommes (live)")
        st.table(df[df["Sexe"]=="H"][cols].head(8))
    with colF:
        st.subheader("👩 Top 8 Femmes (live)")
        st.table(df[df["Sexe"]=="F"][cols].head(8))

# --- Quarts = Top8 H + Top8 F -> 8 équipes H+F, tirage ALÉATOIRE pour les 4 quarts ---
def generer_quarts_top8_hf():
    maj_classement()
    hommes_tries = sorted(
        [(j, st.session_state.joueurs[j]) for j in st.session_state.joueurs if st.session_state.joueurs[j]["Sexe"]=="H"],
        key=lambda x: (x[1]["Points"], x[1]["Jeux"]), reverse=True
    )
    femmes_tries = sorted(
        [(j, st.session_state.joueurs[j]) for j in st.session_state.joueurs if st.session_state.joueurs[j]["Sexe"]=="F"],
        key=lambda x: (x[1]["Points"], x[1]["Jeux"]), reverse=True
    )
    if len(hommes_tries) < 8:
        st.error(f"❌ Au moins 8 hommes requis (actuellement {len(hommes_tries)})"); return False
    if len(femmes_tries) < 8:
        st.error(f"❌ Au moins 8 femmes requises (actuellement {len(femmes_tries)})"); return False

    top8H = [j for j,_ in hommes_tries[:8]]
    top8F = [j for j,_ in femmes_tries[:8]]
    equipes = [[top8H[i], top8F[i]] for i in range(8)]
    random.shuffle(equipes)
    quarts = [(equipes[i], equipes[i+1]) for i in range(0, 8, 2)]

    st.session_state.phases_finales["quarts"] = quarts
    st.session_state.phases_finales["demis"] = []
    st.session_state.phases_finales["finale"] = []
    st.session_state.phases_finales["vainqueur"] = None
    st.success("✅ Quarts générés (Top8 H & Top8 F, tirage aléatoire) !")
    return True

# --- Recomposition aléatoire des équipes gagnantes (H séparés des F) ---
def recomposer_equipes_mixtes_depuis_gagnants(gagnants):
    """gagnants : liste d'équipes [ [H,F], ... ] -> renvoie une liste de nouvelles équipes H+F recomposées aléatoirement."""
    hommes = [eq[0] for eq in gagnants]
    femmes = [eq[1] for eq in gagnants]
    random.shuffle(hommes)
    random.shuffle(femmes)
    return [[hommes[i], femmes[i]] for i in range(len(gagnants))]

# --- UI ---
st.title("🎾 Tournoi de Padel - Rétro Padel")

# Génération de round (respect plafond)
if len(hommes) < 2 or len(femmes) < 2:
    st.warning("⚠️ Il faut au moins 2 hommes et 2 femmes pour générer un round")
else:
    counts = scheduled_counts()
    hommes_ok = sum(1 for j in st.session_state.joueurs if st.session_state.joueurs[j]["Sexe"]=="H" and counts[j] < max_matchs)
    femmes_ok = sum(1 for j in st.session_state.joueurs if st.session_state.joueurs[j]["Sexe"]=="F" and counts[j] < max_matchs)
    terrains_theoriques = min(nb_terrains, hommes_ok//2, femmes_ok//2)

    if terrains_theoriques > 0:
        col1, col2 = st.columns([3,1])
        with col1:
            st.info(f"ℹ️ Vous pouvez générer **{terrains_theoriques}** match(s) avec **{nb_terrains}** terrain(s) (plafond = {max_matchs} matchs/joueur).")
        with col2:
            if st.button("⚡ Générer un nouveau round", type="primary"):
                ok, nbm = generer_round()
                if ok:
                    st.success(f"✅ Round {len(st.session_state.matchs)} généré ({nbm} match(s)).")
                    st.rerun()
                else:
                    st.error("❌ Impossible de générer un nouveau round (plafond atteint / pas assez de joueurs).")
    else:
        st.info(f"ℹ️ Personne d’éligible (plafond **{max_matchs}** atteint ou pas assez de joueurs H/F).")

# Affichage des rounds & scores
if st.session_state.matchs:
    st.header("📋 Matchs du tournoi")
    for r, matchs in enumerate(st.session_state.matchs, 1):
        st.subheader(f"🏆 Round {r}")
        for idx, (e1, e2) in enumerate(matchs):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Terrain {idx+1}:** {e1[0]} (H) + {e1[1]} (F)  🆚  {e2[0]} (H) + {e2[1]} (F)")
            with col2:
                score_key = f"score_{r}_{idx}"
                score = st.text_input("Score (ex: 6-4)", key=score_key, label_visibility="collapsed")
                if score:
                    st.session_state.scores[score_key] = score

    st.markdown("---")
    if st.button("📊 Calculer le classement", type="primary"):
        maj_classement()
        st.session_state.classement_calcule = True
        st.rerun()

# Classement + Top 8 live
if st.session_state.classement_calcule or any(st.session_state.joueurs[j]["Matchs"] > 0 for j in st.session_state.joueurs):
    st.header("📊 Classement général")
    maj_classement()
    afficher_classement()
    afficher_top8_permanents()

# --- Phases finales ---
st.markdown("---")
st.header("🏆 Phases Finales")

c1, c2 = st.columns(2)
with c1:
    if st.button("⚡ Quarts Top 8 (H & F) – Tirage aléatoire", type="primary"):
        if generer_quarts_top8_hf():
            st.rerun()
with c2:
    if st.button("♻️ Reset Phases Finales"):
        st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
        st.success("✅ Phases finales réinitialisées")
        st.rerun()

# Quarts (toujours visibles)
if st.session_state.phases_finales["quarts"]:
    st.subheader("⚔️ Quarts de finale")
    gagnants_quarts = []
    for idx, (e1, e2) in enumerate(st.session_state.phases_finales["quarts"]):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**Quart {idx+1}:** {e1[0]} (H)+{e1[1]} (F)  🆚  {e2[0]} (H)+{e2[1]} (F)")
        with col2:
            score = st.text_input("Score", key=f"quart_{idx}", label_visibility="collapsed")
            if score and "-" in score:
                try:
                    s1, s2 = map(int, score.split("-"))
                    gagnants_quarts.append(e1 if s1 > s2 else e2)
                except:
                    pass

    # Tirage des 1/2 avec recomposition des équipes à partir des GAGNANTS des quarts
    if len(gagnants_quarts) == 4 and st.button("➡️ Valider & Tirage aléatoire des Demi-finales"):
        # 1) recomposer 4 nouvelles équipes H+F (mélange des H et des F gagnants)
        nouvelles_equipes = recomposer_equipes_mixtes_depuis_gagnants(gagnants_quarts)
        # 2) tirage aléatoire du tableau
        random.shuffle(nouvelles_equipes)
        st.session_state.phases_finales["demis"] = [
            (nouvelles_equipes[0], nouvelles_equipes[1]),
            (nouvelles_equipes[2], nouvelles_equipes[3])
        ]
        # on conserve l'affichage des quarts
        st.rerun()

# Demis (toujours visibles)
if st.session_state.phases_finales["demis"]:
    st.subheader("⚔️ Demi-finales")
    gagnants_demis = []
    for idx, (e1, e2) in enumerate(st.session_state.phases_finales["demis"]):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**Demi {idx+1}:** {e1[0]} (H)+{e1[1]} (F)  🆚  {e2[0]} (H)+{e2[1]} (F)")
        with col2:
            score = st.text_input("Score", key=f"demi_{idx}", label_visibility="collapsed")
            if score and "-" in score:
                try:
                    s1, s2 = map(int, score.split("-"))
                    gagnants_demis.append(e1 if s1 > s2 else e2)
                except:
                    pass

    # Tirage de la FINALE avec recomposition à partir des gagnants des demis
    if len(gagnants_demis) == 2 and st.button("➡️ Valider & Tirage aléatoire de la Finale"):
        equipes_finale = recomposer_equipes_mixtes_depuis_gagnants(gagnants_demis)  # 2 équipes recomposées
        random.shuffle(equipes_finale)  # pour l’ordre
        st.session_state.phases_finales["finale"] = [(equipes_finale[0], equipes_finale[1])]
        # on conserve l'affichage des demis
        st.rerun()

# Finale
if st.session_state.phases_finales["finale"]:
    st.subheader("🏆 FINALE")
    e1, e2 = st.session_state.phases_finales["finale"][0]
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**{e1[0]} (H)+{e1[1]} (F)**  🆚  **{e2[0]} (H)+{e2[1]} (F)**")
    with col2:
        score = st.text_input("Score final", key="finale_score", label_visibility="collapsed")
        if score and "-" in score:
            try:
                s1, s2 = map(int, score.split("-"))
                vainqueur = e1 if s1 > s2 else e2
                if st.button("🏅 Valider le vainqueur"):
                    st.session_state.phases_finales["vainqueur"] = vainqueur
                    st.rerun()
            except:
                pass

if st.session_state.phases_finales.get("vainqueur"):
    v = st.session_state.phases_finales["vainqueur"]
    st.balloons()
    st.success(f"🎉🏆 **VAINQUEURS : {v[0]} & {v[1]} !**")

# Top 8 permanents toujours visibles
st.markdown("---")
afficher_top8_permanents()
