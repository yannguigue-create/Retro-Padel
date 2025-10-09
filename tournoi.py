import streamlit as st
import random
import pandas as pd

# -----------------------------
#       INITIALISATION
# -----------------------------
if "joueurs" not in st.session_state:
    st.session_state.joueurs = {}
if "matchs" not in st.session_state:
    st.session_state.matchs = []         # liste de rounds ; round = liste de matchs ; match = ([H,F],[H,F])
if "scores" not in st.session_state:
    st.session_state.scores = {}         # score_key -> "6-4"
if "phases_finales" not in st.session_state:
    st.session_state.phases_finales = {
        "quarts": [],
        "demis": [],
        "finale": [],
        "vainqueur": None
    }
if "classement_calcule" not in st.session_state:
    st.session_state.classement_calcule = False

st.set_page_config(page_title="Tournoi de Padel - Rétro Padel", page_icon="🎾", layout="wide")

# -----------------------------
#       SIDEBAR PARAMS
# -----------------------------
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

nb_terrains = st.sidebar.number_input("Nombre de terrains disponibles", 1, 16, 4, step=1)
max_matchs = st.sidebar.number_input("Nombre maximum de matchs par joueur", 1, 50, 4, step=1)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reset Tournoi Complet", type="primary"):
    st.session_state.joueurs = {}
    st.session_state.matchs = []
    st.session_state.scores = {}
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
    st.session_state.classement_calcule = False
    st.rerun()

# -----------------------------
#   INIT / SYNC LISTES JOUEURS
# -----------------------------
# Supprimer les joueurs retirés
for j in list(st.session_state.joueurs.keys()):
    if j not in (hommes + femmes):
        del st.session_state.joueurs[j]

# Ajouter nouveaux
for h in hommes:
    if h not in st.session_state.joueurs:
        st.session_state.joueurs[h] = {"Points": 0.0, "Jeux": 0, "Matchs": 0, "Sexe": "H"}
for f in femmes:
    if f not in st.session_state.joueurs:
        st.session_state.joueurs[f] = {"Points": 0.0, "Jeux": 0, "Matchs": 0, "Sexe": "F"}

# -----------------------------
#  CALCUL CLASSEMENT / POINTS
# -----------------------------
def maj_classement():
    # Reset
    for j in st.session_state.joueurs:
        st.session_state.joueurs[j]["Points"] = 0.0
        st.session_state.joueurs[j]["Jeux"] = 0
        st.session_state.joueurs[j]["Matchs"] = 0

    # Recalcul depuis TOUS les rounds
    for round_idx, matchs in enumerate(st.session_state.matchs):
        for match_idx, (equipe1, equipe2) in enumerate(matchs):
            score_key = f"score_{round_idx+1}_{match_idx}"
            score = st.session_state.scores.get(score_key, "")
            if not score or "-" not in score:
                continue
            try:
                s1, s2 = map(int, score.split("-"))
            except Exception:
                continue

            if s1 > s2:
                gagnants, perdants, js_gagnants, js_perdants = equipe1, equipe2, s1, s2
            else:
                gagnants, perdants, js_gagnants, js_perdants = equipe2, equipe1, s2, s1

            # Gagnants : 3 + 0.1 par jeu
            for j in gagnants:
                if j in st.session_state.joueurs:
                    st.session_state.joueurs[j]["Points"] += 3.0 + js_gagnants * 0.1
                    st.session_state.joueurs[j]["Jeux"] += js_gagnants
                    st.session_state.joueurs[j]["Matchs"] += 1

            # Perdants : 0.5 + 0.1 par jeu
            for j in perdants:
                if j in st.session_state.joueurs:
                    st.session_state.joueurs[j]["Points"] += 0.5 + js_perdants * 0.1
                    st.session_state.joueurs[j]["Jeux"] += js_perdants
                    st.session_state.joueurs[j]["Matchs"] += 1

