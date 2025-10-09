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

# --- Sidebar Paramètres ---
st.sidebar.header("⚙️ Paramètres du tournoi")

hommes_input = st.sidebar.text_area("Liste des hommes (un par ligne)", height=150)
femmes_input = st.sidebar.text_area("Liste des femmes (un par ligne)", height=150)

# Nettoyage des noms
hommes = [h.strip() for h in hommes_input.splitlines() if h.strip()]
femmes = [f.strip() for f in femmes_input.splitlines() if f.strip()]

# Compteurs en temps réel
st.sidebar.markdown("---")
st.sidebar.markdown(f"<h3 style='color: #1f77b4;'>👨 Hommes : {len(hommes)}</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"<h3 style='color: #ff69b4;'>👩 Femmes : {len(femmes)}</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"<h3 style='color: #2ca02c;'>🎯 Total : {len(hommes) + len(femmes)}</h3>", unsafe_allow_html=True)
st.sidebar.markdown("---")

nb_terrains = st.sidebar.number_input("Nombre de terrains disponibles", 1, 10, 2)
max_matchs = st.sidebar.number_input("Nombre maximum de matchs par joueur", 1, 20, 4)

st.sidebar.markdown("---")

if st.sidebar.button("🔄 Reset Tournoi Complet"):
    st.session_state.joueurs = {}
    st.session_state.matchs = []
    st.session_state.scores = {}
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
    st.session_state.classement_calcule = False
    st.rerun()

# --- Initialisation et mise à jour des joueurs ---
nouveaux_joueurs = set(hommes + femmes)
for j in list(st.session_state.joueurs.keys()):
    if j not in nouveaux_joueurs:
        del st.session_state.joueurs[j]

for h in hommes:
    if h not in st.session_state.joueurs:
        st.session_state.joueurs[h] = {"Points": 0.0, "Jeux": 0, "Matchs": 0, "Sexe": "H"}
for f in femmes:
    if f not in st.session_state.joueurs:
        st.session_state.joueurs[f] = {"Points": 0.0, "Jeux": 0, "Matchs": 0, "Sexe": "F"}

# ---------- Compteurs de MATCHS PLANIFIÉS ----------
def scheduled_counts():
    counts = {j: 0 for j in st.session_state.joueurs}
    for rnd in st.session_state.matchs:
        for (e1, e2) in rnd:
            for p in e1 + e2:
                if p in counts:
                    counts[p] += 1
    return counts

# ---------- CLASSEMENT (scores -> stats) ----------
def maj_classement():
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
            except:
                continue

            if s1 > s2:
                gagnants, perdants, js_gagnants, js_perdants = equipe1, equipe2, s1, s2
            else:
                gagnants, perdants, js_gagnants, js_perdants = equipe2, equipe1, s2, s1

            # Gagnants : 3 + 0.1 * jeux gagnés
            for j in gagnants:
                if j in st.session_state.joueurs:
                    st.session_state.joueurs[j]["Points"] += 3.0 + js_gagnants * 0.1
                    st.session_state.joueurs[j]["Jeux"] += js_gagnants
                    st.session_state.joueurs[j]["Matchs"] += 1
            # Perdants : 0.5 fixe
            for j in perdants:
                if j in st.session_state.joueurs:
                    st.session_state.joueurs[j]["Points"] += 0.5
                    st.session_state.joueurs[j]["Jeux"] += js_perdants
                    st.session_state.joueurs[j]["Matchs"] += 1

