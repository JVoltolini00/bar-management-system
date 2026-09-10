import streamlit as st
import sys
import os
import time
from datetime import datetime

sys.path.append(os.getcwd())
try:
    import database as db
except ModuleNotFoundError:
    st.error("ERRORE: Manca database.py")
    st.stop()

st.set_page_config(page_title="Bar", layout="wide")
db.crea_tabelle()
db.inizializza_dati_base()

# --- CSS: Grandezza e Colori ---
st.markdown("""
<style>
/* 1. TAVOLI GIGANTI */
div.stButton > button {
    width: 100%;
    min_height: 110px !important; /* Molto alti */
    font-weight: bold;
    font-size: 20px !important;   /* Scritta grande */
    border-radius: 12px;
    margin-bottom: 8px;
    box-shadow: 0px 4px 6px rgba(0,0,0,0.3);
}

/* 2. MURA SPESSE (Bianco su nero) */
div[data-testid="stVerticalBlockBorderWrapper"] > div {
    border-width: 5px !important;
    border-style: solid !important;
    border-color: var(--text-color) !important; 
    border-radius: 0px 0px 20px 20px;
    padding: 15px;
}

/* 3. Tasti Speciali */
div[data-testid="column"] button:contains("AGGIUNGI") {
    background-color: #2e7d32 !important;
    color: white !important;
    min-height: 60px !important;
}
div[data-testid="column"] button:contains("CHIUDI") {
    background-color: #c62828 !important;
    color: white !important;
    min-height: 60px !important;
}
/* Tasto ELIMINA piccolo nel magazzino */
div[data-testid="column"] button:contains("🗑️") {
    background-color: #b71c1c !important;
    color: white !important;
    min-height: 35px !important;
    font-size: 14px !important;
}

/* 4. Bancone Enorme */
.bancone-box {
    background-color: #555;
    color: white;
    font-size: 22px;
    font-weight: bold;
    height: 110px; /* Alto come i tavoli */
    display: flex;
    align-items: center;
    justify-content: center;
    border: 3px solid var(--text-color);
    border-radius: 10px;
    width: 150%; /* Trucco per farlo sembrare più largo */
    margin-left: -25%;
    z-index: 10;
}
</style>
""", unsafe_allow_html=True)

st.sidebar.title("Bar")
menu = st.sidebar.radio("Menu", ["Sala", "Magazzino", "Contabilita", "Modifica Sala"])

if menu == "Sala":
    st.title("Sala Bar")

    if 'tavolo_aperto' in st.session_state and st.session_state.tavolo_aperto:
        tavolo = st.session_state.tavolo_aperto
        st.button(f"🔙 TORNA IN SALA", on_click=lambda: st.session_state.pop('tavolo_aperto'))
        st.divider()
        st.header(f"Gestione: {tavolo}")

        ordini = db.leggi_ordini_tavolo(tavolo)
        totale_tavolo = 0.0

        if ordini:
            st.info("📝 Ordini attuali:")
            for o in ordini:
                prz = o['prezzo'] if o['prezzo'] else 0.0
                subtot = o['quantita'] * prz
                totale_tavolo += subtot
                st.write(f"- **{o['quantita']}x** {o['prodotto_nome']} (€ {subtot:.2f})")

            st.write("---")
            label_incassa = f"CHIUDI E INCASSA (€ {totale_tavolo:.2f})"
            if st.button(label_incassa, type="primary"):
                ok, msg = db.chiudi_tavolo(tavolo)
                if ok:
                    st.success(f"✅ {msg}")
                    time.sleep(1.5)
                    del st.session_state['tavolo_aperto']
                    st.rerun()
                else:
                    st.warning(msg)
        else:
            st.write("🟢 Il tavolo è libero.")

        st.markdown("### ➕ Aggiungi Prodotto")
        prodotti = db.leggi_menu()
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            p_scelto = st.selectbox("Scegli", [p['nome'] for p in prodotti], label_visibility="collapsed")
        with c2:
            qta = st.number_input("Qtà", 1, 50, 1, label_visibility="collapsed")
        with c3:
            if st.button("AGGIUNGI"):
                ok, msg = db.aggiungi_ordine(tavolo, p_scelto, qta)
                if ok:
                    st.success("Preso!")
                    time.sleep(0.3)
                    st.rerun()
                else:
                    st.error(msg)
    else:
        st.write("Clicca su un tavolo per ordinare.")

        # MURA SPESSE (Container)
        with st.container(border=True):
            st.markdown(f"<h3 style='text-align:center; margin-top:-10px;'>INGRESSO</h3>", unsafe_allow_html=True)

            tavoli_pos = db.leggi_tavoli_pos()

            # GRIGLIA RIDOTTA -> CELLE PIÙ GRANDI
            MAX_RIGHE = 10
            MAX_COLONNE = 8

            for r in range(MAX_RIGHE):
                cols = st.columns(MAX_COLONNE)
                for c in range(MAX_COLONNE):

                    # BANCONE GRANDE (Riga 8, Colonne 2-4)
                    if r == 8 and (2 <= c <= 4):
                        if c == 3:  # Centro
                            with cols[c]:
                                st.markdown('<div class="bancone-box">BANCONE</div>', unsafe_allow_html=True)
                        else:
                            with cols[c]:
                                st.write("")  # Spazio riservato

                    else:
                        tavolo_qui = next((t for t in tavoli_pos if t['riga'] == r and t['colonna'] == c), None)
                        with cols[c]:
                            if tavolo_qui:
                                nome = tavolo_qui['nome_tavolo']
                                ordini = db.leggi_ordini_tavolo(nome)
                                label = f"🔴 {nome}" if ordini else f"🟢 {nome}"
                                if st.button(label, key=f"btn_{r}_{c}"):
                                    st.session_state.tavolo_aperto = nome
                                    st.rerun()
                            else:
                                st.write("")

