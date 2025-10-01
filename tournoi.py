import streamlit as st
import random
import pandas as pd

# =========================
#   INIT SESSION STATE
# =========================
def _ensure_state():
    ss = st.session_state
    ss.setdefault("joueurs", {})                  # {nom: {Points, Jeux, Matchs, Sexe}}
    ss.setdefault("matchs", [])                   # [[(e1,e2), (e1,e2), ...], ...] par round
    ss.setdefault("scores", {})                   # {(round_idx, match_idx): "6-3"}
    ss.setdefault("phases_finales", {            # phases finales
        "quarts": [],
        "demis": [],
        "finale": [],
        "vainqueur": None
    })

_ensure_state()

# =========================
#   SIDEBAR - PARAMÈTRES
# =========================
st.sidebar.header("⚙️ Paramètres du tournoi")

hommes = [h.strip() for h in st.sidebar.text_area("Liste des hommes (un par ligne)").splitlines() if h.strip()]
femmes = [f.strip() for f in st.sidebar.text_area("Liste des femmes (un par ligne)").splitlines() if f.strip()]
nb_terrains = st.sidebar.number_input("Nombre de terrains disponibles", 1, 12, 2)
max_matchs = st.sidebar.number_input("Nombre maximum de matchs par joueur", 1, 10, 2)

st.sidebar.markdown(f"👨 Hommes : **{len(hommes)}**")
st.sidebar.markdown(f"👩 Femmes : **{len(femmes)}**")
st.sidebar.markdown(f"🔢 Total joueurs : **{len(hommes)+len(femmes)}**")

if st.sidebar.button("🔄 Reset Tournoi"):
    st.session_state.clear()
    _ensure_state()
    st.success("Tournoi réinitialisé.")
    st.rerun()

# =========================
#  ENREGISTREMENT JOUEURS
# =========================
for h in hommes:
    st.session_state.joueurs.setdefault(h, {"Points": 0.0, "Jeux": 0, "Matchs": 0, "Sexe": "H"})
for f in femmes:
    st.session_state.joueurs.setdefault(f, {"Points": 0.0, "Jeux": 0, "Matchs": 0, "Sexe": "F"})

# =========================
#   UTILS
# =========================
def format_team(team):
    # team = [H, F]
    return f"{team[0]} (H) + {team[1]} (F)"

def joueurs_disponibles_pour_round(max_matchs):
    """Joueurs qui n'ont pas encore atteint leur quota."""
    return [j for j, info in st.session_state.joueurs.items() if info["Matchs"] < max_matchs]

def reset_stats():
    """Remet points/jeux/matchs à zéro avant recalcul complet."""
    for j in st.session_state.joueurs:
        st.session_state.joueurs[j]["Points"] = 0.0
        st.session_state.joueurs[j]["Jeux"] = 0
        st.session_state.joueurs[j]["Matchs"] = 0

# =========================
#   GÉNÉRATION DES ROUNDS
# =========================
def generer_round():
    # candidats = joueurs sous le quota
    candidats = joueurs_disponibles_pour_round(max_matchs)
    random.shuffle(candidats)

    H = [j for j in candidats if st.session_state.joueurs[j]["Sexe"] == "H"]
    F = [j for j in candidats if st.session_state.joueurs[j]["Sexe"] == "F"]

    # nombre maximum de matchs jouables ce round
    nb_matchs_round = min(nb_terrains, len(H)//2, len(F)//2)
    if nb_matchs_round <= 0:
        st.warning("Pas assez de joueurs disponibles (ou quota atteint) pour générer un round.")
        return

    matchs = []
    for _ in range(nb_matchs_round):
        # on forme des équipes 1H + 1F vs 1H + 1F
        h1, h2 = H.pop(), H.pop()
        f1, f2 = F.pop(), F.pop()
        e1, e2 = [h1, f1], [h2, f2]
        matchs.append((e1, e2))

    st.session_state.matchs.append(matchs)
    st.success(f"Round {len(st.session_state.matchs)} généré avec {nb_matchs_round} match(s).")

# =========================
#   CLASSEMENT
# =========================
def maj_classement_depuis_tous_les_scores():
    """Recalcule le classement à partir de tous les scores saisis."""
    reset_stats()

    for r, matchs in enumerate(st.session_state.matchs):
        for i, (e1, e2) in enumerate(matchs):
            key = (r, i)
            score = st.session_state.scores.get(key, "").strip()
            if not score:
                continue
            try:
                s1, s2 = map(int, score.split("-"))
            except ValueError:
                continue

            # gagnants/perdants
            if s1 > s2:
                gagnants, perdants, jg, jp = e1, e2, s1, s2
            else:
                gagnants, perdants, jg, jp = e2, e1, s2, s1

            # MAJ stats
            for j in gagnants:
                st.session_state.joueurs[j]["Points"] += 3 + 0.1 * jg
                st.session_state.joueurs[j]["Jeux"] += jg
                st.session_state.joueurs[j]["Matchs"] += 1
            for j in perdants:
                st.session_state.joueurs[j]["Points"] += 0.1 * jp
                st.session_state.joueurs[j]["Jeux"] += jp
                st.session_state.joueurs[j]["Matchs"] += 1

def afficher_classement():
    df = pd.DataFrame.from_dict(st.session_state.joueurs, orient="index")
    df = df.reset_index().rename(columns={"index": "Joueur"})
    df["Points"] = df["Points"].round(1)
    df["Jeux"] = df["Jeux"].astype(int)
    df["Matchs"] = df["Matchs"].astype(int)
    df = df.sort_values(["Points", "Jeux"], ascending=False).reset_index(drop=True)
    df.insert(0, "Rang", df.index + 1)
    st.subheader("🥇 Classement Général")
    st.dataframe(df, use_container_width=True)

# =========================
#   PHASES FINALES
# =========================
def generer_quarts():
    # on prend les 8 meilleurs
    classement = sorted(
        st.session_state.joueurs.items(),
        key=lambda kv: (kv[1]["Points"], kv[1]["Jeux"]),
        reverse=True
    )
    top8 = [j for j, _ in classement[:8]]
    if len(top8) < 8:
        st.warning("Il faut 8 joueurs pour générer les quarts.")
        return

    # on s'assure de l'équilibre H/F par match (1H+1F vs 1H+1F)
    H = [j for j in top8 if st.session_state.joueurs[j]["Sexe"] == "H"]
    F = [j for j in top8 if st.session_state.joueurs[j]["Sexe"] == "F"]
    if len(H) < 4 or len(F) < 4:
        st.warning("Il faut au moins 4 hommes ET 4 femmes dans le Top 8.")
        return

    random.shuffle(H)
    random.shuffle(F)
    quarts = []
    for _ in range(4):
        e1 = [H.pop(), F.pop()]
        e2 = [H.pop(), F.pop()]
        quarts.append((e1, e2))
    st.session_state.phases_finales["quarts"] = quarts
    st.session_state.phases_finales["demis"] = []
    st.session_state.phases_finales["finale"] = []
    st.session_state.phases_finales["vainqueur"] = None
    st.success("Quarts générés.")

def _jouer_et_avancer(nom_phase, prochaine_phase, key_prefix):
    gagnants = []
    for idx, (e1, e2) in enumerate(st.session_state.phases_finales[nom_phase], start=1):
        score = st.text_input(
            f"{nom_phase.capitalize()} Match {idx} : {format_team(e1)} vs {format_team(e2)} (ex: 6-4)",
            key=f"{key_prefix}_{nom_phase}_{idx}"
        )
        if score:
            try:
                s1, s2 = map(int, score.split("-"))
                gagnants.append(e1 if s1 > s2 else e2)
            except ValueError:
                st.warning(f"Score invalide pour le match {idx} ({nom_phase}). Format ex: 6-4")

    # Build prochaine phase à partir des gagnants
    st.session_state.phases_finales[prochaine_phase] = []
    for i in range(0, len(gagnants), 2):
        if i+1 < len(gagnants):
            st.session_state.phases_finales[prochaine_phase].append((gagnants[i], gagnants[i+1]))

def reset_phases_finales():
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}