# ---------- Rounds ----------
def generer_round():
    counts = scheduled_counts()

    eligibles = [j for j in st.session_state.joueurs if counts[j] < max_matchs]
    hommes_dispo = [j for j in eligibles if st.session_state.joueurs[j]["Sexe"] == "H"]
    femmes_dispo = [j for j in eligibles if st.session_state.joueurs[j]["Sexe"] == "F"]

    rnd = random.random
    hommes_dispo.sort(key=lambda x: (counts[x], rnd()))
    femmes_dispo.sort(key=lambda x: (counts[x], rnd()))

    matchs = []
    terrains_possibles = min(nb_terrains, len(hommes_dispo) // 2, len(femmes_dispo) // 2)

    for _ in range(terrains_possibles):
        if len(hommes_dispo) >= 2 and len(femmes_dispo) >= 2:
            h1 = hommes_dispo.pop(0)
            h2 = hommes_dispo.pop(0)
            f1 = femmes_dispo.pop(0)
            f2 = femmes_dispo.pop(0)

            if max(scheduled_counts().get(h1,0),
                   scheduled_counts().get(h2,0),
                   scheduled_counts().get(f1,0),
                   scheduled_counts().get(f2,0)) >= max_matchs:
                continue

            matchs.append(([h1, f1], [h2, f2]))

    if matchs:
        st.session_state.matchs.append(matchs)
        return True, len(matchs)
    return False, 0

def generer_tous_rounds():
    rounds_generes = 0
    while True:
        ok, nbm = generer_round()
        if not ok:
            break
        rounds_generes += 1
        if nbm == 0:
            break
    return rounds_generes

# ---------- Classement / Top 8 ----------
def _df_classement():
    df = pd.DataFrame.from_dict(st.session_state.joueurs, orient="index").reset_index()
    df = df.rename(columns={"index": "Joueur"})
    # ➜ Points à **1 décimale** (demandé)
    df["Points"] = df["Points"].round(1)
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
    st.table(df[["Rang", "Joueur", "Sexe", "Points", "Jeux", "Matchs"]])

def afficher_top8():
    if not st.session_state.joueurs:
        return
    df = _df_classement()
    topH = df[df["Sexe"] == "H"].head(8)[["Joueur", "Points", "Jeux", "Matchs"]].reset_index(drop=True)
    topF = df[df["Sexe"] == "F"].head(8)[["Joueur", "Points", "Jeux", "Matchs"]].reset_index(drop=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🥇 Top 8 Hommes")
        st.dataframe(topH, use_container_width=True)
    with c2:
        st.subheader("🏅 Top 8 Femmes")
        st.dataframe(topF, use_container_width=True)

# ---------- Phases finales ----------
def generer_quarts():
    """8 meilleurs hommes + 8 meilleures femmes, tirage aléatoire H+F vs H+F."""
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

# --- utilitaire : split H/F d’une équipe ---
def split_hf(team):
    h = next(p for p in team if st.session_state.joueurs[p]["Sexe"] == "H")
    f = next(p for p in team if st.session_state.joueurs[p]["Sexe"] == "F")
    return h, f

# ---------------- UI ----------------
st.title("🎾 Tournoi de Padel - Rétro Padel")

# Vérification avant de pouvoir générer un round
if len(hommes) < 2 or len(femmes) < 2:
    st.warning("⚠️ Il faut au moins 2 hommes et 2 femmes pour générer un round")
else:
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
        c1, c2 = st.columns(2)
        with c1:
            if st.button("⚡ Générer 1 round", type="primary", use_container_width=True):
                ok, nbm = generer_round()
                if ok:
                    st.success(f"✅ Round {len(st.session_state.matchs)} généré ({nbm} match(s))")
                    st.rerun()
                else:
                    st.error("❌ Impossible de générer un round")
        with c2:
            if st.button("🚀 Générer TOUS les rounds", type="secondary", use_container_width=True):
                nb = generer_tous_rounds()
                if nb > 0:
                    st.success(f"✅ {nb} round(s) générés automatiquement")
                    st.rerun()
                else:
                    st.warning("⚠️ Aucun round supplémentaire possible")
    else:
        st.info(f"ℹ️ Tous les joueurs éligibles ont atteint le maximum planifié ({max_matchs})")

# Affichage des rounds
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

# Classement + Top 8
if st.session_state.classement_calcule or any(st.session_state.joueurs[j]["Matchs"] > 0 for j in st.session_state.joueurs) or st.session_state.matchs:
    st.header("📊 Classement général")
    maj_classement()
    afficher_classement()
    st.markdown("---")
    afficher_top8()

# --- Phases finales ---
st.markdown("---")
st.header("🏆 Phases Finales")

c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("⚡ Quarts (Top 8)", use_container_width=True):
        if generer_quarts():
            st.success("✅ Quarts générés!")
            st.rerun()
with c2:
    if st.button("🎲 Demis aléatoires", use_container_width=True):
        # option libre (non liée aux quarts)
        tous = list(st.session_state.joueurs.keys())
        H = [j for j in tous if st.session_state.joueurs[j]["Sexe"] == "H"]
        F = [j for j in tous if st.session_state.joueurs[j]["Sexe"] == "F"]
        if len(H) >= 4 and len(F) >= 4:
            random.shuffle(H); random.shuffle(F)
            st.session_state.phases_finales["demis"] = [
                ([H[0], F[0]], [H[1], F[1]]),
                ([H[2], F[2]], [H[3], F[3]]),
            ]
            st.session_state.phases_finales["quarts"] = []
            st.success("✅ Demis générées!")
            st.rerun()
        else:
            st.error("❌ Il faut au moins 4 hommes et 4 femmes")
with c3:
    if st.button("🎲 Finale aléatoire", use_container_width=True):
        tous = list(st.session_state.joueurs.keys())
        H = [j for j in tous if st.session_state.joueurs[j]["Sexe"] == "H"]
        F = [j for j in tous if st.session_state.joueurs[j]["Sexe"] == "F"]
        if len(H) >= 2 and len(F) >= 2:
            random.shuffle(H); random.shuffle(F)
            st.session_state.phases_finales["finale"] = [([H[0], F[0]], [H[1], F[1]])]
            st.session_state.phases_finales["quarts"] = []
            st.session_state.phases_finales["demis"] = []
            st.success("✅ Finale générée!")
            st.rerun()
        else:
            st.error("❌ Il faut au moins 2 hommes et 2 femmes")
with c4:
    if st.button("♻️ Reset Phases", use_container_width=True):
        st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
        st.success("✅ Reset!")
        st.rerun()

# Quarts
if st.session_state.phases_finales["quarts"]:
    st.subheader("⚔️ Quarts de finale")
    gagnants_quarts = []
    for idx, (e1, e2) in enumerate(st.session_state.phases_finales["quarts"]):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.write(f"**Match {idx+1}:** {e1[0]} (H) + {e1[1]} (F)  🆚  {e2[0]} (H) + {e2[1]} (F)")
        with c2:
            sc = st.text_input("Score", key=f"quart_{idx}", label_visibility="collapsed")
            if sc and "-" in sc:
                try:
                    s1, s2 = map(int, sc.split("-"))
                    gagnants_quarts.append(e1 if s1 > s2 else e2)
                except:
                    pass

    # --- DEMIS : recomposition aléatoire (pas les mêmes paires qu'en quarts) ---
    if len(gagnants_quarts) == 4 and st.button("➡️ Valider & Tirage aléatoire des Demi-finales"):
        # Ensemble de TOUTES les équipes ayant existé en quarts (pour les interdire)
        forbidden_teams = set(
            frozenset(tuple(team))
            for (a, b) in st.session_state.phases_finales["quarts"]
            for team in (a, b)
        )
        # Ensemble des affiches de quarts (pour éviter la même confrontation)
        forbidden_matches = set(
            frozenset((tuple(a), tuple(b)))
            for (a, b) in st.session_state.phases_finales["quarts"]
        )

        # On casse les équipes gagnantes -> 4 hommes, 4 femmes
        H = []
        F = []
        for t in gagnants_quarts:
            h, f = split_hf(t)
            H.append(h)
            F.append(f)

        ok = False
        for _ in range(1000):
            random.shuffle(H)
            random.shuffle(F)
            # 4 nouvelles équipes recomposées (H[i] + F[i])
            teams = [[H[0], F[0]], [H[1], F[1]], [H[2], F[2]], [H[3], F[3]]]

            # Aucune équipe ne doit être égale à une équipe vue en quarts
            if any(frozenset(tuple(t)) in forbidden_teams for t in teams):
                continue

            # Tirage aléatoire des affiches (2 demis)
            random.shuffle(teams)
            m1 = frozenset((tuple(teams[0]), tuple(teams[1])))
            m2 = frozenset((tuple(teams[2]), tuple(teams[3])))

            # On refuse les mêmes affiches qu'en quarts
            if m1 in forbidden_matches or m2 in forbidden_matches:
                continue

            st.session_state.phases_finales["demis"] = [(teams[0], teams[1]),
                                                        (teams[2], teams[3])]
            ok = True
            break

        if not ok:
            # En cas d'échec improbable, on fait au moins une recomposition simple
            random.shuffle(H); random.shuffle(F)
            teams = [[H[0], F[0]], [H[1], F[1]], [H[2], F[2]], [H[3], F[3]]]
            random.shuffle(teams)
            st.session_state.phases_finales["demis"] = [(teams[0], teams[1]),
                                                        (teams[2], teams[3])]
        st.rerun()

# Demis
if st.session_state.phases_finales["demis"]:
    st.subheader("⚔️ Demi-finales")
    gagnants_demis = []
    for idx, (e1, e2) in enumerate(st.session_state.phases_finales["demis"]):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.write(f"**Demi-finale {idx+1}:** {e1[0]} (H) + {e1[1]} (F)  🆚  {e2[0]} (H) + {e2[1]} (F)")
        with c2:
            sc = st.text_input("Score", key=f"demi_{idx}", label_visibility="collapsed")
            if sc and "-" in sc:
                try:
                    s1, s2 = map(int, sc.split("-"))
                    gagnants_demis.append(e1 if s1 > s2 else e2)
                except:
                    pass

    if len(gagnants_demis) == 2 and st.button("➡️ Valider & Tirage de la Finale"):
        # Tirage aléatoire entre les deux gagnants des demis (juste l'ordre)
        random.shuffle(gagnants_demis)
        st.session_state.phases_finales["finale"] = [(gagnants_demis[0], gagnants_demis[1])]
        st.rerun()

# Finale
if st.session_state.phases_finales["finale"]:
    st.subheader("🏆 FINALE")
    e1, e2 = st.session_state.phases_finales["finale"][0]
    c1, c2 = st.columns([3, 1])
    with c1:
        st.write(f"**{e1[0]} (H) + {e1[1]} (F)  🆚  {e2[0]} (H) + {e2[1]} (F)**")
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
            except:
                pass

if st.session_state.phases_finales.get("vainqueur"):
    v = st.session_state.phases_finales["vainqueur"]
    st.balloons()
    st.success(f"🎉🏆 **VAINQUEURS DU TOURNOI : {v[0]} et {v[1]} !** 🏆🎉")
