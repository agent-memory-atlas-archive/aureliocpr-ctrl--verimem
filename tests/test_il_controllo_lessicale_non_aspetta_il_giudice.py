"""T80 — il controllo sui NUMERI non ha bisogno del giudice, ma oggi lo aspetta.

IL DIFETTO, letto nel codice
-----------------------------
`anti_confab_gate`, nel ramo della fonte::

    if gscore is None:
        _emit_l4_skipped()          # <- e basta
    else:
        grounding_val = float(gscore)
        …
        # L4.1 — IL CONTROLLO DETERMINISTICO CHE MANCAVA

`L4.1` confronta i **numeri del claim** con quelli della **fonte**: è lessicale,
non chiama nessun modello, e gli servono soltanto le due stringhe che ha già in
mano. Eppure vive dentro il ramo `else`, cioè **solo quando il giudice ha dato
un punteggio**.

⇒ Mentre il giudice carica — `judge_state()` «warming», il caso di ogni prima
scrittura su una macchina fredda — la scrittura entra con l'avviso onesto
`L4-skipped`, **e nessuno guarda i numeri**. Un valore inventato passa, e passa
proprio nella finestra in cui l'utente è più esposto: la prima volta che usa il
prodotto.

🔑 **Non è il moat che manca: è un controllo che NON dipende dal moat, messo
dietro il moat.** L'avviso dice il vero — «entailment NOT verified» — ma dice
meno di quanto il prodotto potrebbe sapere in quel momento.

LA FORMA DEL BANCO
------------------
Tre celle a **una variabile sola**, il giudice:

* giudice ASSENTE + numero inventato → **oggi ammesso senza `L4.1`** ← il rosso
* giudice PRESENTE + lo stesso numero → `L4.1` c'è  ← prova che il caso è reale
* giudice ASSENTE + numeri che la fonte CONTIENE → nessun `L4.1`  ← prova che la
  cura non è «segnala sempre»

Senza la seconda, il rosso potrebbe essere un claim mal costruito invece di un
buco. Senza la terza, una cura che accendesse `L4.1` a ogni scrittura
passerebbe.

⚠️ Nessuna delle tre carica un modello: il giudice è reso indisponibile
esattamente come lo rende il prodotto quando non riesce a dare un punteggio.
"""
from __future__ import annotations

import verimem.grounding_gate as gg
from verimem.anti_confab_gate import run_validation_gate

#: La fonte parla di 500 e 540. Di megabyte non dice niente.
FONTE = ("verbale: la coda aveva 500 elementi\n"
         "rettifica: la coda aveva 540 elementi\n")

#: La metà verbatim tiene alto il giudice quando c'è; il dettaglio con unità è
#: quello che la fonte TACE, cioè la classe che `L4.1` esiste per prendere.
CLAIM_CON_NUMERO_INVENTATO = "La coda ha 540 elementi e occupa 176 MB."

#: Stessa forma, ma ogni numero è nella fonte.
CLAIM_SENZA_NUMERI_NUOVI = "La coda ha 540 elementi, prima ne aveva 500."


def _cancello(claim: str):
    return run_validation_gate(
        proposition=claim, verified_by=None, topic="t/porte", agent=None,
        validate="full", source=FONTE, grounding_llm=object())


def _strati(res) -> list[str]:
    return sorted({str(w.get("layer", "")) for w in (res.warnings or [])})


def _senza_giudice(monkeypatch) -> None:
    """Il giudice non riesce a dare un punteggio: è lo stato «warming».

    Si sostituisce il simbolo che il punto di chiamata risolve — l'import è
    tardivo dentro `run_validation_gate`, quindi conta l'attributo del modulo.
    """
    monkeypatch.setattr(gg, "fact_grounding_score_ex", lambda *a, **k: (None, None))


def _con_giudice(monkeypatch, punteggio: float = 99.9) -> None:
    monkeypatch.setattr(gg, "fact_grounding_score_ex",
                        lambda *a, **k: (punteggio, "local"))


def test_CONTROLLO_col_giudice_il_numero_inventato_viene_visto(monkeypatch) -> None:
    """Il caso è reale: con il giudice presente `L4.1` lo prende.

    Se questa cella cade, il rosso qui sotto non dimostra un buco: dimostra che
    il claim è costruito male. Va letta PRIMA dell'altra.
    """
    monkeypatch.setenv("ENGRAM_GROUNDING_WRITE", "1")
    _con_giudice(monkeypatch)
    strati = _strati(_cancello(CLAIM_CON_NUMERO_INVENTATO))
    assert any(s.startswith("L4.1") for s in strati), (
        f"con il giudice presente il numero inventato NON viene segnalato "
        f"(layer: {strati}): il claim non serve a misurare il buco, "
        f"riformulalo invece di rilassare l'altra cella")


