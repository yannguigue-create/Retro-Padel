# -*- coding: utf-8 -*-
import streamlit as st
import random
import pandas as pd

# -----------------------------
# Page / CSS (compact + nom large)
# -----------------------------
st.set_page_config(page_title="🎾 Tournoi de Padel", page_icon="🎾", layout="wide")
st.markdown(
    """
    <style>
      .block-container {padding-top: 0.6rem; padding-bottom: 0.6rem; max-width: 1400px;}
      /* compacter paddings */
      [data-testid="stMetric"], .stButton>button, .stTextInput, .stNumberInput {margin-top: .2rem; margin-bottom: .2rem;}
      .stTable td, .stTable th {padding: .25rem .4rem !important;}
      .stExpander {border: 1px solid #eaeaea !important; margin-bottom: .35rem;}
      /* élargir la colonne Joueur, resserrer les autres via dataframe style */
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# State initial
# -----------------------------
if "joueurs" not in st.session_state:
    st.session_state.joueurs = {}   # {nom: {"Points":0.0,"Jeux":0,"Matchs":0,"Sexe":"H/F"}}
if "matchs" not in st.session_state:
    st.session_state.matchs = []    # liste de rounds ; round = [([H,F],[H,F]), ...]
if "phases_finales" not in st.session_state:
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
if "classement_calcule" not in st.session_state:
    st.session_state.classement_calcule = False

# -----------------------------
# Sidebar (listes joueurs + params)
# -----------------------------
st.sidebar.header("⚙️ Paramètres du tournoi")

hommes_input = st.sidebar.text_area("Liste des hommes (un par ligne)", height=150, key="txt_h")
femmes_input = st.sidebar.text_area("Liste des femmes (un par ligne)", height=150, key="txt_f")

hommes = [h.strip() for h in hommes_input.splitlines() if h.strip()]
femmes = [f.strip() for f in femmes_input.splitlines() if f.strip()]

st.sidebar.markdown("---")
st.sidebar.markdown(f"👨 **Hommes :** {len(hommes)}")
st.sidebar.markdown(f"👩 **Femmes :** {len(femmes)}")
st.sidebar.markdown(f"🎯 **Total :** {len(hommes)+len(femmes)}")
st.sidebar.markdown("---")

nb_terrains = st.sidebar.number_input("Nombre de terrains disponibles", 1, 10, 4)
max_matchs = st.sidebar.number_input("Nombre maximum de matchs par joueur", 1, 20, 4)

if st.sidebar.button("🔄 Reset Tournoi Complet", use_container_width=True):
    st.session_state.joueurs = {}
    st.session_state.matchs = []
    st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
    st.session_state.classement_calcule = False
    st.rerun()

# -----------------------------
# Synchroniser joueurs
# -----------------------------
def sync_joueurs():
    nouveaux = set(hommes + femmes)
    # retire ceux qui ont disparu
    for j in list(st.session_state.joueurs.keys()):
        if j not in nouveaux:
            del st.session_state.joueurs[j]
    # ajoute ceux qui manquent
    for h in hommes:
        if h not in st.session_state.joueurs:
            st.session_state.joueurs[h] = {"Points": 0.0, "Jeux": 0, "Matchs": 0, "Sexe": "H"}
    for f in femmes:
        if f not in st.session_state.joueurs:
            st.session_state.joueurs[f] = {"Points": 0.0, "Jeux": 0, "Matchs": 0, "Sexe": "F"}

sync_joueurs()

# -----------------------------
# Outils planification
# -----------------------------
def scheduled_counts():
    """Nombre de matches planifiés par joueur (tous rounds confondus)."""
    counts = {j: 0 for j in st.session_state.joueurs}
    for rnd in st.session_state.matchs:
        for e1, e2 in rnd:
            for p in e1 + e2:
                if p in counts:
                    counts[p] += 1
    return counts

# -----------------------------
# Classement (lit st.session_state[score_key])
# -----------------------------
def maj_classement():
    # reset
    for j in st.session_state.joueurs:
        st.session_state.joueurs[j]["Points"] = 0.0
        st.session_state.joueurs[j]["Jeux"]   = 0
        st.session_state.joueurs[j]["Matchs"] = 0

    # recalcule pour tout ce qui a un score saisi
    for round_idx, matches in enumerate(st.session_state.matchs, start=1):
        for match_idx, (equipe1, equipe2) in enumerate(matches):
            key = f"score_{round_idx}_{match_idx}"
            raw = (st.session_state.get(key) or "").strip()
            if "-" not in raw:
                continue
            try:
                s1, s2 = map(int, raw.split("-"))
            except Exception:
                continue

            if s1 > s2:
                gagnants, perdants, js_g, js_p = equipe1, equipe2, s1, s2
            else:
                gagnants, perdants, js_g, js_p = equipe2, equipe1, s2, s1

            # barème
            for j in gagnants:
                st.session_state.joueurs[j]["Points"] += 3.0 + js_g * 0.1
                st.session_state.joueurs[j]["Jeux"]   += js_g
                st.session_state.joueurs[j]["Matchs"] += 1
            for j in perdants:
                st.session_state.joueurs[j]["Points"] += 0.5 + js_p * 0.1
                st.session_state.joueurs[j]["Jeux"]   += js_p
                st.session_state.joueurs[j]["Matchs"] += 1

def _df_classement():
    df = pd.DataFrame.from_dict(st.session_state.joueurs, orient="index").reset_index()
    df.rename(columns={"index": "Joueur"}, inplace=True)
    df["Points"] = df["Points"].round(1)
    df["Jeux"]   = df["Jeux"].astype(int)
    df["Matchs"] = df["Matchs"].astype(int)
    df = df.sort_values(by=["Points", "Jeux"], ascending=False).reset_index(drop=True)
    return df

def render_table_compact(df, colonne_joueur_width=210):
    # On stylise pour élargir "Joueur" et resserrer les autres
    cs = {
        "Joueur": f"min-width: {colonne_joueur_width}px; width: {colonne_joueur_width}px;",
        "Sexe": "width: 45px; text-align: center;",
        "Points": "width: 70px; text-align: right;",
        "Jeux": "width: 60px; text-align: right;",
        "Matchs": "width: 60px; text-align: right;",
        "Rang": "width: 50px; text-align: right;",
    }
    styler = df.style.set_table_styles(
        [{"selector": "th", "props": [("text-align", "left")]}]
    ).set_properties(**{
        c: cs.get(c, "width: 80px;") for c in df.columns
    })
    st.table(styler)

def afficher_classement():
    df = _df_classement()
    df.insert(0, "Rang", df.index + 1)
    # une seule décimale visible
    df["Points"] = df["Points"].map(lambda x: f"{x:.1f}")
    render_table_compact(df)

def afficher_top8():
    df = _df_classement()
    topH = df[df["Sexe"] == "H"].head(8)[["Joueur", "Points", "Jeux", "Matchs"]].copy()
    topF = df[df["Sexe"] == "F"].head(8)[["Joueur", "Points", "Jeux", "Matchs"]].copy()
    topH["Points"] = topH["Points"].map(lambda x: f"{x:.1f}")
    topF["Points"] = topF["Points"].map(lambda x: f"{x:.1f}")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🥇 Top 8 Hommes")
        render_table_compact(topH, colonne_joueur_width=200)
    with c2:
        st.subheader("🏅 Top 8 Femmes")
        render_table_compact(topF, colonne_joueur_width=200)

# -----------------------------
# Génération des rounds
# -----------------------------
def generer_round():
    counts = scheduled_counts()
    eligibles = [j for j in st.session_state.joueurs if counts[j] < max_matchs]
    H = [j for j in eligibles if st.session_state.joueurs[j]["Sexe"] == "H"]
    F = [j for j in eligibles if st.session_state.joueurs[j]["Sexe"] == "F"]

    rnd = random.random
    H.sort(key=lambda x: (counts[x], rnd()))
    F.sort(key=lambda x: (counts[x], rnd()))

    matches = []
    terrains = min(nb_terrains, len(H)//2, len(F)//2)
    for _ in range(terrains):
        if len(H) >= 2 and len(F) >= 2:
            h1, h2 = H.pop(0), H.pop(0)
            f1, f2 = F.pop(0), F.pop(0)
            # re-vérification limite
            c = scheduled_counts()
            if max(c.get(h1,0), c.get(h2,0), c.get(f1,0), c.get(f2,0)) >= max_matchs:
                continue
            matches.append(([h1, f1], [h2, f2]))

    if matches:
        st.session_state.matchs.append(matches)
        return True, len(matches)
    return False, 0

def generer_tous_rounds():
    n = 0
    while True:
        ok, nb = generer_round()
        if not ok or nb == 0:
            break
        n += 1
    return n

# -----------------------------
# Phases finales (Top 8 → Quarts/Demis/Finale)
# -----------------------------
def generer_quarts():
    maj_classement()
    df = _df_classement()
    H = df[df["Sexe"] == "H"]["Joueur"].tolist()[:8]
    F = df[df["Sexe"] == "F"]["Joueur"].tolist()[:8]
    if len(H) < 8 or len(F) < 8:
        st.error(f"❌ Il faut au moins 8 hommes et 8 femmes (actuellement {len(H)}H / {len(F)}F)")
        return False
    random.shuffle(H); random.shuffle(F)
    quarts = []
    for i in range(4):
        quarts.append(([H[i], F[i]], [H[i+4], F[i+4]]))
    st.session_state.phases_finales["quarts"] = quarts
    return True

# -----------------------------
# UI
# -----------------------------
st.title("🎾 Tournoi de Padel")

# Info éligibilité
counts_plan = scheduled_counts()
H_elig = sum(1 for j in st.session_state.joueurs if st.session_state.joueurs[j]["Sexe"] == "H" and counts_plan[j] < max_matchs)
F_elig = sum(1 for j in st.session_state.joueurs if st.session_state.joueurs[j]["Sexe"] == "F" and counts_plan[j] < max_matchs)
terrains_theo = min(nb_terrains, H_elig//2, F_elig//2)

if st.session_state.joueurs:
    maj_classement()
    df_now = _df_classement()
    st.info(
        f"📊 Matchs joués : min={df_now['Matchs'].min() if not df_now.empty else 0}, "
        f"max={df_now['Matchs'].max() if not df_now.empty else 0}, limite={max_matchs}"
    )
    st.info(f"🗓️ Éligibles (PLANIFIÉS < {max_matchs}) → Hommes: {H_elig} | Femmes: {F_elig}")

# Boutons génération rounds
cA, cB = st.columns(2)
with cA:
    if terrains_theo > 0 and st.button("⚡ Générer 1 round", use_container_width=True):
        ok, nb = generer_round()
        if ok:
            st.success(f"✅ Round {len(st.session_state.matchs)} généré ({nb} match(s))")
            st.rerun()
        else:
            st.warning("Aucun match supplémentaire possible.")
with cB:
    if terrains_theo > 0 and st.button("🚀 Générer TOUS les rounds", use_container_width=True):
        nb = generer_tous_rounds()
        if nb > 0:
            st.success(f"✅ {nb} round(s) générés")
            st.rerun()
        else:
            st.warning("Aucun round supplémentaire possible.")

# Rounds & scores
if st.session_state.matchs:
    st.header("📋 Matchs du tournoi")
    for r, matches in enumerate(st.session_state.matchs, start=1):
        with st.expander(f"🏆 Round {r} - {len(matches)} match(s)", expanded=(r == len(st.session_state.matchs))):
            for idx, (e1, e2) in enumerate(matches):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.write(f"**Terrain {idx+1}:** {e1[0]} (H) + {e1[1]} (F)  🆚  {e2[0]} (H) + {e2[1]} (F)")
                with c2:
                    key = f"score_{r}_{idx}"
                    # IMPORTANT : on ne copie plus dans un dict : lecture directe dans session_state
                    st.text_input("Score (ex: 6-4)", key=key, label_visibility="collapsed")

    st.markdown("---")
    if st.button("📊 Calculer le classement", use_container_width=True):
        maj_classement()
        st.session_state.classement_calcule = True
        st.rerun()

# Classement + Top 8
if st.session_state.joueurs:
    st.header("📈 Classement général")
    maj_classement()
    afficher_classement()
    st.markdown("---")
    afficher_top8()

# Phases finales
st.markdown("---")
st.header("🏆 Phases Finales")
c1, c2 = st.columns(2)
with c1:
    if st.button("⚡ Quarts (Top 8)", use_container_width=True):
        if generer_quarts():
            st.success("✅ Quarts générés")
            st.rerun()
with c2:
    if st.button("♻️ Reset Phases", use_container_width=True):
        st.session_state.phases_finales = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
        st.success("Réinitialisé")
        st.rerun()

# --- Quarts ---
if st.session_state.phases_finales["quarts"]:
    st.subheader("⚔️ Quarts de finale")
    winners_quarts = []
    for idx, (A, B) in enumerate(st.session_state.phases_finales["quarts"]):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.write(f"**Match {idx+1}:** {A[0]} (H)+{A[1]} (F)  vs  {B[0]} (H)+{B[1]} (F)")
        with c2:
            sc = st.text_input("Score", key=f"quart_{idx}", label_visibility="collapsed")
            if sc and "-" in sc:
                try:
                    s1, s2 = map(int, sc.split("-"))
                    winners_quarts.append(A if s1 > s2 else B)
                except Exception:
                    pass

    if len(winners_quarts) == 4 and st.button("➡️ Valider & Tirage aléatoire des Demi-finales"):
        # recomposition : on sépare les H et les F des vainqueurs
        forbidden_pairs = set((h, f) for h, f in winners_quarts)  # éviter de re-former les mêmes duos
        H = [t[0] for t in winners_quarts]
        F = [t[1] for t in winners_quarts]
        ok = False
        for _ in range(2000):
            random.shuffle(H); random.shuffle(F)
            pairs = list(zip(H, F))
            if all((h, f) not in forbidden_pairs for (h, f) in pairs):
                ok = True
                break
        if not ok:
            pairs = list(zip(H, F))  # fallback
        random.shuffle(pairs)
        st.session_state.phases_finales["demis"] = [
            (list(pairs[0]), list(pairs[1])),
            (list(pairs[2]), list(pairs[3])),
        ]
        st.rerun()

# --- Demis ---
if st.session_state.phases_finales["demis"]:
    st.subheader("⚔️ Demi-finales")
    winners_demis = []
    for idx, (A, B) in enumerate(st.session_state.phases_finales["demis"]):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.write(f"**Demi-finale {idx+1}:** {A[0]} (H)+{A[1]} (F)  vs  {B[0]} (H)+{B[1]} (F)")
        with c2:
            sc = st.text_input("Score", key=f"demi_{idx}", label_visibility="collapsed")
            if sc and "-" in sc:
                try:
                    s1, s2 = map(int, sc.split("-"))
                    winners_demis.append(A if s1 > s2 else B)
                except Exception:
                    pass

    if len(winners_demis) == 2 and st.button("➡️ Valider & Tirage de la Finale"):
        random.shuffle(winners_demis)  # ordre aléatoire
        st.session_state.phases_finales["finale"] = [(winners_demis[0], winners_demis[1])]
        st.rerun()

# --- Finale ---
if st.session_state.phases_finales["finale"]:
    st.subheader("🏆 FINALE")
    A, B = st.session_state.phases_finales["finale"][0]
    c1, c2 = st.columns([3, 1])
    with c1:
        st.write(f"**{A[0]} (H)+{A[1]} (F)  vs  {B[0]} (H)+{B[1]} (F)**")
    with c2:
        sc = st.text_input("Score final", key="finale_score", label_visibility="collapsed")
        if sc and "-" in sc:
            try:
                s1, s2 = map(int, sc.split("-"))
                vainq = A if s1 > s2 else B
                if st.button("🏆 Déclarer le vainqueur"):
                    st.session_state.phases_finales["vainqueur"] = vainq
                    st.session_state.phases_finales["finale"] = []
                    st.rerun()
            except Exception:
                pass

if st.session_state.phases_finales.get("vainqueur"):
    H, F = st.session_state.phases_finales["vainqueur"]
    st.balloons()
    st.success(f"🎉🏆 **Vainqueurs : {H} & {F} !** 🏆🎉")
