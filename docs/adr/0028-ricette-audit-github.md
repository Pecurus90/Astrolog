# 0028 -- Le ricette, gli audit e GitHub

**Stato:** accettata, 20/10/2026 (Marco). Proposta completa e fonti:
https://claude.ai/artifact/1MAiuNUQdKeLtdEyEz8LHD. Completa ADR 0015, 0025 e 0027.

## Contesto

Le ricette di ADR 0015 mandano in `docs/coda.md` cio' che non si ripara (`/rivedi`, passo 4); il
check di salute del 20/10 ha prodotto una lista. ADR 0027 toglie la coda. GitHub: `main` senza
protezione, CodeQL spento, aggiornamenti di sicurezza di Dependabot spenti, due proposte di
Dependabot aperte dal 30/9 e dal 14/10 senza che nessuno le guardi; il frontend fuori da Dependabot.

## Decisione

- **Ogni rilievo confermato** (revisore, `/rivedi`, audit): `/ripara` subito, Issue `bloccato`
  se bloccato da fuori, o "no" col motivo scritto. Massimo 5 rilievi per revisore o settore, ognuno
  con prova; un verificatore separato prova a smentirli.
- **Ricette nuove**: `/salute` (workflow, sei auditori per settore piu' un verificatore) a fine
  tappa e prima di un rilascio, non a calendario; `/audit <settore>` (sicurezza, test,
  prestazioni, dipendenze, documenti, accessibilita'); `/smista` a inizio sessione (Issue,
  Dependabot, avvisi, CI rossa); `/porta-tavola` (ADR 0025); `/rilascia` scritta, ferma fino al
  primo rilascio. Il revisore segnala solo errori di correttezza o di requisito.
- **Convenzioni e completezza, in ogni ricetta** (Marco 20/10; regola in CLAUDE.md, principio 1):
  ogni numero, soglia e formula, anche gia' in codice, si verifica su una convenzione pubblica con
  fonte citata; un lavoro senza ne' l'una ne' l'altra lo dice in una riga. Cio' che riprende un
  software esterno si confronta con la sua documentazione: parziale, si mostra a Marco cosa manca. Coincide: resta.
  Diverge: ci si ferma e si mostra a Marco cosa fa il codice, cosa dice la convenzione e quanto
  cambia su un esempio; decide lui. Nessuna convenzione: il numero lo sceglie Marco.
- **Audit automatico su GitHub** (Claude Code GitHub Action, Marco 20/10): ogni settimana; se dal
  giro prima il codice non e' cambiato si ferma senza chiamare Claude; se e' cambiato, un settore a
  rotazione sui soli file cambiati. Ogni rilievo con prova apre una Issue `difetto`, che `/smista`
  ripara alla sessione dopo. Si installa con `/install-github-app` (Marco).
- **Dependabot**: una proposta con la CI verde la unisco io, come un commit; rossa diventa un
  `/ripara`. Frequenza mensile, frontend compreso.
- **GitHub**: ruleset su `main` (niente force push, niente cancellazione, nessun obbligo di PR);
  CodeQL di default; aggiornamenti di sicurezza di Dependabot; segnalazioni private di
  vulnerabilita'; etichette `difetto`, `bloccato`, `sicurezza`, `domanda`; due moduli (problema,
  idea), niente Issue in bianco. Milestone, Releases e Discussions al primo rilascio; Projects e
  claude-code-action no.
- **Ordine** (ADR 0027): difetti rimasti, GitHub, coda smontata e tetti, ricette, documenti,
  codice, un `/salute` finale; poi il porting.

## Conseguenze

- `.claude/commands/rivedi.md` e `ripara.md` cambiano; nascono `salute`, `audit`, `smista`,
  `porta-tavola`, `rilascia`.
- Misura (ADR 0025): `fix:` dopo lo sguardo di Marco per fetta; commit di soli documenti sotto un
  quarto.
