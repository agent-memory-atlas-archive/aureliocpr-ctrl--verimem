"""Lo stato in cui una misura è stata presa, stampato IN TESTA alla misura.

Il 13 settembre 2026 una misura ha dato un risultato che due ore dopo non si
riproduceva, e per spiegarlo sono state formulate e falsificate TRE ipotesi —
la delega dell'encoder, gli alias della data dir, un demone con un modello
diverso — tutte plausibili, tutte sbagliate, ognuna costata un banco. La causa
resta ignota, e il motivo per cui resta ignota non è che fosse difficile: è che
**le condizioni della prima misura non erano state registrate**, e lo store era
stato cancellato subito dopo.

Questo file non spiega niente. Registra, e costa un secondo.

    python scripts/stato_della_misura.py [data_dir]

⚠️ NON INTERROGA IL PRODOTTO e non carica modelli: legge variabili d'ambiente,
file di scoperta e il database. Una sonda che accende ciò che deve osservare
cambia ciò che osserva — e qui il soggetto è proprio quale motore si accende.

📌 E LA REGOLA CHE VA CON QUESTO STRUMENTO: **un banco non cancella il proprio
store finché il pari non l'ha letto.** «Chiudo ciò che apro» è una buona
abitudine e qui cede: quel giorno lo store è stato rimosso subito dopo la
misura, e con esso l'unica prova che avrebbe chiuso la domanda all'indietro.
La pulizia si fa dopo la lettura, non dopo l'esecuzione.

⚠️ E DICE ANCHE CIÒ CHE NON C'È. Una variabile non impostata è informazione
quanto una impostata: la riga «non impostata» distingue «l'ho tolta» da «non ci
ho pensato», e le tre ipotesi di quel giorno nascevano tutte dal non saperlo.
"""
from __future__ import annotations

import datetime
import json
import os
import pathlib
import socket
import sqlite3
import sys

#: Le variabili che cambiano ciò che una scrittura fa. L'elenco è esplicito e
#: non un prefisso: `HIPPO_*` prenderebbe anche quelle che non contano, e una
#: riga di rumore in un rapporto si smette di leggere.
VARIABILI = (
    "HIPPO_DATA_DIR", "ENGRAM_DATA_DIR", "VERIMEM_DATA_DIR",
    "HIPPO_ENCODE_DELEGATE_ONLY", "ENGRAM_ENCODE_SERVICE",
    "HIPPO_OFFLINE", "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE",
    "ENGRAM_SEMANTIC_CONFLICT", "ENGRAM_SUPERSEDE_SAME_SOURCE",
    "ENGRAM_VALIDATE_DEFAULT", "VERIMEM_MULTI_WRITER",
    "ENGRAM_GROUNDING_WRITE", "VERIMEM_SCAN_CAP",
)

#: I file con cui i processi si annunciano. Ce n'è più di uno, di sistemi
#: diversi, e il primo che si trova non è per forza quello che il prodotto usa.
SCOPERTA = ("daemon.json", "encode_service.json", "clp-rust-daemon.json")


def _riga(etichetta: str, valore: object) -> str:
    return f"  {etichetta:<30} {valore}"


def _in_ascolto(porta: int) -> bool:
    s = socket.socket()
    s.settimeout(0.4)
    try:
        s.connect(("127.0.0.1", int(porta)))
        return True
    except Exception:  # noqa: BLE001 — una porta chiusa non è un errore
        return False
    finally:
        s.close()


def stato(data_dir: pathlib.Path | None = None) -> list[str]:
    fuori = ["=" * 62,
             "STATO DELLA MISURA — " + datetime.datetime.now().strftime(
                 "%Y-%m-%d %H:%M:%S"),
             "=" * 62, "", "AMBIENTE"]
    for v in VARIABILI:
        val = os.environ.get(v)
        fuori.append(_riga(v, val if val is not None else "— non impostata"))

    fuori.append("")
    fuori.append("FILE DI SCOPERTA (e chi risponde davvero)")
    casa = pathlib.Path.home() / ".engram"
    trovato = False
    for nome in SCOPERTA:
        p = casa / nome
        if not p.exists():
            fuori.append(_riga(nome, "— non esiste"))
            continue
        trovato = True
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            fuori.append(_riga(nome, f"illeggibile: {type(exc).__name__}"))
            continue
        porta = d.get("port")
        stato_porta = ("in ascolto" if porta and _in_ascolto(porta)
                       else "NON risponde")
        fuori.append(_riga(nome, f"porta {porta} ({stato_porta})  "
                                 f"modello {d.get('encoder', '—')}"))
    if not trovato:
        fuori.append(_riga("", "nessun file di scoperta: nessun demone annunciato"))

    fuori.append("")
    fuori.append("LO STORE")
    dd = data_dir or (pathlib.Path(os.environ["HIPPO_DATA_DIR"])
                      if os.environ.get("HIPPO_DATA_DIR") else casa)
    db = pathlib.Path(dd) / "semantic" / "semantic.db"
    fuori.append(_riga("data dir", dd))
    if not db.exists():
        fuori.append(_riga("database", "— non esiste ancora"))
        return fuori
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        # LA DIMENSIONE DEI VETTORI, per gruppo: due dimensioni diverse nello
        # stesso corpus vogliono dire che due motori hanno scritto qui, ed è
        # il genere di cosa che non si nota guardando i fatti.
        gruppi = con.execute(
            "SELECT length(embedding)/4, COUNT(*) FROM facts "
            "GROUP BY 1 ORDER BY 2 DESC").fetchall()
        fuori.append(_riga("fatti per dimensione",
                           ", ".join(f"{d}d: {n}" for d, n in gruppi) or "—"))
        ultimo = con.execute(
            "SELECT substr(id,1,8), length(embedding)/4, "
            "COALESCE(embedding_model,'—'), datetime(created_at,'unixepoch','localtime') "
            "FROM facts ORDER BY created_at DESC LIMIT 1").fetchone()
        if ultimo:
            fuori.append(_riga("ultimo fatto scritto",
                               f"{ultimo[0]}  {ultimo[1]}d  {ultimo[2]}  {ultimo[3]}"))
        con.close()
    except Exception as exc:  # noqa: BLE001 — una sonda non rompe la misura
        fuori.append(_riga("database", f"non leggibile: {type(exc).__name__}: {exc}"))
    return fuori


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    dd = pathlib.Path(argv[0]) if argv else None
    print("\n".join(stato(dd)))
    # Sempre 0: questo strumento REGISTRA, non giudica. Un'uscita diversa da
    # zero farebbe fallire il banco che lo chiama per una cosa che il banco
    # non stava misurando.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
