# -*- coding: utf-8 -*-
import streamlit as st
import random
import pandas as pd

# =========================
#   PAGE + CSS (compact)
# =========================
st.set_page_config(page_title="🎾 Tournoi de Padel", page_icon="🎾", layout="wide")
st.markdown(
    """
    <style>
      .block-container {padding-top: .6rem; padding-bottom: .6rem; max-width: 1400px;}
      .stTable td, .stTable th {padding: .25rem .40rem !important; font-size: 0.92rem;}
      .stExpander {border: 1px solid #eaeaea !important; margin-bottom: .35rem;}
      table {table-layout: auto;} /* élargit la colonne Joueur automatiquement */
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
#   STATE
# =========================
def init_state():
    if "joueurs" not in st.session_state:
        st.session_state.joueurs = {}  # {nom: {"Points":0.0, "Jeux":0, "Matchs":0, "Sexe":"H/F"}}
    if "matchs" not in st.session_state:
        st.session_state.matchs = []   # rounds libres: [ [([H,F],[H,F]), ...], ... ]
    # Phases finales pour le mode Rounds libres
    if "finals" not in st.session_state:
        st.session_state.finals = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
    # Poules auto + tableaux
    if "poules" not in st.session_state:
        st.session_state.poules = {
            "params": {"nb_poules": 2, "teams_per_pool": 4},
            "teams": [],
            "pools": [],
            "main_bracket": [],
            "cons_bracket": [],
        }
    # Poules manuelles + tableaux
    if "poules_manual" not in st.session_state:
        st.session_state.poules_manual = {
            "params": {"nb_poules": 2, "teams_per_pool": 4},
            "selections": {},     # clés "pm_{p}_{s}_H"/"pm_{p}_{s}_F" pour les selectboxes
            "teams": [],          # liste de paires [(H,F), ...]
            "pools": [],          # [{"teams":[ids], "matches":[(i,j),...]}, ...]
            "main_bracket": [],
            "cons_bracket": [],
        }
    if "mode" not in st.session_state:
        st.session_state.mode = "Rounds libres"

init_state()

# =========================
#   SIDEBAR
# =========================
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

mode = st.sidebar.radio(
    "Mode du tournoi",
    ["Rounds libres", "Poules + Élimination", "Poules (manuelles)"],
    index=["Rounds libres", "Poules + Élimination", "Poules (manuelles)"].index(st.session_state.mode)
)
st.session_state.mode = mode

nb_terrains = st.sidebar.number_input("Nombre de terrains disponibles", 1, 10, 4)
max_matchs = st.sidebar.number_input("Nombre maximum de matchs par joueur (Rounds libres)", 1, 20, 4)

if st.sidebar.button("🔄 Reset Tournoi Complet", use_container_width=True):
    st.session_state.clear()
    init_state()
    st.rerun()

# =========================
#   SYNC JOUEURS
# =========================
def sync_joueurs():
    nouveaux = set(hommes + femmes)
    for j in list(st.session_state.joueurs.keys()):
        if j not in nouveaux:
            del st.session_state.joueurs[j]
    for h in hommes:
        if h not in st.session_state.joueurs:
            st.session_state.joueurs[h] = {"Points":0.0,"Jeux":0,"Matchs":0,"Sexe":"H"}
    for f in femmes:
        if f not in st.session_state.joueurs:
            st.session_state.joueurs[f] = {"Points":0.0,"Jeux":0,"Matchs":0,"Sexe":"F"}

sync_joueurs()

# =========================
#   OUTILS
# =========================
def render_table_compact(df):
    """Affiche table compacte, 1 décimale pour Points si présent."""
    if "Points" in df.columns and len(df) > 0:
        df = df.copy()
        df["Points"] = df["Points"].map(lambda x: f"{float(x):.1f}")
    st.table(df)

def add_points(players, s_g, s_p, gagnants, perdants):
    """Barème : Gagnant 3 + 0.1*jeux ; Perdant 0.5 + 0.1*jeux (MAJ jeux/matchs)."""
    for p in gagnants:
        players[p]["Points"] += 3.0 + s_g * 0.1
        players[p]["Jeux"]   += s_g
        players[p]["Matchs"] += 1
    for p in perdants:
        players[p]["Points"] += 0.5 + s_p * 0.1
        players[p]["Jeux"]   += s_p
        players[p]["Matchs"] += 1

def parse_score(s):
    try:
        a,b = map(int, s.strip().split("-"))
        return a,b
    except Exception:
        return None

# =========================
#   CLASSEMENT GLOBAL
# =========================
def maj_classement_global():
    # reset
    for j in st.session_state.joueurs:
        st.session_state.joueurs[j]["Points"] = 0.0
        st.session_state.joueurs[j]["Jeux"]   = 0
        st.session_state.joueurs[j]["Matchs"] = 0

    # 1) Rounds libres
    for r, matches in enumerate(st.session_state.matchs, start=1):
        for m_idx, (e1, e2) in enumerate(matches):
            raw = (st.session_state.get(f"score_{r}_{m_idx}") or "").strip()
            sc = parse_score(raw)
            if not sc: continue
            s1, s2 = sc
            if s1 > s2:
                add_points(st.session_state.joueurs, s1, s2, e1, e2)
            else:
                add_points(st.session_state.joueurs, s2, s1, e2, e1)

    # 2) Phases finales (Rounds libres)
    finals = st.session_state.finals
    for idx, (A,B) in enumerate(finals.get("quarts", [])):
        raw = (st.session_state.get(f"rl_quart_{idx}") or "").strip()
        sc = parse_score(raw)
        if not sc: continue
        s1, s2 = sc
        if s1 > s2: add_points(st.session_state.joueurs, s1, s2, A, B)
        else:      add_points(st.session_state.joueurs, s2, s1, B, A)

    for idx, (A,B) in enumerate(finals.get("demis", [])):
        raw = (st.session_state.get(f"rl_demi_{idx}") or "").strip()
        sc = parse_score(raw)
        if not sc: continue
        s1, s2 = sc
        if s1 > s2: add_points(st.session_state.joueurs, s1, s2, A, B)
        else:      add_points(st.session_state.joueurs, s2, s1, B, A)

    for idx, (A,B) in enumerate(finals.get("finale", [])):
        raw = (st.session_state.get("rl_finale") or "").strip()
        sc = parse_score(raw)
        if not sc: continue
        s1, s2 = sc
        if s1 > s2: add_points(st.session_state.joueurs, s1, s2, A, B)
        else:      add_points(st.session_state.joueurs, s2, s1, B, A)

    # 3) Poules auto (+ tableaux)
    pools = st.session_state.poules.get("pools", [])
    teams = st.session_state.poules.get("teams", [])
    for p_idx, pool in enumerate(pools):
        for m_idx, (ti,tj) in enumerate(pool.get("matches", [])):
            raw = (st.session_state.get(f"pool_{p_idx}_m_{m_idx}") or "").strip()
            sc = parse_score(raw)
            if not sc: continue
            s1, s2 = sc
            e1, e2 = teams[ti], teams[tj]
            if s1 > s2: add_points(st.session_state.joueurs, s1, s2, e1, e2)
            else:      add_points(st.session_state.joueurs, s2, s1, e2, e1)

    for name in ("main_bracket", "cons_bracket"):
        bracket = st.session_state.poules.get(name, [])
        for r_idx, rnd in enumerate(bracket, start=1):
            for m_idx, (A,B) in enumerate(rnd):
                raw = (st.session_state.get(f"{name}_r{r_idx}_m{m_idx}") or "").strip()
                sc = parse_score(raw)
                if not sc: continue
                s1, s2 = sc
                if s1 > s2: add_points(st.session_state.joueurs, s1, s2, A, B)
                else:      add_points(st.session_state.joueurs, s2, s1, B, A)

    # 4) Poules manuelles (+ tableaux)
    mpools = st.session_state.poules_manual.get("pools", [])
    mteams = st.session_state.poules_manual.get("teams", [])
    for p_idx, pool in enumerate(mpools):
        for m_idx, (ti,tj) in enumerate(pool.get("matches", [])):
            raw = (st.session_state.get(f"mpool_{p_idx}_m_{m_idx}") or "").strip()
            sc = parse_score(raw)
            if not sc: continue
            s1, s2 = sc
            e1, e2 = mteams[ti], mteams[tj]
            if s1 > s2: add_points(st.session_state.joueurs, s1, s2, e1, e2)
            else:      add_points(st.session_state.joueurs, s2, s1, e2, e1)

    for name in ("manual_main_bracket", "manual_cons_bracket"):
        bracket = st.session_state.poules_manual.get(name, [])
        for r_idx, rnd in enumerate(bracket, start=1):
            for m_idx, (A,B) in enumerate(rnd):
                raw = (st.session_state.get(f"{name}_r{r_idx}_m{m_idx}") or "").strip()
                sc = parse_score(raw)
                if not sc: continue
                s1, s2 = sc
                if s1 > s2: add_points(st.session_state.joueurs, s1, s2, A, B)
                else:      add_points(st.session_state.joueurs, s2, s1, B, A)

def df_classement():
    """Classement robuste même si 0 joueur."""
    if not st.session_state.joueurs:
        return pd.DataFrame(columns=["Joueur","Sexe","Points","Jeux","Matchs"])
    df = pd.DataFrame.from_dict(st.session_state.joueurs, orient="index").reset_index()
    df.rename(columns={"index":"Joueur"}, inplace=True)
    for c,typ in (("Points", float), ("Jeux", int), ("Matchs", int), ("Sexe", str)):
        if c not in df.columns:
            df[c] = 0.0 if typ is float else ("" if typ is str else 0)
        df[c] = df[c].astype(typ) if typ is not str else df[c].astype(str)
    df["Points"] = df["Points"].round(1)
    df = df.sort_values(by=["Points","Jeux"], ascending=False).reset_index(drop=True)
    return df

def top8_tables(df):
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🥇 Top 8 Hommes")
        topH = df[df["Sexe"]=="H"].head(8)[["Joueur","Points","Jeux","Matchs"]].reset_index(drop=True)
        render_table_compact(topH)
    with c2:
        st.subheader("🏅 Top 8 Femmes")
        topF = df[df["Sexe"]=="F"].head(8)[["Joueur","Points","Jeux","Matchs"]].reset_index(drop=True)
        render_table_compact(topF)

# =========================
#   ROUNDS LIBRES
# =========================
def scheduled_counts_rounds():
    counts = {j: 0 for j in st.session_state.joueurs}
    for rnd in st.session_state.matchs:
        for e1,e2 in rnd:
            for p in e1+e2:
                if p in counts:
                    counts[p] += 1
    return counts

def generer_round():
    counts = scheduled_counts_rounds()
    eligibles = [j for j in st.session_state.joueurs if counts[j] < max_matchs]
    H = [j for j in eligibles if st.session_state.joueurs[j]["Sexe"]=="H"]
    F = [j for j in eligibles if st.session_state.joueurs[j]["Sexe"]=="F"]

    rnd = random.random
    H.sort(key=lambda x:(counts[x], rnd()))
    F.sort(key=lambda x:(counts[x], rnd()))

    matches = []
    terrains = min(nb_terrains, len(H)//2, len(F)//2)
    for _ in range(terrains):
        if len(H)>=2 and len(F)>=2:
            h1,h2 = H.pop(0), H.pop(0)
            f1,f2 = F.pop(0), F.pop(0)
            matches.append(([h1,f1],[h2,f2]))
    if matches:
        st.session_state.matchs.append(matches)
        return True, len(matches)
    return False, 0

def generer_tous_rounds():
    n = 0
    while True:
        ok, nb = generer_round()
        if not ok or nb==0:
            break
        n += 1
    return n

# ===== Phases finales (Rounds libres) =====
def generate_quarts_from_top8(df):
    """Top8 H + Top8 F → 4 quarts aléatoires H+F vs H+F (croisement 0..3 avec 4..7)."""
    Hq = df[df["Sexe"]=="H"]["Joueur"].tolist()[:8]
    Fq = df[df["Sexe"]=="F"]["Joueur"].tolist()[:8]
    if len(Hq) < 8 or len(Fq) < 8:
        st.error(f"❌ Il faut au moins 8 hommes ET 8 femmes dans le classement (actuellement {len(Hq)}H / {len(Fq)}F).")
        return False
    random.shuffle(Hq); random.shuffle(Fq)
    quarts = []
    for i in range(4):
        quarts.append(([Hq[i], Fq[i]], [Hq[i+4], Fq[i+4]]))
    st.session_state.finals["quarts"] = quarts
    st.session_state.finals["demis"]  = []
    st.session_state.finals["finale"] = []
    st.session_state.finals["vainqueur"] = None
    return True

def recomposed_semis_from_quarters_winners(winners):
    """Recompose aléatoirement 4 gagnants (H séparés et F séparées) en nouvelles paires H+F,
       en évitant de reproduire les **mêmes duos H-F** qu'en quarts."""
    forbidden = set((t[0],t[1]) for t in winners)
    H = [t[0] for t in winners]
    F = [t[1] for t in winners]
    ok = False
    for _ in range(2000):
        random.shuffle(H); random.shuffle(F)
        pairs = list(zip(H,F))
        if all((h,f) not in forbidden for (h,f) in pairs):
            ok = True
            break
    if not ok:
        pairs = list(zip(H,F))  # fallback
    random.shuffle(pairs)
    return [ (list(pairs[0]), list(pairs[1])), (list(pairs[2]), list(pairs[3])) ]

def section_rounds_libres():
    st.title("🎾 Tournoi de Padel – Rounds libres")

    counts = scheduled_counts_rounds()
    H_elig = sum(1 for j in st.session_state.joueurs
                 if st.session_state.joueurs[j]["Sexe"]=="H" and counts[j]<max_matchs)
    F_elig = sum(1 for j in st.session_state.joueurs
                 if st.session_state.joueurs[j]["Sexe"]=="F" and counts[j]<max_matchs)
    terrains_theo = min(nb_terrains, H_elig//2, F_elig//2)

    maj_classement_global()
    df_now = df_classement()

    c1, c2 = st.columns(2)
    with c1:
        if terrains_theo>0 and st.button("⚡ Générer 1 round", use_container_width=True):
            ok, nb = generer_round()
            if ok:
                st.success(f"✅ Round {len(st.session_state.matchs)} généré ({nb} match(s))")
                st.rerun()
            else:
                st.warning("Aucun match supplémentaire possible.")
    with c2:
        if terrains_theo>0 and st.button("🚀 Générer TOUS les rounds", use_container_width=True):
            nb = generer_tous_rounds()
            if nb>0:
                st.success(f"✅ {nb} round(s) générés")
                st.rerun()
            else:
                st.warning("Aucun round supplémentaire possible.")

    if st.session_state.matchs:
        st.header("📋 Matchs du tournoi")
        for r,matches in enumerate(st.session_state.matchs, start=1):
            with st.expander(f"🏆 Round {r} - {len(matches)} match(s)", expanded=(r==len(st.session_state.matchs))):
                for idx,(e1,e2) in enumerate(matches):
                    cc1, cc2 = st.columns([3,1])
                    with cc1:
                        st.write(f"**Terrain {idx+1}:** {e1[0]} (H)+{e1[1]} (F)  🆚  {e2[0]} (H)+{e2[1]} (F)")
                    with cc2:
                        st.text_input("Score (ex: 6-4)", key=f"score_{r}_{idx}", label_visibility="collapsed")

    st.markdown("---")
    st.header("📈 Classement général")
    df = df_classement()
    if df.empty:
        st.info("Ajoute des joueurs dans la barre latérale pour commencer.")
    else:
        df.insert(0,"Rang", df.index+1)
        render_table_compact(df)

    st.markdown("---")
    # === TOP 8 toujours affiché ===
    top8_tables(df)

    # === PHASES FINALES ===
    st.markdown("---")
    st.header("🏆 Phases Finales (Rounds libres)")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⚡ Quarts Top 8 (H & F) – Tirage aléatoire", use_container_width=True):
            if generate_quarts_from_top8(df):
                st.success("✅ Quarts générés !")
                st.rerun()
    with c2:
        if st.button("♻️ Reset Phases Finales", use_container_width=True):
            st.session_state.finals = {"quarts": [], "demis": [], "finale": [], "vainqueur": None}
            st.success("Phases finales réinitialisées.")
            st.rerun()

    finals = st.session_state.finals

    # Quarts
    if finals["quarts"]:
        st.subheader("⚔️ Quarts de finale")
        for idx,(A,B) in enumerate(finals["quarts"]):
            c1,c2 = st.columns([3,1])
            with c1:
                st.write(f"**Match {idx+1}:** {A[0]} (H)+{A[1]} (F)  🆚  {B[0]} (H)+{B[1]} (F)")
            with c2:
                st.text_input("Score", key=f"rl_quart_{idx}", label_visibility="collapsed")
        if st.button("➡️ Valider & Tirage aléatoire des Demi-finales"):
            winners=[]; ok_all=True
            for idx,(A,B) in enumerate(finals["quarts"]):
                raw=(st.session_state.get(f"rl_quart_{idx}") or "").strip()
                sc=parse_score(raw)
                if not sc: ok_all=False; break
                s1,s2=sc
                winners.append(A if s1>s2 else B)
            if not ok_all or len(winners)!=4:
                st.warning("Veuillez compléter tous les scores des quarts.")
            else:
                st.session_state.finals["demis"] = recomposed_semis_from_quarters_winners(winners)
                st.success("✅ Demi-finales créées !")
                st.rerun()

    # Demis
    if finals["demis"]:
        st.subheader("⚔️ Demi-finales")
        for idx,(A,B) in enumerate(finals["demis"]):
            c1,c2 = st.columns([3,1])
            with c1:
                st.write(f"**Demi {idx+1}:** {A[0]} (H)+{A[1]} (F)  🆚  {B[0]} (H)+{B[1]} (F)")
            with c2:
                st.text_input("Score", key=f"rl_demi_{idx}", label_visibility="collapsed")
        if st.button("➡️ Valider & Tirage de la Finale"):
            winners=[]; ok_all=True
            for idx,(A,B) in enumerate(finals["demis"]):
                raw=(st.session_state.get(f"rl_demi_{idx}") or "").strip()
                sc=parse_score(raw)
                if not sc: ok_all=False; break
                s1,s2=sc
                winners.append(A if s1>s2 else B)
            if not ok_all or len(winners)!=2:
                st.warning("Veuillez compléter les scores des demi-finales.")
            else:
                random.shuffle(winners)
                st.session_state.finals["finale"] = [(winners[0], winners[1])]
                st.success("✅ Finale créée !")
                st.rerun()

    # Finale
    if finals["finale"]:
        st.subheader("🏁 Finale")
        (A,B) = finals["finale"][0]
        c1,c2 = st.columns([3,1])
        with c1:
            st.write(f"**{A[0]} (H)+{A[1]} (F)  🆚  {B[0]} (H)+{B[1]} (F)**")
        with c2:
            st.text_input("Score final", key="rl_finale", label_visibility="collapsed")
        if st.button("🏆 Déclarer le vainqueur"):
            raw=(st.session_state.get("rl_finale") or "").strip()
            sc=parse_score(raw)
            if not sc:
                st.warning("Renseigne le score final (ex: 6-4).")
            else:
                s1,s2=sc
                st.session_state.finals["vainqueur"] = A if s1>s2 else B
                st.balloons()
                st.success(f"🎉 Vainqueurs : **{st.session_state.finals['vainqueur'][0]} & {st.session_state.finals['vainqueur'][1]}** !")

# =========================
#   POULES AUTO + ÉLIMINATION
# =========================
def make_pairs_for_pools(nb_pairs):
    H = hommes[:]; F = femmes[:]
    random.shuffle(H); random.shuffle(F)
    nb = min(len(H), len(F), nb_pairs)
    return [(H[i],F[i]) for i in range(nb)]

def round_robin_indices(n):
    idxs = list(range(n))
    if n % 2 == 1:
        idxs.append(None); n += 1
    half = n//2
    schedule=[]; rows=idxs[:]
    for _ in range(n-1):
        pairings=[]
        for i in range(half):
            a = rows[i]; b = rows[n-1-i]
            if a is not None and b is not None:
                pairings.append((a,b))
        rows = [rows[0]] + [rows[-1]] + rows[1:-1]
        schedule.extend(pairings)
    return schedule

def build_pools():
    nb_p = st.session_state.poules["params"]["nb_poules"]
    tpp  = st.session_state.poules["params"]["teams_per_pool"]
    total_needed = nb_p * tpp
    teams = make_pairs_for_pools(total_needed)
    if len(teams) < total_needed:
        st.error(f"Pas assez de joueurs pour {nb_p} poule(s) de {tpp} équipes (il faut {total_needed} paires H+F).")
        return False
    st.session_state.poules["teams"] = teams
    pools=[]
    all_ids=list(range(total_needed))
    for p in range(nb_p):
        pool_ids = all_ids[p*tpp:(p+1)*tpp]
        rr = round_robin_indices(tpp)
        matches=[]
        for (a,b) in rr:
            matches.append((pool_ids[a], pool_ids[b]))
        pools.append({"teams": pool_ids, "matches": matches})
    st.session_state.poules["pools"]=pools
    st.session_state.poules["main_bracket"]=[]
    st.session_state.poules["cons_bracket"]=[]
    return True

def render_pools():
    st.subheader("📦 Poules")
    teams = st.session_state.poules["teams"]
    pools = st.session_state.poules["pools"]

    main_candidates=[]; cons_candidates=[]
    for p_idx,pool in enumerate(pools):
        with st.expander(f"🏁 Poule {p_idx+1} – {len(pool['teams'])} équipes", expanded=True):
            st.markdown("**Équipes :** " + ", ".join([f"{teams[i][0]}+{teams[i][1]}" for i in pool["teams"]]))
            for m_idx,(ti,tj) in enumerate(pool["matches"]):
                e1,e2 = teams[ti], teams[tj]
                c1,c2 = st.columns([3,1])
                with c1: st.write(f"**Match {m_idx+1}:** {e1[0]}+{e1[1]} 🆚 {e2[0]}+{e2[1]}")
                with c2: st.text_input("Score (ex: 6-4)", key=f"pool_{p_idx}_m_{m_idx}", label_visibility="collapsed")

            # Classement interne rapide
            scs=[{"team":ti,"Pts":0.0,"Jeux":0} for ti in pool["teams"]]
            def pos(team_id): 
                for k,d in enumerate(scs):
                    if d["team"]==team_id: return k

            for m_idx,(ti,tj) in enumerate(pool["matches"]):
                raw=(st.session_state.get(f"pool_{p_idx}_m_{m_idx}") or "").strip()
                sc=parse_score(raw)
                if not sc: continue
                s1,s2=sc
                ia=pos(ti); ib=pos(tj)
                if s1>s2:
                    scs[ia]["Pts"]+=3.0+s1*0.1; scs[ib]["Pts"]+=0.5+s2*0.1
                else:
                    scs[ib]["Pts"]+=3.0+s2*0.1; scs[ia]["Pts"]+=0.5+s1*0.1
                scs[ia]["Jeux"]+=s1; scs[ib]["Jeux"]+=s2

            scs=sorted(scs, key=lambda x:(x["Pts"],x["Jeux"]), reverse=True)
            dfp=pd.DataFrame([{
                "Equipe":f"{teams[d['team']][0]}+{teams[d['team']][1]}",
                "Points":round(d["Pts"],1),
                "Jeux":d["Jeux"],
            } for d in scs])
            dfp.index=dfp.index+1
            st.caption("Classement de la poule")
            render_table_compact(dfp)

            if len(scs)>=2:
                main_candidates += [ teams[scs[0]["team"]], teams[scs[1]["team"]] ]
            if len(scs)>=4:
                cons_candidates += [ teams[scs[2]["team"]], teams[scs[3]["team"]] ]

    c1,c2=st.columns(2)
    with c1:
        if st.button("🎲 Générer tableaux (principal & consolante)"):
            if len(main_candidates)>=4:
                tmp=main_candidates[:]; random.shuffle(tmp)
                first_round=[]
                for i in range(0,len(tmp),2):
                    if i+1<len(tmp): first_round.append((tmp[i],tmp[i+1]))
                st.session_state.poules["main_bracket"]=[first_round]
            if len(cons_candidates)>=4:
                tmpc=cons_candidates[:]; random.shuffle(tmpc)
                first_round_c=[]
                for i in range(0,len(tmpc),2):
                    if i+1<len(tmpc): first_round_c.append((tmpc[i],tmpc[i+1]))
                st.session_state.poules["cons_bracket"]=[first_round_c]
            st.rerun()
    with c2:
        if st.button("♻️ Reset tableaux"):
            st.session_state.poules["main_bracket"]=[]
            st.session_state.poules["cons_bracket"]=[]
            st.success("Tableaux réinitialisés")
            st.rerun()

def render_bracket(title, key_prefix, bracket):
    st.subheader(f"📈 {title}")
    if not bracket:
        st.info("Aucun tour pour le moment.")
        return
    for r_idx, rnd in enumerate(bracket, start=1):
        with st.expander(f"Tour {r_idx} – {len(rnd)} match(s)", expanded=(r_idx==len(bracket))):
            for m_idx,(A,B) in enumerate(rnd):
                c1,c2=st.columns([3,1])
                with c1:
                    st.write(f"{A[0]}+{A[1]}  🆚  {B[0]}+{B[1]}")
                with c2:
                    st.text_input("Score (ex: 6-4)", key=f"{key_prefix}_r{r_idx}_m{m_idx}", label_visibility="collapsed")
            if r_idx==len(bracket):
                if st.button(f"✅ Valider le Tour {r_idx} ({title})"):
                    winners=[]; ok=True
                    for m_idx,(A,B) in enumerate(rnd):
                        raw=(st.session_state.get(f"{key_prefix}_r{r_idx}_m{m_idx}") or "").strip()
                        sc=parse_score(raw)
                        if not sc: ok=False; break
                        s1,s2=sc
                        winners.append(A if s1>s2 else B)
                    if not ok or len(winners)<2:
                        st.warning("Complète tous les scores.")
                    else:
                        random.shuffle(winners)
                        next_round=[]
                        for i in range(0,len(winners),2):
                            if i+1<len(winners):
                                next_round.append((winners[i], winners[i+1]))
                        if next_round:
                            bracket.append(next_round)
                            st.rerun()

def section_poules():
    st.title("🎾 Tournoi de Padel – Poules + Élimination")
    nb_p = st.number_input("Nombre de poules", 1, 16,
                           value=st.session_state.poules["params"]["nb_poules"], key="nb_poules")
    tpp  = st.number_input("Équipes par poule (paires H+F)", 2, 12,
                           value=st.session_state.poules["params"]["teams_per_pool"], key="teams_per_pool")
    st.session_state.poules["params"]["nb_poules"]=int(nb_p)
    st.session_state.poules["params"]["teams_per_pool"]=int(tpp)

    if st.button("⚡ Créer / Recréer les poules", type="primary"):
        if build_pools(): st.rerun()

    if st.session_state.poules["pools"]:
        render_pools()

    st.markdown("---")
    st.header("🏆 Tableaux à élimination directe")
    render_bracket("Tableau principal", "main_bracket", st.session_state.poules["main_bracket"])
    render_bracket("Tableau consolante", "cons_bracket", st.session_state.poules["cons_bracket"])

    st.markdown("---")
    st.header("📈 Classement général (agrégé)")
    maj_classement_global()
    df = df_classement()
    if df.empty:
        st.info("Aucun résultat.")
    else:
        df.insert(0,"Rang", df.index+1)
        render_table_compact(df)

# =========================
#   POULES MANUELLES
# =========================
def build_pools_manual():
    """Construit les poules à partir des sélections manuelles H/F."""
    nb_p = st.session_state.poules_manual["params"]["nb_poules"]
    tpp  = st.session_state.poules_manual["params"]["teams_per_pool"]
    total_needed = nb_p * tpp

    # Lire sélections
    sels = st.session_state.poules_manual["selections"]
    pairs = []
    usedH=set(); usedF=set()
    for p in range(nb_p):
        for s in range(tpp):
            h_key=f"pm_{p}_{s}_H"; f_key=f"pm_{p}_{s}_F"
            h = sels.get(h_key, "")
            f = sels.get(f_key, "")
            if h and f:
                pairs.append((h,f))
                usedH.add(h); usedF.add(f)

    if len(pairs) != total_needed:
        st.error(f"Il faut définir **exactement {total_needed}** équipes (1 H + 1 F).")
        return False

    # Construire pools + round-robin
    st.session_state.poules_manual["teams"] = pairs
    pools=[]
    all_ids=list(range(total_needed))
    for p in range(nb_p):
        pool_ids = all_ids[p*tpp:(p+1)*tpp]
        rr = round_robin_indices(tpp)
        matches=[]
        for (a,b) in rr:
            matches.append((pool_ids[a], pool_ids[b]))
        pools.append({"teams": pool_ids, "matches": matches})
    st.session_state.poules_manual["pools"]=pools
    st.session_state.poules_manual["main_bracket"]=[]
    st.session_state.poules_manual["cons_bracket"]=[]
    return True

def render_pools_manual():
    st.subheader("📦 Poules (manuelles)")
    teams = st.session_state.poules_manual["teams"]
    pools = st.session_state.poules_manual["pools"]

    main_candidates=[]; cons_candidates=[]
    for p_idx,pool in enumerate(pools):
        with st.expander(f"🏁 Poule {p_idx+1} – {len(pool['teams'])} équipes", expanded=True):
            st.markdown("**Équipes :** " + ", ".join([f"{teams[i][0]}+{teams[i][1]}" for i in pool["teams"]]))
            for m_idx,(ti,tj) in enumerate(pool["matches"]):
                e1,e2 = teams[ti], teams[tj]
                c1,c2 = st.columns([3,1])
                with c1: st.write(f"**Match {m_idx+1}:** {e1[0]}+{e1[1]} 🆚 {e2[0]}+{e2[1]}")
                with c2: st.text_input("Score (ex: 6-4)", key=f"mpool_{p_idx}_m_{m_idx}", label_visibility="collapsed")

            # Classement interne rapide (mêmes règles)
            scs=[{"team":ti,"Pts":0.0,"Jeux":0} for ti in pool["teams"]]
            def pos(team_id): 
                for k,d in enumerate(scs):
                    if d["team"]==team_id: return k

            for m_idx,(ti,tj) in enumerate(pool["matches"]):
                raw=(st.session_state.get(f"mpool_{p_idx}_m_{m_idx}") or "").strip()
                sc=parse_score(raw)
                if not sc: continue
                s1,s2=sc
                ia=pos(ti); ib=pos(tj)
                if s1>s2:
                    scs[ia]["Pts"]+=3.0+s1*0.1; scs[ib]["Pts"]+=0.5+s2*0.1
                else:
                    scs[ib]["Pts"]+=3.0+s2*0.1; scs[ia]["Pts"]+=0.5+s1*0.1
                scs[ia]["Jeux"]+=s1; scs[ib]["Jeux"]+=s2

            scs=sorted(scs, key=lambda x:(x["Pts"],x["Jeux"]), reverse=True)
            dfp=pd.DataFrame([{
                "Equipe":f"{teams[d['team']][0]}+{teams[d['team']][1]}",
                "Points":round(d["Pts"],1),
                "Jeux":d["Jeux"],
            } for d in scs])
            dfp.index=dfp.index+1
            st.caption("Classement de la poule")
            render_table_compact(dfp)

            if len(scs)>=2:
                main_candidates += [ teams[scs[0]["team"]], teams[scs[1]["team"]] ]
            if len(scs)>=4:
                cons_candidates += [ teams[scs[2]["team"]], teams[scs[3]["team"]] ]

    c1,c2=st.columns(2)
    with c1:
        if st.button("🎲 Générer tableaux (principal & consolante) – Poules manuelles"):
            if len(main_candidates)>=4:
                tmp=main_candidates[:]; random.shuffle(tmp)
                first_round=[]
                for i in range(0,len(tmp),2):
                    if i+1<len(tmp): first_round.append((tmp[i],tmp[i+1]))
                st.session_state.poules_manual["main_bracket"]=[first_round]
            if len(cons_candidates)>=4:
                tmpc=cons_candidates[:]; random.shuffle(tmpc)
                first_round_c=[]
                for i in range(0,len(tmpc),2):
                    if i+1<len(tmpc): first_round_c.append((tmpc[i],tmpc[i+1]))
                st.session_state.poules_manual["cons_bracket"]=[first_round_c]
            st.rerun()
    with c2:
        if st.button("♻️ Reset tableaux – Poules manuelles"):
            st.session_state.poules_manual["main_bracket"]=[]
            st.session_state.poules_manual["cons_bracket"]=[]
            st.success("Tableaux (manuels) réinitialisés")
            st.rerun()

def render_bracket_manual(title, key_prefix, bracket):
    st.subheader(f"📈 {title}")
    if not bracket:
        st.info("Aucun tour pour le moment.")
        return
    for r_idx, rnd in enumerate(bracket, start=1):
        with st.expander(f"Tour {r_idx} – {len(rnd)} match(s)", expanded=(r_idx==len(bracket))):
            for m_idx,(A,B) in enumerate(rnd):
                c1,c2=st.columns([3,1])
                with c1:
                    st.write(f"{A[0]}+{A[1]}  🆚  {B[0]}+{B[1]}")
                with c2:
                    st.text_input("Score (ex: 6-4)", key=f"{key_prefix}_r{r_idx}_m{m_idx}", label_visibility="collapsed")
            if r_idx==len(bracket):
                if st.button(f"✅ Valider le Tour {r_idx} ({title}) – Poules manuelles"):
                    winners=[]; ok=True
                    for m_idx,(A,B) in enumerate(rnd):
                        raw=(st.session_state.get(f"{key_prefix}_r{r_idx}_m{m_idx}") or "").strip()
                        sc=parse_score(raw)
                        if not sc: ok=False; break
                        s1,s2=sc
                        winners.append(A if s1>s2 else B)
                    if not ok or len(winners)<2:
                        st.warning("Complète tous les scores.")
                    else:
                        random.shuffle(winners)
                        next_round=[]
                        for i in range(0,len(winners),2):
                            if i+1<len(winners):
                                next_round.append((winners[i], winners[i+1]))
                        if next_round:
                            bracket.append(next_round)
                            st.rerun()

def section_poules_manual():
    st.title("🎾 Tournoi de Padel – Poules (manuelles)")
    pm = st.session_state.poules_manual

    nb_p = st.number_input("Nombre de poules", 1, 16,
                           value=pm["params"]["nb_poules"], key="m_nb_poules")
    tpp  = st.number_input("Équipes par poule (paires H+F)", 2, 12,
                           value=pm["params"]["teams_per_pool"], key="m_teams_per_pool")
    pm["params"]["nb_poules"]=int(nb_p)
    pm["params"]["teams_per_pool"]=int(tpp)
    total_needed = pm["params"]["nb_poules"] * pm["params"]["teams_per_pool"]

    st.caption("Sélectionne **manuellement** chaque équipe (1 homme + 1 femme) par poule.")
    sels = pm["selections"]

    # aide : pour éviter les doublons, on suit les choix courants
    def current_used():
        usedH=set(); usedF=set()
        for p in range(pm["params"]["nb_poules"]):
            for s in range(pm["params"]["teams_per_pool"]):
                h=sels.get(f"pm_{p}_{s}_H","")
                f=sels.get(f"pm_{p}_{s}_F","")
                if h: usedH.add(h)
                if f: usedF.add(f)
        return usedH, usedF

    for p in range(pm["params"]["nb_poules"]):
        with st.expander(f"✍️ Poule {p+1} – définir {pm['params']['teams_per_pool']} équipes", expanded=True):
            for s in range(pm["params"]["teams_per_pool"]):
                usedH, usedF = current_used()
                h_key=f"pm_{p}_{s}_H"; f_key=f"pm_{p}_{s}_F"
                # autoriser le choix déjà sélectionné pour ce slot (sinon il disparaît des options)
                current_h = sels.get(h_key,"")
                current_f = sels.get(f_key,"")
                optH = [x for x in hommes if x==current_h or x not in usedH]
                optF = [x for x in femmes if x==current_f or x not in usedF]
                c1,c2 = st.columns(2)
                with c1:
                    sels[h_key] = st.selectbox(
                        f"Equipe {s+1} – Homme", optH, index=optH.index(current_h) if current_h in optH else 0 if optH else None, key=h_key
                    ) if optH else ""
                with c2:
                    sels[f_key] = st.selectbox(
                        f"Equipe {s+1} – Femme", optF, index=optF.index(current_f) if current_f in optF else 0 if optF else None, key=f_key
                    ) if optF else ""

    c1,c2 = st.columns(2)
    with c1:
        if st.button("⚡ Créer / Mettre à jour les poules (manuelles)", type="primary"):
            if build_pools_manual():
                st.success(f"✅ {pm['params']['nb_poules']} poule(s) créées.")
                st.rerun()
    with c2:
        if st.button("♻️ Reset (sélections & tableaux manuels)"):
            pm["selections"]={}
            pm["teams"]=[]; pm["pools"]=[]; pm["main_bracket"]=[]; pm["cons_bracket"]=[]
            st.success("Tout a été réinitialisé pour les poules manuelles.")
            st.rerun()

    # Rendu des poules si dispo
    if pm["pools"]:
        render_pools_manual()

    st.markdown("---")
    st.header("🏆 Tableaux à élimination directe (manuels)")
    render_bracket_manual("Tableau principal (man.)", "manual_main_bracket", pm["main_bracket"])
    render_bracket_manual("Tableau consolante (man.)", "manual_cons_bracket", pm["cons_bracket"])

    st.markdown("---")
    st.header("📈 Classement général (agrégé)")
    maj_classement_global()
    df = df_classement()
    if df.empty:
        st.info("Aucun résultat.")
    else:
        df.insert(0,"Rang", df.index+1)
        render_table_compact(df)

# =========================
#   ROUTAGE
# =========================
if st.session_state.mode == "Rounds libres":
    section_rounds_libres()
elif st.session_state.mode == "Poules + Élimination":
    section_poules()
else:  # Poules (manuelles)
    section_poules_manual()
