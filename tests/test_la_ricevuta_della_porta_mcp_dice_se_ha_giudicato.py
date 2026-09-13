"""README:352 — la riga della tabella «it depends on the port» che ho scritto IO.

IL CLAIM, testuale dal README pubblicato (riga 352, tabella «What gets your
first write judged: it depends on the port»):

    | **MCP server** - `hippo_remember` | the server **delegates to a shared
    encode daemon by construction** and never loads the judge in its own process
    … It starts the daemon itself - but **if the daemon is missing or does not
    come up, the write is stored UNJUDGED**: `stored: true`, and the receipt
    carries `layers: ['L4-skipped']`. **Read that field.** `admitted` on its own
    does not mean judged. |

⚠️ QUESTA RIGA L'HO SCRITTA IO l'08/09 ed è entrata su main con `5ac8d9f1`
**senza nessun presidio**. È la forma che ho denunciato tutto il giorno — una
promessa che nessun test tiene ferma — applicata alla riga che ho aggiunto io.
La prendo prima delle altre per questo: chi mappa i debiti degli altri comincia
dal proprio.

E non è una riga qualsiasi: **dice all'utente quale campo leggere** per sapere
se ciò che ha appena scritto è stato giudicato o no. Se quel campo non arriva a
quella porta, l'utente legge `stored: true` e crede di avere un fatto
verificato mentre ha un `model_claim`.

COME SI PROVA. Non contando le occorrenze del nome: `grep '"layers"'
verimem/mcp_server.py` è **vuoto**, e non vuol dire niente — il payload del tool
è costruito con `_ok({**res, …})` e propaga ciò che gli passa il livello sotto.
Un'assenza si prova ESEGUENDO, e questo file invoca la porta e guarda la
ricevuta che ne esce.

⚠️ ZERO COPIE: `_invoke_tool` è importato da `tests.test_mcp_thin`.

ws7 «Iris», 10/09/2026. Misurato con:
`python -m pytest tests/test_la_ricevuta_della_porta_mcp_dice_se_ha_giudicato.py -q -p no:randomly`
"""
from __future__ import annotations

import json
import pathlib

import pytest

from tests.test_mcp_thin import _invoke_tool

#: Il nome del campo, come il README lo insegna all'utente.
CAMPO = "layers"
#: Il valore che quel campo deve portare quando il giudizio non è girato.
SALTATO = "L4-skipped"  # citato nel docstring, non piu asserito: vedi il test in fondo


async def _ricevuta_di_una_scrittura_con_fonte() -> dict:
    """Scrive dalla porta MCP con una `source` e rende la ricevuta.

    ⚠️ CREDEVO che in un test il giudice non girasse (nessun daemon, embedder
    stub) e che questa fosse la condizione «daemon assente» del README. **La
    misura mi ha smentita**: la ricevuta porta
    `adjudication.judge.model = local_gate_ce_v2` e `evidence_class =
    cross_encoder`, cioè **il giudizio gira davvero**. Lo scrivo qui perché era
    un'assunzione mia, comoda, e non l'avevo verificata: quello che questo file
    prova è l'ASSENZA DEL CAMPO, non il comportamento a daemon spento.
    """
    blocchi = await _invoke_tool(
        "hippo_remember",
        {"proposition": "il capannone 12 misura 400 metri quadri.",
         "topic": "note",
         "source": "Perizia del 2026-03-04: il capannone 12 misura 400 mq."},
    )
    return json.loads(blocchi[0])


# ── IL CONTROLLO POSITIVO PER PRIMO ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_CONTROLLO_la_porta_risponde_e_la_ricevuta_ha_un_corpo(tmp_data_dir):
    """Una ricevuta vuota o un errore soddisfano ogni asserzione «non c'è X»."""
    ricevuta = await _ricevuta_di_una_scrittura_con_fonte()
    assert isinstance(ricevuta, dict), f"la porta non ha reso un oggetto: {ricevuta!r}"
    assert ricevuta, "la porta ha reso una ricevuta VUOTA"
    assert not ricevuta.get("error"), (
        f"la scrittura dalla porta MCP è fallita: {ricevuta.get('error')!r}. "
        "Questo test non può dire niente sul campo della ricevuta se la "
        "scrittura non è avvenuta."
    )


