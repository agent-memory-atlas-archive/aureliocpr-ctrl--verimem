# 2026-09-13 — un worktree ha perso 493 file tracciati, e fra questi il cancello che controlla i commit

* **Cosa** — dopo una notte a PC spento, un worktree sotto `%TEMP%` ha ripreso
  con **493 file tracciati cancellati** e zero modificati. Fra i cancellati
  c'erano `.githooks/pre-commit`, `.githooks/pre-push`, tre workflow di CI,
  `Dockerfile`, `LICENSE`, `Makefile`. Un commit fatto in quello stato è
  passato **senza il gate del lint**: nell'uscita mancava la riga
  `pre-commit: lint clean` e c'era solo `prepare-commit-msg`.

  ```
  git status --porcelain | grep '^ D' | wc -l   →  493
  git status --porcelain | grep -c '^ M'        →    0
  ```

* **Classe** — **sensore scollegato**. Il cancello non ha detto di no e non si
  è lamentato: non c'era. Un presidio assente dal disco non emette nessun
  segnale, e l'unico indizio è stato che *mancava una riga che di solito c'è*.

* **Causa** — la pulizia di `%TEMP%` a sistema spento rimuove file dal
  worktree. Git li vede come cancellati nell'albero di lavoro, non nell'indice,
  quindi nessun comando fallisce e nessun avviso compare. Gli **hook sono file
  tracciati come gli altri**: sparendo, smettono di girare in silenzio.

* **Cura** — `git ls-files -d -z | xargs -0 git checkout --` ha ripristinato
  tutti e 493 i file; il lint è stato ripassato a mano sul commit
  (`All checks passed!`). Nel prodotto **nessuna cura**: il difetto è nella
  posizione del worktree, non nel codice. I worktree si creano d'ora in poi
  sotto `~/Code/worktrees/<ws>/`, fuori da `%TEMP%`.

* **Controllo** — **nessuno**, ed è un debito che va detto: niente fallisce da
  solo se gli hook spariscono di nuovo. Il controllo minimo che chiuderebbe il
  buco è una riga all'inizio del lavoro — `test -x .githooks/pre-commit` — che
  si lamenta invece di lasciar committare senza gate. Finché non c'è, dopo ogni
  riavvio `git status` va letto **anche** per i file che non sono i propri.

* **Owner** — ws2 (Porte) tiene il debito del controllo mancante.

---

📌 Una cosa è andata bene per disciplina e non per fortuna, e vale come nota:
il commit fatto in quello stato conteneva **solo il file voluto**
(`1 file changed, 26 insertions, 5 deletions`), perché era stato fatto con
`git add <file>` e non con `git commit -a`. Con 493 cancellazioni in albero, un
`-a` le avrebbe portate tutte su un ramo condiviso. La regola del pathspec
(«committa col pathspec», registro delle trappole della copia condivisa) è
servita esattamente qui.
