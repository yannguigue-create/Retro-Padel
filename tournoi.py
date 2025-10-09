# -*- coding: utf-8 -*-
import streamlit as st
import random
import pandas as pd

# =========================
#   INITIALISATION
# =========================
st.set_page_config(page_title="🎾 Tournoi de Padel", page_icon="🎾", layout="wide")

# ---- COMPACT UI (présentation uniquement) ----
COMPACT_CSS = """
<style>
/* Conteneur principal : largeur bornée + paddings réduits */
[data-testid="stAppViewContainer"] .main{
  max-width: 1050px;       /* ← régle ici (ex: 1000 / 900) si tu veux encore plus étroit */
  padding-left: 1rem;
  padding-right: 1rem;
  padding-top: 0.5rem;
  margin: 0 auto;
}
div.block-container{
  padding-top: 0.4rem;
  padding-bottom: 0.4rem;
}

/* Titres et marges plus serrés */
h1,h2,h3,h4{ margin: 0.5rem 0 0.35rem 0; }

/* Espacement vertical global plus compact */
section.main .element-container{ margin-bottom: 0.45rem; }

/* Expandeurs (Rounds) : en-tête et contenu plus denses */
div[data-testid="stExpander"] details summary{
  padding: 0.22rem 0.5rem !important;
  font-size: 0.95rem !important;
  line-height: 1.15 !important;
}
div[data-testid="stExpander"] div[role="region"]{
  padding: 0.4rem 0.6rem !important;
}

/* Colonnes Score (text input à droite) : largeur et hauteur réduites */
div[data-testid="stTextInput"]{ max-width: 120px; }
div[data-testid="stTextInput"] input{
  padding: 0.25rem 0.45rem !important;
  min-height: 1.8rem !important;
  font-size: 0.92rem !important;
}

/* Boutons compacts */
.stButton>button{
  padding: 0.28rem 0.6rem !important;
  font-size: 0.92rem !important;
}

/* Tables plus denses */
div[data-testid="stTable"] table{ font-size: 0.92rem !important; }
div[data-testid="stTable"] th, 
div[data-testid="stTable"] td{
  padding: 0.16rem 0.42rem !important;
  white-space: nowrap;      /* évite d’élargir les colonnes */
}

/* Légère réduction des champs number en sidebar */
div[data-testid="stNumberInput"] input{
  padding: 0.2rem 0.4rem !important;
  min-height: 1.8rem !important;
  font-size: 0.92rem !important;
}
</style>
"""
st.markdown(COMPACT_CSS, unsafe_allow_html=True)
# ---- FIN COMPACT UI ----

if "joueurs" not in st.session_state:
    st.session_state.joueurs = {}
if "matchs" not in st.session_state:
    st.session_state.matchs = []
if "scores" not in st.session_state:
    st.session_state.scores = {}
if "phases_finales" not in st.session_state:
    st.session_state.phases_finales = {
        "quarts": [],
        "demis": [],
        "finale": [],
        "vainqueur": None
    }
if "classement_calcule" not in st.session_state:
    st.session_state.classement_calcule = False

# =========================
#   PARAMÈTRES SIDEBAR
# =========================
st.sidebar.header("⚙️ Paramètres du tournoi")

hommes_input = st.sidebar.text_area("Liste des hommes (un par ligne)", height=150)
femmes_input = st.sidebar.text_area("Liste des femmes (un par ligne)", height=150)

hommes = [h.strip() for h in hommes_input.splitlines() if h.strip()]
femmes = [f.strip() for f in femmes_input.splitlines() if f.strip()]

st.sidebar.markdown("---")
st.sidebar.markdown(f"👨 **Hommes :** {len(hommes)}")
st.sidebar.markdown(f"👩 **Femmes :** {len(femmes)}")
st.sidebar.markdown(f"🎯 **Total :** {len(hommes) + len(femmes)}")
st.sidebar.markdown("---")

nb_terrains = st.sidebar.number_input("Nombre de terrains disponibles", 1, 10, 4)
max_matchs = st.sidebar.number_input("Nombre maximum de matchs par joueur", 1, 20, 4)

