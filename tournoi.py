import streamlit as st
import random
import pandas as pd

# =========================
#   INITIALISATION
# =========================
if "joueurs" not in st.session_state:
    st.session_state.joueurs = {}
if "matchs" not in st.session_state:
    st.session_state.matchs = []  # list[round] ; round = list[ ( [H,F], [H,F] ) ]
if "scores" not in st.session_state:
    st.session_state.scores = {}  # "score_{round}_{idx}" -> "6-4"
if "phases_finales" not in st.session_state:
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
if "classement_calcule" not in st.session_state:
    st.session_state.classement_calcule = False

st.set_page_config(page_title="Tournoi de Padel - Rétro Padel", page_icon="🎾", layout="wide")

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

# =========================
#   SYNC LISTES JOUEURS
# =========================
# Supprimer les joueurs non présents
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

# =========================
#   CSS TABLES COMPACTES
# =========================
# (uniquement pour compacter l'affichage ; ne change aucune logique)
st.markdown("""
<style>
.small-table thead th, .small-table tbody td {
    padding: 6px 8px !important;
    font-size: 0.85rem !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
#   OUTILS
# =========================
def scheduled_counts():
    """Nombre de matchs planifiés par joueur (tous rounds confondus)."""
    counts = {j: 0 for j in st.session_state.joueurs}
    for rnd in st.session_state.matchs:
        for (e1, e2) in rnd:
            for p in e1 + e2:
                if p in counts:
                    counts[p] += 1
    return counts

def maj_classement():
    """Recalcule Points/Jeux/Matchs à partir des scores saisis."""
    for j in st.session_state.joueurs:
        st.session_state.joueurs[j]["Points"] = 0.0
        st.session_state.joueurs[j]["Jeux"] = 0
        st.session_state.joueurs[j]["Matchs"] = 0

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

            # Gagnants : 3 pts + 0.1 par jeu gagné
            for j in gagnants:
                if j in st.session_state.joueurs:
                    st.session_state.joueurs[j]["Points"] += 3.0 + js_gagnants * 0.1
                    st.session_state.joueurs[j]["Jeux"] += js_gagnants
                    st.session_state.joueurs[j]["Matchs"] += 1

            # Perdants : 0.5 pt fixe
            for j in perdants:
                if j in st.session_state.joueurs:
                    st.session_state.joueurs[j]["Points"] += 0.5
                    st.session_state.joueurs[j]["Jeux"] += js_perdants
                    st.session_state.joueurs[j]["Matchs"] += 1

def _df_classement():
    """Classement trié (Points -> Jeux), Points affichés à 1 décimale."""
    df = pd.DataFrame.from_dict(st.session_state.joueurs, orient="index").reset_index()
    df = df.rename(columns={"index": "Joueur"})
    df["Points"] = df["Points"].round(1)  # 1 décimale
    df["Jeux"] = df["Jeux"].astype(int)
    df["Matchs"] = df["Matchs"].astype(int)
    df = df.sort_values(by=["Points", "Jeux"], ascending=False).reset_index(drop=True)
    return df

def afficher_classement():
    if not st.session_state.joueurs:
        st.warning("Aucun joueur enregistré")
        return
    df = _df_classement()
    df.insert(0, "Rang", df.index + 1)
    show = df[["Rang", "Joueur", "Sexe", "Points", "Jeux", "Matchs"]].copy()
    # Forcer l'affichage 1 décimale (sans changer le tri)
    show["Points"] = show["Points"].map(lambda x: f"{x:.1f}")
    st.table(show.style.set_table_attributes('class="small-table"'))

def afficher_top8():
    if not st.session_state.joueurs:
        return
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
#   GÉNÉRATION DES ROUNDS
# =========================
def generer_round():
    """Crée un round en respectant nb_terrains et max_matchs (équité par joueurs)."""
    counts = scheduled_counts()
    eligibles = [j for j in st.session_state.joueurs if counts[j] < max_matchs]
    hommes_dispo = [j for j in eligibles if st.session_state.joueurs[j]["Sexe"] == "H"]
    femmes_dispo = [j for j in eligibles if st.session_state.joueurs[j]["Sexe"] == "F"]

    rnd = random.random
    hommes_dispo.sort(key=lambda x: (counts[x], rnd()))  # d'abord ceux qui ont - de matchs
    femmes_dispo.sort(key=lambda x: (counts[x], rnd()))

    matchs = []
    terrains_possibles = min(nb_terrains, len(hommes_dispo) // 2, len(femmes_dispo) // 2)

    for _ in range(terrains_possibles):
        if len(hommes_dispo) >= 2 and len(femmes_dispo) >= 2:
            h1 = hommes_dispo.pop(0)
            h2 = hommes_dispo.pop(0)
            f1 = femmes_dispo.pop(0)
            f2 = femmes_dispo.pop(0)

            # Vérification de dernière minute
            if max(scheduled_counts().get(h1, 0),
                   scheduled_counts().get(h2, 0),
                   scheduled_counts().get(f1, 0),
                   scheduled_counts().get(f2, 0)) >= max_matchs:
                continue

            matchs.append(([h1, f1], [h2, f2]))

    if matchs:
        st.session_state.matchs.append(matchs)
        return True, len(matchs)
    return False, 0

def generer_tous_rounds():
    """Génère jusqu'à ce que plus aucun match possible (respect max_matchs)."""
    rounds_generes = 0
    while True:
        ok, nbm = generer_round()
        if not ok:
            break
        rounds_generes += 1
        if nbm == 0:
            break
    return rounds_generes

# =========================
#   PHASES FINALES
# =========================
def generer_quarts():
    """Top 8 H + Top 8 F, tirage aléatoire H+F vs H+F (4 matchs)."""
    maj_classement()
    df = _df_classement()
    hommes_qualifies = df[df["Sexe"] == "H"]["Joueur"].tolist()[:8]
    femmes_qualifies = df[df["Sexe"] == "F"]["Joueur"].tolist()[:8]

    if len(hommes_qualifies) < 8:
        st.error(f"❌ Il faut au moins 8 hommes qualifiés (actuellement : {len(hommes_qualifies)})")
        return False
    if len(femmes_qualifies) < 8:
        st.error(f"❌ Il faut au moins 8 femmes qualifiées (actuellement : {len(femmes_qualifies)})")
        return False

    random.shuffle(hommes_qualifies)
    random.shuffle(femmes_qualifies)

    quarts = []
    for i in range(4):
        h1, f1 = hommes_qualifies[i], femmes_qualifies[i]
        h2, f2 = hommes_qualifies[i+4], femmes_qualifies[i+4]
        quarts.append(([h1, f1], [h2, f2]))

    st.session_state.phases_finales["quarts"] = quarts
    return True

def split_hf(team):
    """Retourne (H,F) pour une équipe [p1,p2]."""
    h = next(p for p in team if st.session_state.joueurs[p]["Sexe"] == "H")
    f = next(p for p in team if st.session_state.joueurs[p]["Sexe"] == "F")
    return h, f

# =========================
#          UI
# =========================
st.title("🎾 Tournoi de Padel - Rétro Padel")

# -------- Génération rounds --------
if len(hommes) >= 2 and len(femmes) >= 2:
    counts_planifie = scheduled_counts()
    hommes_disponibles = sum(1 for j in st.session_state.joueurs if st.session_state.joueurs[j]["Sexe"] == "H" and counts_planifie[j] < max_matchs)
    femmes_disponibles = sum(1 for j in st.session_state.joueurs if st.session_state.joueurs[j]["Sexe"] == "F" and counts_planifie[j] < max_matchs)
    terrains_theoriques = min(nb_terrains, hommes_disponibles // 2, femmes_disponibles // 2)

    if st.session_state.joueurs:
        maj_classement()
        df_now = _df_classement()
        st.info(
            f"📊 Matchs JOUÉS : min={df_now['Matchs'].min() if not df_now.empty else 0}, "
            f"max={df_now['Matchs'].max() if not df_now.empty else 0}, "
            f"limite={max_matchs}"
        )
        st.info(f"🗓️ Éligibles (PLANIFIÉS < {max_matchs}) → Hommes: {hommes_disponibles}, Femmes: {femmes_disponibles}")

    if terrains_theoriques > 0:
        st.info(f"ℹ️ Prochain round possible : jusqu’à {terrains_theoriques} match(s) (avec {nb_terrains} terrain(s))")
        colA, colB = st.columns(2)
        with colA:
            if st.button("⚡ Générer 1 round", type="primary", use_container_width=True):
                ok, nbm = generer_round()
                if ok:
                    st.success(f"✅ Round {len(st.session_state.matchs)} généré ({nbm} match(s))")
                    st.rerun()
                else:
                    st.error("❌ Impossible de générer un round")
        with colB:
            if st.button("🚀 Générer TOUS les rounds", type="secondary", use_container_width=True):
                nb = generer_tous_rounds()
                if nb > 0:
                    st.success(f"✅ {nb} round(s) générés automatiquement")
                    st.rerun()
                else:
                    st.warning("⚠️ Aucun round supplémentaire possible")
    else:
        st.info(f"ℹ️ Tous les joueurs éligibles ont atteint le maximum planifié ({max_matchs})")
else:
    st.warning("⚠️ Il faut au moins 2 hommes et 2 femmes pour générer un round")

# -------- Affichage rounds + saisie scores --------
if st.session_state.matchs:
    st.markdown("---")
    st.header("📋 Matchs du tournoi")
    for r, matchs in enumerate(st.session_state.matchs, 1):
        with st.expander(f"🏆 Round {r} - {len(matchs)} match(s)", expanded=(r == len(st.session_state.matchs))):
            for idx, (e1, e2) in enumerate(matchs):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.write(f"**Terrain {idx+1}:** {e1[0]} (H) + {e1[1]} (F)  🆚  {e2[0]} (H) + {e2[1]} (F)")
                with c2:
                    key = f"score_{r}_{idx}"
                    val = st.text_input("Score (ex: 6-4)", key=key, label_visibility="collapsed")
                    if val:
                        st.session_state.scores[key] = val

    st.markdown("---")
    if st.button("📊 Calculer le classement", type="primary"):
        maj_classement()
        st.session_state.classement_calcule = True
        st.rerun()

# -------- Classement + Top8 permanents --------
if st.session_state.classement_calcule or any(st.session_state.joueurs[j]["Matchs"] > 0 for j in st.session_state.joueurs) or st.session_state.matchs:
    st.header("📈 Classement général")
    maj_classement()
    afficher_classement()
    st.markdown("---")
    afficher_top8()

# -------- Phases finales --------
st.markdown("---")
st.header("🏆 Phases Finales")

colQ, colR = st.columns(2)
with colQ:
    if st.button("⚡ Quarts (Top 8 H & F) – Tirage aléatoire", use_container_width=True):
        if generer_quarts():
            st.success("✅ Quarts générés !")
            st.rerun()
with colR:
    if st.button("♻️ Reset Phases", use_container_width=True):
        st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
        st.success("✅ Reset Phases !")
        st.rerun()

# --- QUARTS ---
if st.session_state.phases_finales["quarts"]:
    st.subheader("🗡️ Quarts de finale")
    gagnants_quarts = []
    for idx, (e1, e2) in enumerate(st.session_state.phases_finales["quarts"]):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.write(f"**Quart {idx+1}:** {e1[0]} (H)+{e1[1]} (F)  vs  {e2[0]} (H)+{e2[1]} (F)")
        with c2:
            sc = st.text_input("Score", key=f"quart_{idx}", label_visibility="collapsed")
            if sc and "-" in sc:
                try:
                    s1, s2 = map(int, sc.split("-"))
                    gagnants_quarts.append(e1 if s1 > s2 else e2)
                except Exception:
                    pass

    # --- DEMIS : recomposition aléatoire en évitant mêmes paires et mêmes affiches qu'en quarts ---
    if len(gagnants_quarts) == 4 and st.button("✅ Valider & Tirage aléatoire des Demi-finales"):
        # équipes et affiches interdites (issues des quarts)
        forbidden_teams = set(
            frozenset(tuple(team))
            for (a, b) in st.session_state.phases_finales["quarts"]
            for team in (a, b)
        )
        forbidden_matches = set(
            frozenset((tuple(a), tuple(b)))
            for (a, b) in st.session_state.phases_finales["quarts"]
        )
        # casser les paires gagnantes -> listes H & F
        H, F = [], []
        for team in gagnants_quarts:
            h = next(p for p in team if st.session_state.joueurs[p]["Sexe"] == "H")
            f = next(p for p in team if st.session_state.joueurs[p]["Sexe"] == "F")
            H.append(h); F.append(f)

        ok = False
        for _ in range(1000):
            random.shuffle(H); random.shuffle(F)
            teams = [[H[0], F[0]], [H[1], F[1]], [H[2], F[2]], [H[3], F[3]]]
            # pas de réutilisation d'une équipe déjà vue en quarts
            if any(frozenset(tuple(t)) in forbidden_teams for t in teams):
                continue
            # tirage des affiches de demis
            random.shuffle(teams)
            m1 = frozenset((tuple(teams[0]), tuple(teams[1])))
            m2 = frozenset((tuple(teams[2]), tuple(teams[3])))
            # éviter une affiche identique à un quart
            if m1 in forbidden_matches or m2 in forbidden_matches:
                continue
            st.session_state.phases_finales["demis"] = [(teams[0], teams[1]), (teams[2], teams[3])]
            ok = True
            break

        if not ok:
            # cas très improbable : on accepte la recompo même si une contrainte n'a pas pu être satisfaite
            random.shuffle(H); random.shuffle(F)
            teams = [[H[0], F[0]], [H[1], F[1]], [H[2], F[2]], [H[3], F[3]]]
            random.shuffle(teams)
            st.session_state.phases_finales["demis"] = [(teams[0], teams[1]), (teams[2], teams[3])]
        st.rerun()

# --- DEMIS ---
if st.session_state.phases_finales["demis"]:
    st.subheader("⚔️ Demi-finales")
    gagnants_demis = []
    for idx, (e1, e2) in enumerate(st.session_state.phases_finales["demis"]):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.write(f"**Demi-finale {idx+1}:** {e1[0]} (H)+{e1[1]} (F)  vs  {e2[0]} (H)+{e2[1]} (F)")
        with c2:
            sc = st.text_input("Score", key=f"demi_{idx}", label_visibility="collapsed")
            if sc and "-" in sc:
                try:
                    s1, s2 = map(int, sc.split("-"))
                    gagnants_demis.append(e1 if s1 > s2 else e2)
                except Exception:
                    pass

    if len(gagnants_demis) == 2 and st.button("✅ Valider & Tirage de la Finale"):
        random.shuffle(gagnants_demis)  # ordre aléatoire (pas de recomposition en finale)
        st.session_state.phases_finales["finale"] = [(gagnants_demis[0], gagnants_demis[1])]
        st.rerun()

# --- FINALE ---
if st.session_state.phases_finales["finale"]:
    st.subheader("🏆 FINALE")
    e1, e2 = st.session_state.phases_finales["finale"][0]
    c1, c2 = st.columns([3, 1])
    with c1:
        st.write(f"**{e1[0]} (H)+{e1[1]} (F)  vs  {e2[0]} (H)+{e2[1]} (F)**")
    with c2:
        sc = st.text_input("Score final", key="finale_score", label_visibility="collapsed")
        if sc and "-" in sc:
            try:
                s1, s2 = map(int, sc.split("-"))
                vainq = e1 if s1 > s2 else e2
                if st.button("🏆 Déclarer le vainqueur"):
                    st.session_state.phases_finales["vainqueur"] = vainq
                    st.session_state.phases_finales["finale"] = []
                    st.rerun()
            except Exception:
                pass

if st.session_state.phases_finales.get("vainqueur"):
    v = st.session_state.phases_finales["vainqueur"]
    st.balloons()
    st.success(f"🎉🏆 **VAINQUEURS DU TOURNOI : {v[0]} et {v[1]} !** 🏆🎉")
