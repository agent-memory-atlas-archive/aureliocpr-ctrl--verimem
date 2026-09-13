# 2026-09-13 — un backtick dentro un testo ha eseguito `git stash` in un repo condiviso

* **Cosa** — un testo destinato al canale è stato passato a uno script tramite
  un **heredoc non quotato** (`<<PY`). Il testo conteneva backtick: la shell li
  ha **eseguiti** prima che Python vedesse una riga. Uno di quei comandi era
  `git stash`, e ha nascosto il lavoro non committato di un'altra sessione su
  `engram-orchestrator`, ramo `syn-loop-fixes` — 16 file tracciati.

  ```
  stash@{0} ecf3987c  WIP on syn-loop-fixes: b095254 …
  ```

* **Classe** — **rosso vero** sull'ambiente, non sul prodotto: si riproduce a
  comando. Un heredoc `<<PY` interpola; `<<'PY'` no. La differenza è un apice.

* **Causa** — la regola esisteva ed era nota («i testi si scrivono con Write,
  mai con heredoc: i backtick vengono eseguiti»), ma era stata applicata **solo
  a metà del suo perimetro**: ai testi da *inviare*, non a quelli da
  *aggiornare*. Una regola applicata a metà non protegge la metà che manca.
  ⚠️ Il ramo stashato era fermo su un commit che documenta **questo stesso
  incidente** avvenuto il 2026-09-04 con `pip install`: la lezione c'era, in
  quel punto esatto, e non ha impedito la ripetizione.

* **Cura** — ripristino verificato, non presunto: `git stash apply ecf3987c`
  (per SHA, mai per indice), `git diff --stat ecf3987c` **vuoto** cioè albero
  identico, poi `git stash drop` ritrovando la propria voce per SHA. La voce di
  un'altra sessione, più vecchia, non è stata toccata. Regola adottata per
  tutte le istanze: **heredoc solo quotato**, e **mai `git stash` nel repo
  condiviso** — lo stash stack è unico per tutti i worktree e tutte le sessioni.

* **Controllo** — il sostituto del `git stash` è un **worktree usa-e-getta più
  `git revert --no-commit <sha>`**: isola *una* variabile invece di tutto il
  lavoro non committato, i due alberi coesistono quindi il confronto non dipende
  dall'ordine, e non tocca nessun altro. È già stato usato per la falsificazione
  di T56 e i due bracci sono nel canale. **Controllo automatico: nessuno** — un
  heredoc non quotato non è distinguibile a posteriori, e questo resta un debito.

* **Owner** — ws2 (Porte) tiene il debito del controllo mancante.
