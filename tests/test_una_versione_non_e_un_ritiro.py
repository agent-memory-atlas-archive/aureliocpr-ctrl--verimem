"""T56 RED-2 — due versioni della stessa grandezza, e cosa rende ogni lettura.

LA PROMESSA (ruolo di prodotto, 12 settembre 2026): le versioni restano
entrambe nel corpus, e a cambiare è *cosa rende una lettura*:

    lettura di default        -> 1 risposta, la più recente
    --include-superseded      -> 2 risposte, e si vede QUALE è superata
    ogni riga resa            -> dice di quale grandezza parla

⚠️ **LA COPPIA È STATA CAMBIATA, E IL PERCHÉ È LA LEZIONE DI QUESTO FILE.**
La prima stesura usava «mediana 33.0s» e «min 16.3s» della stessa esecuzione:
**due grandezze diverse, vere insieme**, che nessuna politica deve ritirare —
e questo file lo dichiarava quindici righe sopra il proprio assert pretendendo
lo stesso una riga sola. La lettura di default ne rendeva due perché **erano
due fatti vivi**, e il banco lo chiamava difetto del prodotto.

Ne discendeva l'altro esito che sembrava un verdetto: la cura della seconda
cella non mordeva. Non poteva: senza supersessione nessuna delle due righe
portava il campo da mostrare, quindi la cura non aveva niente da stampare e i
due alberi davano lo stesso esito, cella per cella. **Non falsificata: non
messa alla prova.** La coppia qui sotto — stessa grandezza, stessa fonte, due
istanti — è la riscrittura del banco E l'esperimento che mette alla prova
quella cura.

⚠️ **PERCHÉ ALLA PORTA E NON DALL'SDK.** Il campo che distingue una versione
superata (`superseded_by`) è già nel dizionario che l'SDK restituisce — la sua
vista lo porta sempre, `None` quando il fatto è vivo. Un test scritto lì
sarebbe verde col difetto intero: la riga che la riga di comando stampa porta
testo, somiglianza e moat. Il livello a cui si misura decide il verdetto.

PREDIZIONI, dichiarate prima di eseguire (12 settembre, 19:30 lette):

    cella 1  default              -> VERDE con la coppia nuova (ora c'è un
                                     ritiro: la vista curata ne rende una)
    cella 2  superati             -> ROSSO senza la cura, VERDE con la cura.
                                     È l'unica cella che le distingue, e per
                                     questo porta `xfail(strict=True)`: se
                                     passa senza cura, XPASS = fallimento e il
                                     banco lo dice da sé
    cella 3  la grandezza         -> VERDE, e vedi il limite dichiarato nel
                                     suo docstring: qui la soddisfa il TESTO
                                     dei fatti, non la porta
    cella 4  al passato           -> VERDE: misurato il 12 settembre, il
                                     ripiego sulla data di creazione regge

Ticket: T56 (`docs/stato-reale/ticket/T56-supersessione.md`, §6bis e §6ter).
Il primo RED è `tests/test_le_tre_porte_conservano_lo_stesso_numero.py`.

Comando (una sola esecuzione, un file solo)::

    HIPPO_OFFLINE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \\
    ENGRAM_ENCODE_SERVICE=0 pytest -q -p no:randomly -rsfE \\
    tests/test_una_versione_non_e_un_ritiro.py
"""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time

import pytest

#: DUE VERSIONI DELLA STESSA GRANDEZZA, da una fonte che le contiene entrambe
#: in successione. È il caso che il ticket porta come falsificatore del
#: criterio dell'impronta: una fonte PUÒ contenere una successione temporale,
#: e allora i due fatti sono versioni — non due letture complementari.
FONTE = ("latency report, 12 September: the median was 33.0s on the morning "
         "run, then 41.2s after the index rebuild")
PRIMA = "La latenza mediana è 33.0s."
SECONDA = "La latenza mediana è 41.2s."
TOPIC = "t56/versione"
DOMANDA = "latenza"
#: Il nome della grandezza di cui parlano entrambe: la terza asserzione della
#: promessa chiede che ogni riga resa lo porti.
GRANDEZZA = "mediana"


def _ambiente(dati: pathlib.Path) -> dict[str, str]:
    env = {**os.environ,
           "HIPPO_DATA_DIR": str(dati), "ENGRAM_ENCODE_SERVICE": "0",
           "HIPPO_OFFLINE": "1", "HF_HUB_OFFLINE": "1",
           "TRANSFORMERS_OFFLINE": "1",
           #: la riga non deve andare a capo: la griglia si restringe da sola
           #: sul terminale del banco, e una riga spezzata si conta due volte
           "COLUMNS": "200"}
    for alias in ("ENGRAM_DATA_DIR", "VERIMEM_DATA_DIR"):
        env.pop(alias, None)
    return env