if st.sidebar.button("🔄 Reset Tournoi Complet"):
    st.session_state.joueurs = {}
    st.session_state.matchs = []
    st.session_state.scores = {}
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
    st.session_state.classement_calcule = False
    st.rerun()

# =========================
#   SYNCHRONISATION JOUEURS
# =========================
def sync_joueurs():
    nouveaux = set(hommes + femmes)
    # remove old
    for j in list(st.session_state.joueurs.keys()):
        if j not in nouveaux:
            del st.session_state.joueurs[j]
    # add new
    for h in hommes:
        if h not in st.session_state.joueurs:
            st.session_state.joueurs[h] = {"Points": 0.0, "Jeux": 0, "Matchs": 0, "Sexe": "H"}
    for f in femmes:
        if f not in st.session_state.joueurs:
            st.session_state.joueurs[f] = {"Points": 0.0, "Jeux": 0, "Matchs": 0, "Sexe": "F"}

sync_joueurs()

# =========================
#   OUTILS
# =========================
def scheduled_counts():
    """Nombre de matchs PLANIFIÉS par joueur (tous rounds confondus)."""
    counts = {j: 0 for j in st.session_state.joueurs}
    for rnd in st.session_state.matchs:
        for (e1, e2) in rnd:
            for p in e1 + e2:
                if p in counts:
                    counts[p] += 1
    return counts

# =========================
#   CLASSEMENT
# =========================
def maj_classement():
    """Recalcule Points / Jeux / Matchs à partir des scores saisis."""
    for j in st.session_state.joueurs:
        st.session_state.joueurs[j]["Points"] = 0.0
        st.session_state.joueurs[j]["Jeux"] = 0
        st.session_state.joueurs[j]["Matchs"] = 0

    for round_idx, matchs in enumerate(st.session_state.matchs):
        for match_idx, (e1, e2) in enumerate(matchs):
            key = f"score_{round_idx+1}_{match_idx}"
            sc = st.session_state.scores.get(key, "")
            if not sc or "-" not in sc:
                continue
            try:
                s1, s2 = map(int, sc.split("-"))
            except:
                continue
            if s1 > s2:
                gagnants, perdants, js_g, js_p = e1, e2, s1, s2
            else:
                gagnants, perdants, js_g, js_p = e2, e1, s2, s1

            # gagnant : 3 + 0.1 par jeu ; perdant : 0.5 fixe
            for j in gagnants:
                st.session_state.joueurs[j]["Points"] += 3.0 + js_g * 0.1
                st.session_state.joueurs[j]["Jeux"] += js_g
                st.session_state.joueurs[j]["Matchs"] += 1
            for j in perdants:
                st.session_state.joueurs[j]["Points"] += 0.5
                st.session_state.joueurs[j]["Jeux"] += js_p
                st.session_state.joueurs[j]["Matchs"] += 1

def _df_classement():
    """DataFrame classement (Points arrondis à 1 décimale)."""
    df = pd.DataFrame.from_dict(st.session_state.joueurs, orient="index").reset_index()
    df.rename(columns={"index": "Joueur"}, inplace=True)
    df["Points"] = df["Points"].round(1)   # <-- 1 seule décimale
    df["Jeux"] = df["Jeux"].astype(int)
    df["Matchs"] = df["Matchs"].astype(int)
    df = df.sort_values(by=["Points", "Jeux"], ascending=False).reset_index(drop=True)
    return df

def _df_display_one_decimal(df):
    """Force l’affichage des Points à 1 décimale (chaîne)."""
    df = df.copy()
    df["Points"] = df["Points"].map(lambda x: f"{x:.1f}")
    return df

def afficher_classement():
    df = _df_classement()
    df.insert(0, "Rang", df.index + 1)
    df = _df_display_one_decimal(df)
    st.table(df[["Rang", "Joueur", "Sexe", "Points", "Jeux", "Matchs"]])