def test_senza_giudice_il_numero_inventato_passa_SENZA_essere_guardato(
        monkeypatch) -> None:
    """IL ROSSO. Stesso claim, stessa fonte: cambia solo che il giudice carica.

    Oggi la scrittura entra con `L4-skipped` e **nessun `L4.1`**: il controllo
    sui numeri non è stato saltato perché non poteva decidere — è stato saltato
    perché sta dietro a chi non poteva decidere.
    """
    monkeypatch.setenv("ENGRAM_GROUNDING_WRITE", "1")
    _senza_giudice(monkeypatch)
    strati = _strati(_cancello(CLAIM_CON_NUMERO_INVENTATO))

    assert "L4-skipped" in strati, (
        f"il giudice non risulta assente (layer: {strati}): il banco non sta "
        f"misurando la finestra del riscaldamento, e il verdetto qui sotto non "
        f"vale")
    assert any(s.startswith("L4.1") for s in strati), (
        f"IL BUCO: senza giudice il numero che la fonte non contiene entra "
        f"SENZA che nessuno lo guardi (layer: {strati}). `L4.1` e' lessicale e "
        f"in quel momento ha gia' in mano tutto cio' che gli serve — la fonte "
        f"e la proposizione. Sta dietro al moat solo per come e' scritto il "
        f"ramo, non perche' dipenda dal moat.")


def test_CONTROLLO_senza_FONTE_non_cambia_niente(monkeypatch) -> None:
    """🔴 IL CONFINE VERO DELLA CURA, e nel banco mancava (rilievo del pari).

    `L4.1` confronta i numeri del claim con quelli della **fonte**. Se la cura
    venisse scritta come «fai girare i controlli lessicali comunque» invece di
    «falli girare ogni volta che c'e' una FONTE», una scrittura senza fonte
    confronterebbe i suoi numeri con il nulla — e da lì **ogni numero risulta
    assente**.

    ⚠️ E non e' un timore teorico: dentro quella testa lessicale c'e' anche
    `L4.1-ambiguo`, che guarda **solo la proposizione** (`numeri_ambigui`) e non
    ha nessuna fonte da consultare. Su una scrittura senza fonte si
    accenderebbe da sola.

    ⇒ Sarebbe **l'unico modo in cui questa cura puo' fare un danno grosso**:
    quarantinare in massa le scritture ordinarie che oggi entrano
    legittimamente come non verificate. Questa cella lo rende impossibile, e
    deve passare **prima e dopo** la cura.
    """
    monkeypatch.setenv("ENGRAM_GROUNDING_WRITE", "1")
    _senza_giudice(monkeypatch)
    res = run_validation_gate(
        proposition=CLAIM_CON_NUMERO_INVENTATO, verified_by=None,
        topic="t/porte", agent=None, validate="full", source=None,
        grounding_llm=object())
    strati = _strati(res)
    assert not any(s.startswith("L4.1") for s in strati), (
        f"una scrittura SENZA FONTE viene segnalata dai controlli lessicali "
        f"(layer: {strati}): non c'e' nessuna fonte con cui confrontare i "
        f"numeri, quindi «assente dalla fonte» non vuol dire niente. Una cura "
        f"che accende quei controlli fuori dal ramo della fonte quarantina in "
        f"massa le scritture ordinarie.")


def test_CONTROLLO_senza_giudice_i_numeri_della_fonte_NON_si_segnalano(
        monkeypatch) -> None:
    """L'altra faccia: la cura non deve diventare «segnala sempre».

    Un claim i cui numeri stanno tutti nella fonte non deve produrre `L4.1`
    nemmeno a giudice spento. Senza questa cella, accendere il layer su ogni
    scrittura passerebbe per cura.
    """
    monkeypatch.setenv("ENGRAM_GROUNDING_WRITE", "1")
    _senza_giudice(monkeypatch)
    strati = _strati(_cancello(CLAIM_SENZA_NUMERI_NUOVI))
    assert not any(s.startswith("L4.1") for s in strati), (
        f"un claim i cui numeri sono TUTTI nella fonte viene segnalato lo "
        f"stesso (layer: {strati}): il controllo non distingue piu' le due "
        f"popolazioni, e un avviso che si accende sempre non informa nessuno")
