"""Lo strumento che registra lo stato deve dire anche ciò che NON c'è.

Il 13 settembre 2026 tre ipotesi sono state formulate e falsificate una dopo
l'altra per spiegare una misura che non si riproduceva, e nessuna delle tre
sarebbe nata se le condizioni della prima misura fossero state registrate.
Tutte e tre riguardavano variabili d'ambiente **assenti**: la delega tolta o
messa, gli alias della data dir puliti o sporchi.

⇒ Il valore di questo strumento sta quasi tutto nel NEGATIVO. Uno che stampasse
solo le variabili impostate sembrerebbe funzionare — l'uscita è piena, le righe
ci sono — e non distinguerebbe «l'ho tolta apposta» da «non ci ho pensato»,
che è proprio la differenza su cui si sono spesi tre banchi.

Perciò il presidio principale qui non è «stampa il valore»: è **stampa la
riga anche quando il valore non c'è**.
"""

from __future__ import annotations

import pathlib
import sqlite3
import tempfile

import pytest

from scripts.stato_della_misura import VARIABILI, stato


def _testo(dd: pathlib.Path | None = None) -> str:
    return "\n".join(stato(dd))


def test_una_variabile_impostata_compare_col_suo_valore(monkeypatch):
    monkeypatch.setenv("HIPPO_ENCODE_DELEGATE_ONLY", "1")
    assert "HIPPO_ENCODE_DELEGATE_ONLY     1" in _testo(), (
        "una variabile impostata non compare col suo valore")


def test_una_variabile_NON_impostata_compare_lo_stesso(monkeypatch):
    """IL CUORE: l'assenza è informazione, e va stampata.

    Senza questa riga chi legge non sa se la variabile fosse tolta apposta o
    semplicemente non considerata — ed è esattamente l'ambiguità che ha
    prodotto tre ipotesi sbagliate.
    """
    monkeypatch.delenv("HIPPO_ENCODE_DELEGATE_ONLY", raising=False)
    t = _testo()
    assert "HIPPO_ENCODE_DELEGATE_ONLY" in t, (
        "una variabile non impostata sparisce dal rapporto: chi legge non "
        "distingue «tolta apposta» da «non considerata»")
    assert "— non impostata" in t, (
        "la riga c'è ma non dichiara che il valore manca")


def test_TUTTE_le_variabili_dell_elenco_compaiono_sempre(monkeypatch):
    """⚠️ Il controllo che rende il precedente non aneddotico: una sola
    variabile assente stampata non dice niente sulle altre tredici."""
    for v in VARIABILI:
        monkeypatch.delenv(v, raising=False)
    t = _testo()
    mancanti = [v for v in VARIABILI if v not in t]
    assert not mancanti, (
        f"{len(mancanti)} variabili su {len(VARIABILI)} spariscono quando non "
        f"sono impostate: {mancanti}")


def test_uno_store_che_non_esiste_non_fa_esplodere_la_sonda():
    """Una sonda che si rompe dove la misura stava per cominciare toglie
    informazione invece di darne — e lo fa proprio nel caso in cui serve, cioè
    su uno store appena creato e ancora vuoto."""
    vuota = pathlib.Path(tempfile.mkdtemp(prefix="stato-vuoto-"))
    t = _testo(vuota)
    assert "non esiste ancora" in t, (
        f"su uno store vuoto la sonda non lo dichiara: {t[-300:]}")


def test_due_dimensioni_nello_stesso_corpus_si_vedono():
    """Il caso che questo strumento esiste per rendere visibile: due motori
    che hanno scritto nello stesso store. Guardando i fatti non si nota;
    guardando le dimensioni, sì."""
    d = pathlib.Path(tempfile.mkdtemp(prefix="stato-misto-"))
    (d / "semantic").mkdir(parents=True)
    con = sqlite3.connect(d / "semantic" / "semantic.db")
    con.execute("CREATE TABLE facts (id TEXT, embedding BLOB, "
                "embedding_model TEXT, created_at REAL)")
    con.executemany(
        "INSERT INTO facts VALUES (?,?,?,?)",
        [("a", b"\x00" * (768 * 4), "e5-base", 1.0),
         ("b", b"\x00" * (384 * 4), "MiniLM", 2.0)])
    con.commit()
    con.close()
    t = _testo(d)
    assert "768d: 1" in t and "384d: 1" in t, (
        "due dimensioni diverse nello stesso corpus non vengono distinte, e "
        f"questo e' il caso che lo strumento esiste per mostrare:\n{t[-300:]}")