def afficher_top8():
    df = _df_classement()
    topH = df[df["Sexe"] == "H"].head(8)[["Joueur", "Points", "Jeux", "Matchs"]]
    topF = df[df["Sexe"] == "F"].head(8)[["Joueur", "Points", "Jeux", "Matchs"]]
    topH = _df_display_one_decimal(topH)
    topF = _df_display_one_decimal(topF)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🥇 Top 8 Hommes")
        st.table(topH)
    with c2:
        st.subheader("🏅 Top 8 Femmes")
        st.table(topF)

# =========================
#   ROUNDS (génération)
# =========================
def generer_round():
    counts = scheduled_counts()
    eligibles = [j for j in st.session_state.joueurs if counts[j] < max_matchs]
    H = [j for j in eligibles if st.session_state.joueurs[j]["Sexe"] == "H"]
    F = [j for j in eligibles if st.session_state.joueurs[j]["Sexe"] == "F"]

    rnd = random.random
    H.sort(key=lambda x: (counts[x], rnd()))
    F.sort(key=lambda x: (counts[x], rnd()))

    matchs = []
    terrains = min(nb_terrains, len(H)//2, len(F)//2)

    for _ in range(terrains):
        if len(H) >= 2 and len(F) >= 2:
            h1, h2 = H.pop(0), H.pop(0)
            f1, f2 = F.pop(0), F.pop(0)
            # re-vérif limite
            c = scheduled_counts()
            if max(c.get(h1,0), c.get(h2,0), c.get(f1,0), c.get(f2,0)) >= max_matchs:
                continue
            matchs.append(([h1, f1], [h2, f2]))

    if matchs:
        st.session_state.matchs.append(matchs)
        return True, len(matchs)
    return False, 0

def generer_tous_rounds():
    n = 0
    while True:
        ok, nb = generer_round()
        if not ok or nb == 0:
            break
        n += 1
    return n

# =========================
#   PHASES FINALES
# =========================
def generer_quarts():
    """8 meilleurs H + 8 meilleures F, tirage aléatoire H+F vs H+F."""
    maj_classement()
    df = _df_classement()
    H = df[df["Sexe"] == "H"]["Joueur"].tolist()[:8]
    F = df[df["Sexe"] == "F"]["Joueur"].tolist()[:8]
    if len(H) < 8 or len(F) < 8:
        st.error(f"❌ Il faut au moins 8 hommes et 8 femmes (actuellement {len(H)}H / {len(F)}F).")
        return False
    random.shuffle(H); random.shuffle(F)
    quarts = []
    for i in range(4):
        quarts.append(([H[i], F[i]], [H[i+4], F[i+4]]))
    st.session_state.phases_finales["quarts"] = quarts
    return True

def _pairs_from_quarts(quarts):
    winners_H, winners_F = [], []
    forbidden_pairs = set()
    for (e1, e2) in quarts:
        sc_key = f"quart_score_{len(forbidden_pairs)}"
    return winners_H, winners_F, forbidden_pairs

def _tirage_semis_recompose(winners_teams, quarts):
    forbidden = set()
    for (h, f) in winners_teams:
        forbidden.add((h, f))
    H = [team[0] for team in winners_teams]
    F = [team[1] for team in winners_teams]
    for _ in range(2000):
        random.shuffle(H)
        random.shuffle(F)
        pairs = list(zip(H, F))
        if all((h, f) not in forbidden for (h, f) in pairs):
            random.shuffle(pairs)
            return [(pairs[0], pairs[1]), (pairs[2], pairs[3])]
    random.shuffle(H); random.shuffle(F)
    pairs = list(zip(H, F))
    random.shuffle(pairs)
    return [(pairs[0], pairs[1]), (pairs[2], pairs[3])]

# =========================
#   UI
# =========================
st.title("🎾 Tournoi de Padel - Rétro Padel")

# --- génération rounds ---
counts_plan = scheduled_counts()
H_elig = sum(1 for j in st.session_state.joueurs if st.session_state.joueurs[j]["Sexe"] == "H" and counts_plan[j] < max_matchs)
F_elig = sum(1 for j in st.session_state.joueurs if st.session_state.joueurs[j]["Sexe"] == "F" and counts_plan[j] < max_matchs)
terrains_theo = min(nb_terrains, H_elig//2, F_elig//2)

if st.session_state.joueurs:
    maj_classement()
    df_now = _df_classement()
    st.info(f"📊 Matchs joués: min={df_now['Matchs'].min() if not df_now.empty else 0}, "
            f"max={df_now['Matchs'].max() if not df_now.empty else 0}, limite={max_matchs}")
    st.info(f"🗓️ Éligibles (PLANIFIÉS < {max_matchs}) → Hommes: {H_elig}, Femmes: {F_elig}")

if terrains_theo > 0:
    colA, colB = st.columns(2)
    with colA:
        if st.button("⚡ Générer 1 round", use_container_width=True):
            ok, nb = generer_round()
            if ok:
                st.success(f"✅ Round {len(st.session_state.matchs)} généré ({nb} match(s))")
                st.rerun()
            else:
                st.error("❌ Impossible de générer un round")
    with colB:
        if st.button("🚀 Générer TOUS les rounds", use_container_width=True):
            nb = generer_tous_rounds()
            if nb > 0:
                st.success(f"✅ {nb} round(s) générés")
                st.rerun()
            else:
                st.warning("⚠️ Aucun round supplémentaire possible")

# --- rounds & saisie scores ---
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
    if st.button("📊 Calculer le classement"):
        maj_classement()
        st.session_state.classement_calcule = True
        st.rerun()

# --- Classement + Top 8 ---
if st.session_state.joueurs:
    st.header("📈 Classement général")
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
            st.success("✅ Quarts générés")
            st.rerun()
with c2:
    if st.button("♻️ Reset Phases", use_container_width=True):
        st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
        st.success("✅ Phases finales réinitialisées")
        st.rerun()

# --- Quarts ---
if st.session_state.phases_finales["quarts"]:
    st.subheader("⚔️ Quarts de finale")
    gagnants_quarts = []
    for idx, (e1, e2) in enumerate(st.session_state.phases_finales["quarts"]):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.write(f"**Match {idx+1}:** {e1[0]} (H)+{e1[1]} (F)  vs  {e2[0]} (H)+{e2[1]} (F)")
        with c2:
            sc = st.text_input("Score", key=f"quart_{idx}", label_visibility="collapsed")
            if sc and "-" in sc:
                try:
                    s1, s2 = map(int, sc.split("-"))
                    gagnants_quarts.append(e1 if s1 > s2 else e2)
                except:
                    pass

    if len(gagnants_quarts) == 4 and st.button("➡️ Valider & Tirage aléatoire des Demi-finales"):
        forbidden = set((team[0], team[1]) for team in gagnants_quarts)
        H = [t[0] for t in gagnants_quarts]
        F = [t[1] for t in gagnants_quarts]
        ok = False
        for _ in range(2000):
            random.shuffle(H)
            random.shuffle(F)
            new_pairs = list(zip(H, F))
            if all((h, f) not in forbidden for (h, f) in new_pairs):
                ok = True
                break
        if not ok:
            new_pairs = list(zip(H, F))
        random.shuffle(new_pairs)
        st.session_state.phases_finales["demis"] = [
            (list(new_pairs[0]), list(new_pairs[1])),
            (list(new_pairs[2]), list(new_pairs[3])),
        ]
        st.rerun()

# --- Demis ---
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
                except:
                    pass

    if len(gagnants_demis) == 2 and st.button("➡️ Valider & Tirage de la Finale"):
        random.shuffle(gagnants_demis)
        st.session_state.phases_finales["finale"] = [(gagnants_demis[0], gagnants_demis[1])]
        st.rerun()

# --- Finale ---
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
            except:
                pass

if st.session_state.phases_finales.get("vainqueur"):
    v = st.session_state.phases_finales["vainqueur"]
    st.balloons()
    st.success(f"🎉🏆 **VAINQUEURS DU TOURNOI : {v[0]} et {v[1]} !** 🏆🎉")
