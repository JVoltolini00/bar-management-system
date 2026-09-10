import sqlite3
from datetime import datetime

DB_NAME = "bar.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def crea_tabelle():
    conn = get_connection()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS prodotti
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     nome
                     TEXT
                     NOT
                     NULL
                     UNIQUE,
                     prezzo
                     REAL,
                     quantita
                     INTEGER
                     DEFAULT
                     0,
                     categoria
                     TEXT
                 )''')

    c.execute('''CREATE TABLE IF NOT EXISTS ordini
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     tavolo
                     TEXT
                     NOT
                     NULL,
                     prodotto_nome
                     TEXT
                     NOT
                     NULL,
                     quantita
                     INTEGER
                     NOT
                     NULL,
                     stato
                     TEXT
                     DEFAULT
                     'in_attesa'
                 )''')

    c.execute('''CREATE TABLE IF NOT EXISTS storico_incassi
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     data
                     TEXT,
                     importo
                     REAL,
                     tavolo
                     TEXT
                 )''')

    c.execute('''CREATE TABLE IF NOT EXISTS tavoli_pos
                 (
                     nome_tavolo
                     TEXT
                     PRIMARY
                     KEY,
                     riga
                     INTEGER,
                     colonna
                     INTEGER
                 )''')

    conn.commit()
    conn.close()


def inizializza_dati_base():
    conn = get_connection()
    c = conn.cursor()

    if c.execute("SELECT count(*) FROM prodotti").fetchone()[0] == 0:
        c.executemany("INSERT INTO prodotti (nome, prezzo, quantita, categoria) VALUES (?, ?, ?, ?)",
                      [("Heineken", 4.0, 30, "Birra"), ("Coca Cola", 3.0, 50, "Bibita"), ("Toast", 5.0, 20, "Cibo")])

    if c.execute("SELECT count(*) FROM tavoli_pos").fetchone()[0] == 0:
        # Griglia 10x8: Posizioniamo i tavoli a "L"
        tavoli = [
            ("Tavolo 1", 0, 0), ("Tavolo 2", 1, 0), ("Tavolo 3", 2, 0),
            ("Tavolo 4", 3, 0), ("Tavolo 5", 4, 0),
            ("Tavolo 6", 0, 1), ("Tavolo 7", 0, 2), ("Tavolo 8", 0, 3),
            ("Tavolo 9", 0, 4), ("Tavolo 10", 0, 5)
        ]
        c.executemany("INSERT INTO tavoli_pos (nome_tavolo, riga, colonna) VALUES (?, ?, ?)", tavoli)

    conn.commit()
    conn.close()


def leggi_menu():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM prodotti ORDER BY categoria ASC, nome ASC").fetchall()


def leggi_tavoli_pos():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM tavoli_pos").fetchall()


def leggi_ordini_tavolo(tavolo):
    with get_connection() as conn:
        query = '''
                SELECT o.*, p.prezzo
                FROM ordini o
                         LEFT JOIN prodotti p ON o.prodotto_nome = p.nome
                WHERE o.tavolo = ? \
                  AND o.stato != 'pagato' \
                '''
        return conn.execute(query, (tavolo,)).fetchall()


def aggiungi_ordine(tavolo, prodotto_nome, quantita):
    conn = get_connection()
    try:
        cur = conn.cursor()
        res = cur.execute("SELECT quantita FROM prodotti WHERE nome = ?", (prodotto_nome,)).fetchone()
        if not res or res['quantita'] < quantita:
            return False, "Prodotto esaurito!"

        cur.execute("UPDATE prodotti SET quantita = quantita - ? WHERE nome = ?", (quantita, prodotto_nome))
        cur.execute("INSERT INTO ordini (tavolo, prodotto_nome, quantita) VALUES (?, ?, ?)",
                    (tavolo, prodotto_nome, quantita))
        conn.commit()
        return True, "Aggiunto"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def chiudi_tavolo(tavolo):
    conn = get_connection()
    try:
        cur = conn.cursor()
        query = '''
                SELECT sum(o.quantita * p.prezzo) as totale
                FROM ordini o
                         JOIN prodotti p ON o.prodotto_nome = p.nome
                WHERE o.tavolo = ? \
                  AND o.stato != 'pagato' \
                '''
        res = cur.execute(query, (tavolo,)).fetchone()
        totale = res['totale'] if res['totale'] else 0.0

        if totale > 0:
            oggi = datetime.now().strftime("%Y-%m-%d")
            cur.execute("INSERT INTO storico_incassi (data, importo, tavolo) VALUES (?, ?, ?)", (oggi, totale, tavolo))
            cur.execute("UPDATE ordini SET stato = 'pagato' WHERE tavolo = ?", (tavolo,))
            conn.commit()
            return True, f"Incassati € {totale:.2f}"
        return False, "Nessun ordine da pagare."
    except Exception as e:
        return False, f"Errore: {str(e)}"
    finally:
        conn.close()


def rifornisci_prodotto(nome, qta):
    with get_connection() as conn:
        conn.execute("UPDATE prodotti SET quantita = quantita + ? WHERE nome = ?", (qta, nome))
        conn.commit()


def crea_prodotto(nome, prezzo, qta, cat):
    try:
        with get_connection() as conn:
            conn.execute("INSERT INTO prodotti (nome, prezzo, quantita, categoria) VALUES (?, ?, ?, ?)",
                         (nome, prezzo, qta, cat))
            conn.commit()
        return True, "Ok"
    except:
        return False, "Errore (nome duplicato?)"


def elimina_prodotto(nome_prodotto):
    with get_connection() as conn:
        conn.execute("DELETE FROM prodotti WHERE nome = ?", (nome_prodotto,))
        conn.commit()


def aggiorna_posizione_tavolo(nome, riga, colonna):
    with get_connection() as conn:
        conn.execute("DELETE FROM tavoli_pos WHERE nome_tavolo = ?", (nome,))
        conn.execute("INSERT INTO tavoli_pos VALUES (?, ?, ?)", (nome, riga, colonna))
        conn.commit()


def elimina_tavolo(nome):
    with get_connection() as conn:
        conn.execute("DELETE FROM tavoli_pos WHERE nome_tavolo = ?", (nome,))
        conn.commit()


def get_incassi_stats():
    oggi = datetime.now().strftime("%Y-%m-%d")
    mese = datetime.now().strftime("%Y-%m")
    anno = datetime.now().strftime("%Y")

    conn = get_connection()
    inc_oggi = conn.execute("SELECT sum(importo) FROM storico_incassi WHERE data = ?", (oggi,)).fetchone()[0] or 0
    inc_mese = conn.execute("SELECT sum(importo) FROM storico_incassi WHERE data LIKE ?", (f"{mese}%",)).fetchone()[
                   0] or 0
    inc_anno = conn.execute("SELECT sum(importo) FROM storico_incassi WHERE data LIKE ?", (f"{anno}%",)).fetchone()[
                   0] or 0
    conn.close()
    return inc_oggi, inc_mese, inc_anno


if __name__ == "__main__":
    crea_tabelle()
    inizializza_dati_base()