def afficher_classement():
    if not st.session_state.joueurs:
        st.warning("Aucun joueur")
        return
    df = pd.DataFrame.from_dict(st.session_state.joueurs, orient="index").reset_index().rename(columns={"index":"Joueur"})
    df["Points"] = df["Points"].round(1)   # une seule décimale
    df["Jeux"] = df["Jeux"].astype(int)
    df["Matchs"] = df["Matchs"].astype(int)
    df = df.sort_values(by=["Points","Jeux"], ascending=False).reset_index(drop=True)
    df.insert(0, "Rang", df.index+1)
    df = df[["Rang","Joueur","Sexe","Points","Jeux","Matchs"]]
    st.table(df)

# -----------------------------
#        GENERATION ROUNDS
# -----------------------------
def generer_round():
    """Crée un round en privilégiant les joueurs avec le moins de matchs.
       Respecte max_matchs et nb_terrains. Paires 1H+1F vs 1H+1F."""
    maj_classement()

    if not st.session_state.joueurs:
        return False, 0

    # Prendre d'abord ceux qui ont le minimum de matchs joués (équité)
    min_m = min(j["Matchs"] for j in st.session_state.joueurs.values()) if st.session_state.joueurs else 0
    candidats = [j for j, d in st.session_state.joueurs.items() if d["Matchs"] == min_m and d["Matchs"] < max_matchs]

    if len(candidats) < 4:
        # élargir si pas assez
        candidats = [j for j, d in st.session_state.joueurs.items() if d["Matchs"] < max_matchs]

    hommes_dispo = [j for j in candidats if st.session_state.joueurs[j]["Sexe"] == "H"]
    femmes_dispo = [j for j in candidats if st.session_state.joueurs[j]["Sexe"] == "F"]
    random.shuffle(hommes_dispo)
    random.shuffle(femmes_dispo)

    # nombre de matchs possible ce round
    terrains = min(nb_terrains, len(hommes_dispo)//2, len(femmes_dispo)//2)
    matchs = []
    for _ in range(terrains):
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

def generer_tous_rounds(max_iter=200):
    """Génère tous les rounds possibles jusqu'à ce que plus personne ne puisse jouer
       (respect de max_matchs et nb_terrains)."""
    count = 0
    for _ in range(max_iter):
        ok, _n = generer_round()
        if not ok:
            break
        count += 1
    return count

# -----------------------------
#   OUTILS PHASES FINALES
# -----------------------------
def split_hf(team):
    """Retourne (homme, femme) pour l'équipe [p1,p2]."""
    h = next(p for p in team if st.session_state.joueurs[p]["Sexe"] == "H")
    f = next(p for p in team if st.session_state.joueurs[p]["Sexe"] == "F")
    return h, f

def generer_quarts_top8():
    """Top 8 hommes + Top 8 femmes -> 4 matchs (1H+1F par équipe).
       Tirage aléatoire des paires puis des affiches."""
    maj_classement()
    # tri global
    tri = sorted(st.session_state.joueurs.items(),
                 key=lambda x: (x[1]["Points"], x[1]["Jeux"]),
                 reverse=True)

    top_h = [j for j,_ in tri if st.session_state.joueurs[j]["Sexe"]=="H"][:8]
    top_f = [j for j,_ in tri if st.session_state.joueurs[j]["Sexe"]=="F"][:8]

    if len(top_h) < 8 or len(top_f) < 8:
        st.error(f"❌ Il faut 8 hommes et 8 femmes dans le top (actuellement H:{len(top_h)} F:{len(top_f)})")
        return False

    random.shuffle(top_h)
    random.shuffle(top_f)
    equipes = [[top_h[i], top_f[i]] for i in range(8)]
    random.shuffle(equipes)
    quarts = [(equipes[0], equipes[1]),
              (equipes[2], equipes[3]),
              (equipes[4], equipes[5]),
              (equipes[6], equipes[7])]
    st.session_state.phases_finales["quarts"] = quarts
    return True

# -----------------------------
#             UI
# -----------------------------
st.title("🎾 Tournoi de Padel - Rétro Padel")

# Génération rounds
if len(hommes) >= 2 and len(femmes) >= 2:
    colA, colB = st.columns(2)
    with colA:
        if st.button("⚡ Générer 1 round", use_container_width=True):
            ok, nbm = generer_round()
            if ok:
                st.success(f"✅ Round {len(st.session_state.matchs)} généré ({nbm} match(s))")
            else:
                st.warning("Plus de round possible")
            st.rerun()
    with colB:
        if st.button("🚀 Générer TOUS les rounds", use_container_width=True):
            nbR = generer_tous_rounds()
            if nbR > 0:
                st.success(f"✅ {nbR} round(s) généré(s)")
            else:
                st.info("Aucun round supplémentaire possible")
            st.rerun()
else:
    st.warning("⚠️ Il faut au moins 2 hommes et 2 femmes pour commencer.")

# Affichage des rounds et saisie des scores
if st.session_state.matchs:
    st.markdown("---")
    st.header("📋 Matchs du tournoi")
    for r, matchs in enumerate(st.session_state.matchs, 1):
        with st.expander(f"🏆 Round {r} – {len(matchs)} match(s)", expanded=(r == len(st.session_state.matchs))):
            for idx, (e1, e2) in enumerate(matchs):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Terrain {idx+1} :** {e1[0]} (H) + {e1[1]} (F)  🆚  {e2[0]} (H) + {e2[1]} (F)")
                with col2:
                    key = f"score_{r}_{idx}"
                    sc = st.text_input("Score (ex: 6-4)", key=key, label_visibility="collapsed")
                    if sc:
                        st.session_state.scores[key] = sc

    st.markdown("---")
    if st.button("📊 Calculer le classement", type="primary"):
        maj_classement()
        st.session_state.classement_calcule = True
        st.rerun()

# Classement + Top 8 permanents
if st.session_state.joueurs:
    st.header("📈 Classement général")
    maj_classement()
    afficher_classement()

    # TOP 8 H / F
    tri_all = sorted(st.session_state.joueurs.items(),
                     key=lambda x: (x[1]["Points"], x[1]["Jeux"]),
                     reverse=True)
    top_h = [ (j,d) for j,d in tri_all if d["Sexe"]=="H" ][:8]
    top_f = [ (j,d) for j,d in tri_all if d["Sexe"]=="F" ][:8]

    colH, colF = st.columns(2)
    with colH:
        st.subheader("🏅 Top 8 Hommes")
        if top_h:
            dfH = pd.DataFrame([{
                "Joueur": j,
                "Points": round(d["Points"], 1),
                "Jeux": int(d["Jeux"]),
                "Matchs": int(d["Matchs"])
            } for j,d in top_h])
            st.table(dfH)
        else:
            st.info("Pas assez d'hommes")

    with colF:
        st.subheader("🏅 Top 8 Femmes")
        if top_f:
            dfF = pd.DataFrame([{
                "Joueur": j,
                "Points": round(d["Points"], 1),
                "Jeux": int(d["Jeux"]),
                "Matchs": int(d["Matchs"])
            } for j,d in top_f])
            st.table(dfF)
        else:
            st.info("Pas assez de femmes")

# -----------------------------
#        PHASES FINALES
# -----------------------------
st.markdown("---")
st.header("🏆 Phases Finales")

colQ, colR = st.columns([1,1])
with colQ:
    if st.button("⚡ Quarts Top 8 (H & F) – Tirage aléatoire"):
        if generer_quarts_top8():
            st.success("✅ Quarts générés (Top 8 H & F) !")
            st.rerun()

with colR:
    if st.button("♻️ Reset Phases Finales"):
        st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
        st.success("Phases finales réinitialisées")
        st.rerun()

# --- QUARTS ---
if st.session_state.phases_finales["quarts"]:
    st.subheader("🗡️ Quarts de finale")
    gagnants_quarts = []
    for idx, (e1, e2) in enumerate(st.session_state.phases_finales["quarts"]):
        col1, col2 = st.columns([3,1])
        with col1:
            st.write(f"**Quart {idx+1} :** {e1[0]} (H)+{e1[1]} (F)  vs  {e2[0]} (H)+{e2[1]} (F)")
        with col2:
            sc = st.text_input("Score", key=f"quart_{idx}", label_visibility="collapsed")
            if sc and "-" in sc:
                try:
                    s1, s2 = map(int, sc.split("-"))
                    gagnants_quarts.append(e1 if s1 > s2 else e2)
                except Exception:
                    pass

    # Bouton de validation et tirage DEMIS aléatoire AVEC RECOMPOSITION DES PAIRES
    if len(gagnants_quarts) == 4 and st.button("✅ Valider & Tirage aléatoire des Demi-finales"):
        hommes = []
        femmes = []
        for team in gagnants_quarts:
            h, f = split_hf(team)
            hommes.append(h)
            femmes.append(f)
        random.shuffle(hommes)
        random.shuffle(femmes)
        nouvelles_equipes = [[hommes[0], femmes[0]],
                             [hommes[1], femmes[1]],
                             [hommes[2], femmes[2]],
                             [hommes[3], femmes[3]]]
        random.shuffle(nouvelles_equipes)
        st.session_state.phases_finales["demis"] = [
            (nouvelles_equipes[0], nouvelles_equipes[1]),
            (nouvelles_equipes[2], nouvelles_equipes[3]),
        ]
        # On laisse les quarts visibles (on ne les efface pas)
        st.success("Demi-finales tirées au sort avec recomposition des paires !")
        st.rerun()

# --- DEMIS ---
if st.session_state.phases_finales["demis"]:
    st.subheader("⚔️ Demi-finales")
    gagnants_demis = []
    for idx, (e1, e2) in enumerate(st.session_state.phases_finales["demis"]):
        col1, col2 = st.columns([3,1])
        with col1:
            st.write(f"**Demi-finale {idx+1} :** {e1[0]} (H)+{e1[1]} (F)  vs  {e2[0]} (H)+{e2[1]} (F)")
        with col2:
            sc = st.text_input("Score", key=f"demi_{idx}", label_visibility="collapsed")
            if sc and "-" in sc:
                try:
                    s1, s2 = map(int, sc.split("-"))
                    gagnants_demis.append(e1 if s1 > s2 else e2)
                except Exception:
                    pass

    # Validation et tirage FINAL aléatoire AVEC recomposition
    if len(gagnants_demis) == 2 and st.button("✅ Valider & Tirage aléatoire de la Finale"):
        hommes = []
        femmes = []
        for team in gagnants_demis:
            h, f = split_hf(team)
            hommes.append(h)
            femmes.append(f)
        random.shuffle(hommes)
        random.shuffle(femmes)
        final_teams = [[hommes[0], femmes[0]],
                       [hommes[1], femmes[1]]]
        random.shuffle(final_teams)
        st.session_state.phases_finales["finale"] = [tuple(final_teams)]
        # On laisse les demis visibles
        st.success("Finale tirée au sort avec recomposition des paires !")
        st.rerun()

# --- FINALE ---
if st.session_state.phases_finales["finale"]:
    st.subheader("🏆 FINALE")
    e1, e2 = st.session_state.phases_finales["finale"][0]
    col1, col2 = st.columns([3,1])
    with col1:
        st.write(f"**{e1[0]} (H)+{e1[1]} (F)  vs  {e2[0]} (H)+{e2[1]} (F)**")
    with col2:
        sc = st.text_input("Score final", key="finale_score", label_visibility="collapsed")
        if sc and "-" in sc:
            try:
                s1, s2 = map(int, sc.split("-"))
                vainqueur = e1 if s1 > s2 else e2
                if st.button("🏆 Déclarer le vainqueur"):
                    st.session_state.phases_finales["vainqueur"] = vainqueur
                    st.session_state.phases_finales["finale"] = []
                    st.rerun()
            except Exception:
                pass

if st.session_state.phases_finales.get("vainqueur"):
    v = st.session_state.phases_finales["vainqueur"]
    st.balloons()
    st.success(f"🎉 **VAINQUEURS DU TOURNOI : {v[0]} et {v[1]} !** 🎉")