# ── LA PROMESSA: «Read that field» ──────────────────────────────────────────


#: I nomi che README:352 insegna a LEGGERE nella ricevuta di `hippo_remember`,
#: presi dalla riga stessa: «`stored: true`, and the receipt carries
#: `layers: ['L4-skipped']`. **Read that field.** `admitted` on its own does not
#: mean judged.»
#:
#: ⚠️ `hippo_remember` sta nella stessa riga fra backtick ma e' il NOME DELLA
#: PORTA, non un campo della ricevuta: sta fuori di proposito.
NOMI_CHE_LA_RIGA_INSEGNA = frozenset({"stored", CAMPO, "admitted"})

#: Il README letto dalla radice del repo: serve al controllo positivo in fondo.
_README = pathlib.Path(__file__).resolve().parents[1] / "README.md"

#: Quelli che la ricevuta NON rende come chiave di primo livello, misurati il
#: 13/09/2026 invocando la porta (le 16 chiavi vere sono nel messaggio d'errore
#: qui sotto, non in un ricordo).
#:
#: 🔴 SONO TUTTI E TRE — e il difetto registrato il 10/09 ne contava UNO.
#: Cercavo `layers` perche' era il campo che la riga dice di leggere, e non ho
#: guardato gli altri due che la STESSA riga nomina. `admitted` esiste, ma come
#: VALORE dentro `adjudication.disposition`, non come campo: un utente che
#: segue la riga cerca tre nomi e non ne trova nessuno.
NON_RESI_IL_13_09 = frozenset({"stored", "layers", "admitted"})


@pytest.mark.asyncio
async def test_quali_nomi_della_riga_la_ricevuta_non_rende(tmp_data_dir):
    """🔴 Il difetto e' APERTO e questo test lo REGISTRA. Cade nei DUE versi.

    ⚙️ ERA UN `xfail(strict=True)` su `layers` solo. Convertito il 13/09 alla
    forma decisa il 12/09 — «un test misura e resta, o si toglie con la ragione»
    — e nel convertirlo il difetto si e' rivelato TRE VOLTE piu' grande: un
    `xfail` chiede «il campo c'e'?» e si accontenta del no; un cricchetto chiede
    «quali mancano?» e deve elencarli, e l'elenco ha fatto la differenza.

    🟢 Se l'insieme si ACCORCIA, un nome e' arrivato alla porta: togli quel nome
       da `NON_RESI_IL_13_09` nello stesso commit; a zero, questo presidio
       diventa positivo e il docstring perde il paragrafo del difetto.
    🔴 Se si ALLUNGA, la ricevuta ha perso un campo che la pagina promette.

    PER L'UTENTE: chi segue README:352 cerca tre nomi nella ricevuta e non ne
    trova nessuno, quindi non ha modo di sapere se la scrittura e' stata
    giudicata — che e' esattamente cio' che quella riga dice di NON fare.

    LA CURA E' SUL README, non sul prodotto: `judged` e' il campo giusto e c'e'
    gia' (lo presidia il test qui sotto). Ma la riga non si riscrive a occhio:
    serve la misura nella condizione che descrive — daemon assente — che qui NON
    e' riprodotta (in questo test il giudice gira:
    `adjudication.judge.model = local_gate_ce_v2`). Una riga di documentazione
    corretta a occhio e' come e' nato questo difetto.
    """
    ricevuta = await _ricevuta_di_una_scrittura_con_fonte()

    # Controllo positivo: se la ricevuta tornasse vuota, ogni «manca» sarebbe
    # vero per la ragione sbagliata e questo test misurerebbe il nulla.
    assert ricevuta, "la porta non ha reso nessuna ricevuta: il presidio non misura"

    non_resi = frozenset(n for n in NOMI_CHE_LA_RIGA_INSEGNA if n not in ricevuta)
    assert non_resi == NON_RESI_IL_13_09, (
        "i nomi che README:352 insegna a leggere e che la ricevuta non rende "
        "sono cambiati.\n"
        f"  oggi     : {sorted(non_resi)}\n"
        f"  il 13/09 : {sorted(NON_RESI_IL_13_09)}\n"
        f"  arrivati : {sorted(NON_RESI_IL_13_09 - non_resi)}\n"
        f"  persi    : {sorted(non_resi - NON_RESI_IL_13_09)}\n"
        f"  chiavi rese dalla porta: {sorted(ricevuta)}\n"
        "**Guarda la riga e la porta, non aggiornare l'elenco.**"
    )