def _cli(env: dict[str, str], *argomenti: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "verimem.cli", *argomenti],
                          env=env, capture_output=True, text=True, timeout=300)


@pytest.fixture(scope="module")
def store() -> dict[str, object]:
    """Scrive le due versioni UNA volta e tiene l'istante che sta in mezzo.

    L'istante serve all'ultima cella: `--as-of` chiede «cosa valeva allora», e
    «allora» deve cadere DOPO la prima scrittura e PRIMA della seconda. Si
    prende dall'orologio e non dal database di proposito — leggere
    `created_at` legherebbe il banco allo schema invece che al contratto.
    """
    dati = pathlib.Path(tempfile.mkdtemp(prefix="t56-versione-"))
    env = _ambiente(dati)
    prima = _cli(env, "facts", "add", "-p", PRIMA, "--source", FONTE,
                 "--topic", TOPIC)
    if prima.returncode != 0:
        pytest.skip("CONTROLLO POSITIVO SPENTO: la prima scrittura non è "
                    f"riuscita (exit {prima.returncode}), quindi nessuna di "
                    f"queste letture misura qualcosa. {prima.stderr[-400:]}")
    time.sleep(1.1)          # due istanti distinti, non due righe nello stesso
    in_mezzo = time.time()
    time.sleep(1.1)
    seconda = _cli(env, "facts", "add", "-p", SECONDA, "--source", FONTE,
                   "--topic", TOPIC)
    if seconda.returncode != 0:
        pytest.skip("CONTROLLO POSITIVO SPENTO: la seconda scrittura non è "
                    f"riuscita (exit {seconda.returncode}). "
                    f"{seconda.stderr[-400:]}")
    return {"env": env, "in_mezzo": in_mezzo, "dati": dati}


def _righe(uscita: str) -> list[str]:
    """Le righe di risposta di `recall`: quelle che cominciano con «- »."""
    return [r.strip() for r in uscita.splitlines() if r.strip().startswith("- ")]


def _elenco(righe: list[str]) -> str:
    return os.linesep.join(righe)


def _forma(riga: str) -> str:
    """La riga con ogni numero ridotto a un segnaposto.

    🔴 I NUMERI VANNO TOLTI, e la prima stesura di questo banco non lo faceva:
    la riga porta il punteggio di somiglianza, diverso per due fatti diversi
    quasi sempre. Confrontando le righe intere, due risposte risultavano
    distinte **anche senza nessuna cura**, cioè la cella sarebbe passata per il
    motivo sbagliato.

    Le due versioni differiscono SOLO per il numero della misura, quindi una
    volta sostituiti tutti i numeri le due righe sono identiche carattere per
    carattere — e l'unica differenza che può restare è ciò che **la porta**
    aggiunge. Nessun ritaglio di testa e coda: meno cose da azzeccare.
    """
    return re.sub(r"[0-9]+(?:[.,][0-9]+)?", "#", riga)


def test_CONTROLLO_la_coppia_e_leggibile_dalla_porta(store):
    """⚠️ SENZA QUESTO le celle sotto possono essere verdi per il motivo
    sbagliato: una ricerca che non trova NIENTE rende zero righe, e «zero» si
    confronta bene con qualunque attesa formulata al ribasso. Qui si pretende
    che la domanda risponda, prima di chiedere che risponda in un certo modo."""
    esito = _cli(store["env"], "recall", DOMANDA, "--include-superseded")
    assert esito.returncode == 0, esito.stderr[-400:]
    assert _righe(esito.stdout), (
        "la domanda non rende niente nemmeno chiedendo anche i superati: le "
        "celle qui sotto non misurerebbero il versionamento, misurerebbero un "
        f"silenzio. {esito.stdout[-600:]}")


def test_la_lettura_di_default_rende_solo_la_versione_piu_recente(store):
    """CELLA 1 — «ti do l'ultima».

    ⚠️ Questa cella ha senso SOLO con due versioni della stessa grandezza. Con
    due grandezze diverse (una mediana e un minimo) due risposte sono la
    risposta giusta, e pretenderne una sola misura il banco, non il prodotto:
    è l'errore che questo file ha già fatto una volta.
    """
    esito = _cli(store["env"], "recall", DOMANDA)
    assert esito.returncode == 0, esito.stderr[-400:]
    righe = _righe(esito.stdout)
    assert len(righe) == 1, (
        f"la lettura di default rende {len(righe)} risposte invece di una: "
        "versionare promette che l'ultima versione è quella servita. "
        + _elenco(righe))
    assert "41.2" in righe[0], (
        "la risposta servita non è la versione più recente della grandezza. "
        + righe[0])