# =========================
#   UI
# =========================
st.title("🎾 Tournoi de Padel - Rétro Padel")

# Générer un round
if st.button("⚡ Générer un nouveau round"):
    generer_round()

# Affichage des rounds & saisie des scores
for r_idx, matchs in enumerate(st.session_state.matchs, start=1):
    st.subheader(f"🏆 Round {r_idx}")
    for m_idx, (e1, e2) in enumerate(matchs, start=1):
        st.markdown(f"**Match {m_idx}** — {format_team(e1)}  vs  {format_team(e2)}")
        key = (r_idx-1, m_idx-1)  # clé: (round_index_zero_based, match_index_zero_based)
        st.session_state.scores[key] = st.text_input(
            f"Score Round {r_idx} Match {m_idx} (ex: 6-3)",
            value=st.session_state.scores.get(key, ""),
            key=f"score_{r_idx}_{m_idx}"
        )

# Calcul classements
if st.button("📊 Calculer le classement"):
    maj_classement_depuis_tous_les_scores()
    afficher_classement()

# Phases finales
st.header("🏆 Phases Finales")

colA, colB = st.columns(2)
with colA:
    if st.button("⚡ Générer les Quarts"):
        generer_quarts()
with colB:
    if st.button("♻️ Reset Phases Finales"):
        reset_phases_finales()
        st.success("Phases finales réinitialisées.")

# Quarts
if st.session_state.phases_finales["quarts"]:
    st.subheader("Quarts de finale")
    for e1, e2 in st.session_state.phases_finales["quarts"]:
        st.write(f"• {format_team(e1)}  vs  {format_team(e2)}")
    _jouer_et_avancer("quarts", "demis", "pf")

# Demis
if st.session_state.phases_finales["demis"]:
    st.subheader("Demi-finales")
    for e1, e2 in st.session_state.phases_finales["demis"]:
        st.write(f"• {format_team(e1)}  vs  {format_team(e2)}")
    _jouer_et_avancer("demis", "finale", "pf")

# Finale
if st.session_state.phases_finales["finale"]:
    st.subheader("Finale")
    for e1, e2 in st.session_state.phases_finales["finale"]:
        st.write(f"• {format_team(e1)}  vs  {format_team(e2)}")

    # Saisie & vainqueur
    gagnants_finale = []
    for idx, (e1, e2) in enumerate(st.session_state.phases_finales["finale"], start=1):
        score = st.text_input(
            f"Finale — Match {idx} : {format_team(e1)} vs {format_team(e2)} (ex: 6-4)",
            key=f"pf_finale_{idx}"
        )
        if score:
            try:
                s1, s2 = map(int, score.split("-"))
                gagnants_finale.append(e1 if s1 > s2 else e2)
            except ValueError:
                st.warning("Score finale invalide (ex: 6-4).")

    if gagnants_finale:
        # Une finale → un vainqueur (équipe)
        st.session_state.phases_finales["vainqueur"] = gagnants_finale[0]

# Vainqueur
if st.session_state.phases_finales.get("vainqueur"):
    e = st.session_state.phases_finales["vainqueur"]
    st.success(f"🏆 Vainqueur : {format_team(e)}")
