# 0025 -- Uno studio per ruoli: la pagina si collauda contro la tavola prima di Marco

**Stato:** accettata, 20/10/2026 (Marco, dal check di salute). Allarga ADR 0015: ricette, un giro
di revisione e le macchine al posto dei prompt restano. Superata in gran parte da ADR 0040: tolti
`verificatore-disegno`, modo `pagina`, `tools/contratti.py`, **Supera** obbligatoria, misura `fix:`
per fetta; `collaudatore` al passo 29 del piano. Resta il giro della fetta, base di `/porta-tavola`.

## Contesto

Check di salute del 20/10/2026 (sei audit in sola lettura). Il metodo di ADR 0015 ha retto sul
codice: lotti da 0,1-0,9 M token, nessun revert in 300 commit. Non ha retto attorno al codice:
- i difetti a schermo li trova Marco: Meteo 7 `fix:` di fila sulle tavole v37.1-v37.3 (14/10),
  Dashboard 5 `feat:` e 8 `fix:` in un giorno (16/10). Nessuno confronta la pagina con la tavola
  prima di lui;
- nessuna ricetta per portare una tavola di Design; `porting-fedele` parla ancora di pagine da
  `old/src`;
- il vocabolario non lo controlla nessuna macchina sui documenti («bersaglio», «pose» nelle
  brief e negli ADR, 20/10/2026);
- le consegne di Design si verificano a mano, senza lista (FWHM px/″ invertiti, 20/10/2026);
- la sessione principale fa tutto: 125 commit `docs:` su 300.

## Decisione

| Ruolo | Chi | Cosa fa |
|---|---|---|
| Prodotto | Marco | Testi, soglie, tavole, rischio; guarda a schermo |
| Disegno | Claude Design | Tavole e `docs/COMPONENTI.md` |
| Capo progetto e dominio | sessione principale, Opus | Piano, contratti, ADR, backend coi test rossi, coordina |
| Verificatore del disegno | agente `verificatore-disegno`, Sonnet, DesignSync | Ogni consegna contro una lista fissa: brief punto per punto, glossario, soglie con fonte, numeri contro gli ADR, unita' |
| Integratore delle pagine | `sviluppatore` modo `pagina`, Opus | La tavola in React coi componenti comuni, chiavi i18n, tipi generati; nessun calcolo |
| Revisore, auditore | come oggi | Un giro; le promesse eseguite |
| Collaudatore | agente `collaudatore`, Opus, Chrome | App isolata contro le catture della tavola: pieno, vuoto, "non so", telefono, console. **Prima di Marco** |
| Esploratore, traduttore | come oggi | -- |
| Guardiani | macchine in pre-commit | Glossario, contratti, frasi superate, coda senza voci fatte |

**Il giro di una fetta di porting:**
1. **Tavola congelata**: il verificatore controlla la consegna, Marco approva una versione;
   durante la fetta non si muove.
2. Piano corto; a Marco solo testi e soglie nuove, a scelta multipla.
3. Backend: test rossi, logica, rotta, tipi generati.
4. Pagina: l'integratore, solo coi componenti comuni.
5. Controlli, revisore, auditore (ADR 0015).
6. Collaudatore; le differenze le ripara chi ha scritto, una verifica.
7. Marco a schermo.
8. Traduzione, guida, commit e push; sessione nuova per la fetta dopo.

**La misura del metodo**: per fetta, quanti `fix:` arrivano dopo lo sguardo di Marco. Sostituisce
la tabella per lavoro di ADR 0015 (superata: vedi 0040).

## Conseguenze

- Nascono `.claude/agents/verificatore-disegno.md`, `.claude/agents/collaudatore.md`, il modo
  `pagina` dello `sviluppatore` e un comando per portare una tavola; la parte "pagine" di
  `porting-fedele` esce (superata in parte: vedi 0040).
- Nascono `tools/glossario.py` (la colonna «non si dice» contro testi, brief e documenti, con
  `<!-- glossario-ok -->` per le citazioni) e `tools/contratti.py` (ogni test citato in un
  contratto esiste). La riga **Supera** diventa obbligatoria in un ADR che cambia un contratto.
  (superata: vedi 0040; `tools/glossario.py` al passo 26 del piano.)
- Il confronto automatico delle catture (Playwright) sarebbe una dipendenza di sviluppo: si
  chiede a Marco quando serve.