@pytest.mark.xfail(strict=True, reason=(
    "T56: chiedendo anche le versioni superate la porta stampa due righe della "
    "stessa forma — la riga di lettura porta testo, somiglianza e moat e non "
    "nomina `superseded_by`, che pure è nel dizionario dell'SDK. Chi legge "
    "riceve due valori della stessa grandezza e nessuno dei due dichiara di "
    "essere quello vecchio"))
def test_chiedendo_anche_le_superate_si_vede_quale_e_superata(store):
    """CELLA 2 — «te le do tutte, e ti dico quale vale».

    Non pretende una parola precisa: pretende che le due righe **si
    distinguano**. Un test che imponesse la dicitura deciderebbe la forma
    dell'interfaccia al posto di chi la disegna; qui la promessa è che una
    differenza ci sia.
    """
    esito = _cli(store["env"], "recall", DOMANDA, "--include-superseded")
    assert esito.returncode == 0, esito.stderr[-400:]
    righe = _righe(esito.stdout)
    assert len(righe) == 2, (
        f"chiedendo anche le superate le risposte sono {len(righe)} invece di "
        "due: versionare tiene entrambe le versioni. " + _elenco(righe))
    vecchia = [r for r in righe if "33.0" in r]
    nuova = [r for r in righe if "41.2" in r]
    assert vecchia, "la versione superata non torna affatto. " + _elenco(righe)
    assert nuova, "la versione più recente non torna. " + _elenco(righe)
    assert _forma(vecchia[0]) != _forma(nuova[0]), (
        "le due righe sono indistinguibili una volta tolti i numeri: la porta "
        "non dice quale delle due è la versione superata, e chi legge riceve "
        "due valori della stessa grandezza senza un ordine. "
        f"superata: {vecchia[0]} — corrente: {nuova[0]}")


def test_ogni_riga_resa_dice_di_quale_grandezza_parla(store):
    """CELLA 3 — la terza asserzione della promessa, e l'unica che un conteggio
    di righe non può falsificare: due risposte alla stessa domanda sono
    accettabili se ognuna dichiara di che cosa parla.

    📌 LIMITE DICHIARATO, perché chi legge il verde sappia che cosa ha in mano:
    su questa coppia la asserzione è soddisfatta dal **testo dei fatti** — li
    ho scritti io e nominano la grandezza — non da qualcosa che fa la porta.
    Qui presidia il corpus, non il prodotto. Per misurare il prodotto
    servirebbe un fatto che la grandezza NON la nomina e una porta che la
    qualifichi comunque: quel banco non esiste, e finché non esiste questa
    cella dice solo che le due risposte non sono anonime.
    """
    esito = _cli(store["env"], "recall", DOMANDA, "--include-superseded")
    assert esito.returncode == 0, esito.stderr[-400:]
    righe = _righe(esito.stdout)
    assert righe, "nessuna risposta da qualificare. " + esito.stdout[-400:]
    mute = [r for r in righe if GRANDEZZA not in r.lower()]
    assert not mute, (
        f"{len(mute)} righe su {len(righe)} non dicono di quale grandezza "
        "parlano: due numeri diversi per la stessa domanda, e chi legge non sa "
        "se sono due misure o due versioni. " + _elenco(mute))


def test_al_passato_si_riceve_la_versione_che_valeva_allora(store):
    """CELLA 4 — «ti do quella che valeva allora».

    Misurato il 12 settembre: **passa**. Era l'unica cella che avevo lasciato
    senza predizione — il filtro del viaggio nel tempo guarda `asserted_at`,
    che nessuna porta valorizza, e ripiega su `created_at`. Il ripiego regge, e
    questa cella sta qui per accorgersi del giorno in cui smettesse di reggere.
    """
    esito = _cli(store["env"], "recall", DOMANDA,
                 "--as-of", f"{store['in_mezzo']:.3f}")
    assert esito.returncode == 0, esito.stderr[-400:]
    righe = _righe(esito.stdout)
    assert righe, (
        "la lettura al passato non rende niente all'istante in cui la prima "
        f"versione era l'unica scritta. {esito.stdout[-600:]}")
    assert any("33.0" in r for r in righe), (
        "al passato non si riceve la versione che a quell'istante era l'unica "
        "scritta. " + _elenco(righe))
    assert not any("41.2" in r for r in righe), (
        "al passato torna anche la versione scritta DOPO quell'istante: "
        "allora non era ancora vera. " + _elenco(righe))