elif menu == "Magazzino":
    st.title("Magazzino")
    t1, t2, t3 = st.tabs(["Scorte (Gestione)", "Rifornimento", "Nuovo Prodotto"])

    with t1:
        prodotti = db.leggi_menu()
        categorie = sorted(list(set([p['categoria'] for p in prodotti])))

        for cat in categorie:
            st.markdown(f"### {cat}")
            k1, k2, k3, k4 = st.columns([4, 2, 2, 1])
            k1.caption("Nome")
            k2.caption("Qtà")
            k3.caption("Prezzo")
            k4.caption("Canc")

            prodotti_cat = [p for p in prodotti if p['categoria'] == cat]

            for p in prodotti_cat:
                c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
                c1.write(f"**{p['nome']}**")
                if p['quantita'] < 10:
                    c2.markdown(f":red[{p['quantita']}]")
                else:
                    c2.write(f"{p['quantita']}")
                c3.write(f"€ {p['prezzo']}")
                if c4.button("🗑️", key=f"del_{p['id']}"):
                    db.elimina_prodotto(p['nome'])
                    st.rerun()
            st.divider()

    with t2:
        c1, c2 = st.columns(2)
        nome = c1.selectbox("Prodotto", [p['nome'] for p in db.leggi_menu()])
        qta = c2.number_input("Qta Arrivata", 1, 1000, 1)
        if st.button("Aggiorna", type="primary"):
            db.rifornisci_prodotto(nome, qta)
            st.success("Aggiornato")
            time.sleep(0.5)
            st.rerun()

    with t3:
        with st.form("new"):
            nome = st.text_input("Nome")
            cat = st.selectbox("Categoria", ["Birra", "Cocktail", "Bibita", "Cibo", "Altro"])
            c1, c2 = st.columns(2)
            prz = c1.number_input("Prezzo", 0.0, 100.0, 5.0)
            qta = c2.number_input("Qta Iniziale", 0, 1000, 10)
            if st.form_submit_button("Crea"):
                if nome:
                    ok, msg = db.crea_prodotto(nome, prz, qta, cat)
                    if ok:
                        st.success("Creato")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Errore")

elif menu == "Contabilita":
    st.title("Contabilita")
    st.markdown(f"Data: **{datetime.now().strftime('%d/%m/%Y')}**")
    inc_oggi, inc_mese, inc_anno = db.get_incassi_stats()
    c1, c2, c3 = st.columns(3)
    c1.metric("Oggi", f"€ {inc_oggi:.2f}")
    c2.metric("Mese", f"€ {inc_mese:.2f}")
    c3.metric("Anno", f"€ {inc_anno:.2f}")
    st.divider()
    st.write("Storico:")
    conn = db.get_connection()
    df = conn.execute("SELECT data, tavolo, importo FROM storico_incassi ORDER BY id DESC").fetchall()
    conn.close()
    st.table([{"Data": r['data'], "Tavolo": r['tavolo'], "Incasso": f"€ {r['importo']:.2f}"} for r in df])

elif menu == "Modifica Sala":
    st.title("Configurazione")
    # Limiti impostati sulla nuova griglia 10x8
    st.info("Sposta i tavoli. Righe: 0-9, Colonne: 0-7")
    st.warning("Zona Bancone: Riga 8, Colonne 2-4")

    tavoli = db.leggi_tavoli_pos()
    for t in tavoli:
        with st.expander(f"Modifica {t['nome_tavolo']}"):
            c1, c2, c3 = st.columns(3)
            # Limiti corretti per non dare errori
            nr = c1.number_input("Riga", 0, 9, t['riga'], key=f"r_{t['nome_tavolo']}")
            nc = c2.number_input("Col", 0, 7, t['colonna'], key=f"c_{t['nome_tavolo']}")
            if c3.button("Salva", key=f"s_{t['nome_tavolo']}"):
                db.aggiorna_posizione_tavolo(t['nome_tavolo'], nr, nc)
                st.rerun()
            if st.button("Elimina Tavolo", key=f"d_{t['nome_tavolo']}"):
                db.elimina_tavolo(t['nome_tavolo'])
                st.rerun()
    st.divider()
    with st.form("add"):
        nome = st.text_input("Nome Nuovo Tavolo")
        c1, c2 = st.columns(2)
        r = c1.number_input("Riga", 0, 9)
        c = c2.number_input("Col", 0, 7)
        if st.form_submit_button("Aggiungi"):
            if nome:
                db.aggiorna_posizione_tavolo(nome, r, c)
                st.rerun()