def test_CONTROLLO_la_riga_del_readme_insegna_ANCORA_quei_tre_nomi():
    """Il presidio sopra confronta con una riga che potrebbe essere riscritta.

    Se il README cambia quella riga, l'elenco qui sopra smette di descrivere una
    promessa viva e il suo rosso non vorrebbe piu' dire niente. Questo lo dice
    invece di lasciarlo passare — ed e' la meta' che un `xfail` non poteva avere,
    perche' l'`xfail` guardava la porta e mai la pagina.
    """
    testo = _README.read_text(encoding="utf-8", errors="replace")
    i = testo.find("Read that field")
    assert i > 0, (
        "README:352 non contiene piu' «Read that field»: la riga presidiata e' "
        "stata riscritta o tolta. Se e' stata CURATA, riscrivi questo presidio; "
        "se e' stata solo spostata, aggiorna il frammento."
    )
    riga = testo[max(0, i - 700) : i + 120]
    mancanti = sorted(n for n in NOMI_CHE_LA_RIGA_INSEGNA if f"`{n}" not in riga)
    assert not mancanti, (
        f"la riga non nomina piu' {mancanti}: insegnava tre campi il 13/09 e "
        "l'elenco qui sopra e' misurato su quei tre. Se la riga e' stata "
        "riscritta con i nomi giusti, il difetto e' curato e i due presidi qui "
        "vanno girati insieme."
    )


# ── E IL CAMPO CHE C'È DAVVERO, perché il README possa essere riscritto ─────


@pytest.mark.asyncio
async def test_la_ricevuta_dice_SE_HA_GIUDICATO_con_il_campo_judged(tmp_data_dir):
    """La porta MCP la risposta ce l'ha: si chiama `judged`, non `layers`.

    Questo test non presidia una riga del README — presidia il campo su cui
    quella riga andrà RISCRITTA. Serve a due cose: che `judged` non sparisca
    mentre aspetto la misura per correggere il testo, e che chi riscrive la riga
    abbia il nome giusto misurato invece che scelto a occhio.

    ⚠️ Qui NON asserisco il valore. In questo test il giudice gira davvero
    (`adjudication.judge.model` = `local_gate_ce_v2`), quindi `judged` è vero e
    non dice niente sul caso «daemon assente» che il README descrive. Quel caso
    e' di ws5 (T26a/a) e la misura è sua: un'asserzione sul valore, qui,
    proverebbe una condizione che non ho riprodotto.
    """
    ricevuta = await _ricevuta_di_una_scrittura_con_fonte()
    assert "judged" in ricevuta, (
        "la porta MCP non rende nemmeno `judged`: allora l'utente non ha NESSUN "
        f"campo per sapere se la scrittura è stata giudicata. Chiavi: {sorted(ricevuta)}"
    )
    assert isinstance(ricevuta["judged"], bool), (
        f"`judged` non è un booleano ma {type(ricevuta['judged']).__name__}: "
        "un campo che si legge come sì/no deve essere sì/no."
    )
