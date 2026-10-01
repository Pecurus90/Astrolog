export const meta = {
  name: 'esegui',
  description: 'Build a planned task, review and fix until no defect is left, audit by running, checks green',
  whenToUse: 'After the plan and Marco\'s answers. args: {task, plan, mode: "meccanico"|"spostamento"|"logica", surface: bool, answers: [string], history: [string], parked: [string]}',
  phases: [
    { title: 'Build' },
    { title: 'Review' },
    { title: 'Audit' },
    { title: 'Checks' },
  ],
}

// Review rounds go on until one finds no defect; the caps only stop a runaway.
const MAX_REVIEW_ROUNDS = 10
const MAX_CYCLES = 3
const HARDENING = 'irrobustimento'

const FINDINGS = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          file: { type: 'string' },
          line: { type: 'integer' },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          kind: { type: 'string', enum: ['difetto', HARDENING] },
          problem: { type: 'string' },
          fix: { type: 'string' },
        },
        required: ['file', 'problem', 'severity', 'kind'],
      },
    },
  },
  required: ['findings'],
}

const WORK = {
  type: 'object',
  properties: {
    files: { type: 'array', items: { type: 'string' } },
    done: { type: 'array', items: { type: 'string' } },
    rejected: { type: 'array', items: { type: 'string' } },
    repeated: { type: 'array', items: { type: 'string' } },
    checks: { type: 'string' },
    question: { type: ['string', 'null'] },
  },
  required: ['files', 'checks', 'question'],
}

const VERDICT = {
  type: 'object',
  properties: {
    holds: { type: 'boolean' },
    ran: { type: 'string' },
    issues: { type: 'array', items: { type: 'string' } },
  },
  required: ['holds', 'ran', 'issues'],
}

const CHECKS = {
  type: 'object',
  properties: {
    all_passed: { type: 'boolean' },
    failed: { type: 'array', items: { type: 'string' } },
  },
  required: ['all_passed', 'failed'],
}

const answers = (args.answers || []).map((a) => `- ${a}`).join('\n')
const task =
  `COMPITO:\n${args.task}\n\nPIANO:\n${args.plan}` +
  (answers ? `\n\nRISPOSTE DI MARCO (valgono, non si richiedono):\n${answers}` : '')
// "logica": the main session built it before launching; fixes go to an agent on the session model.
const fixer = args.mode === 'logica' ? undefined : 'sviluppatore'
// "spostamento" (move, rename, fix imports): no judgment, so the cheaper model.
const fixerModel = args.mode === 'spostamento' ? 'sonnet' : undefined
const QUESTION_RULE =
  'Se per andare avanti serve una decisione che dipende da Marco (gusto, dati suoi, rischio che ' +
  'accetta), NON decidere: metti in `question` la domanda a scelta multipla con la consigliata ' +
  '(la piu corretta, anche se costa piu lavoro) e fermati. Un difetto non e una domanda: si ripara.'
const DOCS_RULE =
  'I documenti vanno nello stesso diff: docs/guida-utente.md se cambia cio che l utente vede, ' +
  'il contratto in docs/domini/, docs/coda.md (chiuso -> sparisce; debito nuovo -> Parcheggio), ' +
  'un ADR in docs/adr/ per una decisione nuova, lo schema in backend/astrolog/schema.sql. ' +
  'Ogni file nuovo: `git add -N <file>`, senno revisione e controlli non lo vedono.'

// Survives a relaunch after a question, so repeats are still recognised.
const history = [...(args.history || [])]
const resuming = history.length > 0
const rejected = []
// Hardening the reviewers proposed: not built, the main session parks it in docs/coda.md.
// Carried across a relaunch like history, so nothing parked before a question is lost.
const parked = [...(args.parked || [])]
let rounds = 0
const end = (status, extra) => ({ status, review_rounds: rounds, rejected_findings: rejected, parked, history, ...extra })
// A question after Build leaves a mark in history, so the relaunch knows not to build again.
const stop = (where, question) => {
  if (where !== 'build') history.push(`domanda (${where}): ${question}`)
  return end('question', { where, question })
}
const failed = (where) => end('failed', { where })

if (!['meccanico', 'spostamento', 'logica'].includes(args.mode)) return failed(`mode: ${args.mode}`)

const KIND_RULE =
  'Ogni rilievo dichiara `kind`. `difetto`: il diff fa una cosa sbagliata, dice il falso (codice, ' +
  'commento o documento), viola una regola del progetto o del compito, manca qualcosa che il ' +
  'compito chiedeva, contiene roba che il compito non chiedeva, o un caso che puo capitare oggi ' +
  'fallisce in silenzio. `irrobustimento`: una cosa da aggiungere che il diff non ha, cioe una ' +
  'protezione contro un caso che oggi non puo capitare, un miglioramento che nessuno ha chiesto, un ' +
  'doppione che c era gia prima del diff o un debito da una fase successiva. Roba non chiesta gia ' +
  'nel diff, o un doppione che il diff introduce, e difetto, non irrobustimento. Nel dubbio fra i ' +
  'due, difetto.'

const REVIEWERS = [
  { type: 'revisore', what: 'le regole di AstroLog del tuo file di agente (anche i controlli che nessuna macchina fa piu), se fa quello che il compito chiede e nient altro, e se i documenti nel diff dicono il vero' },
  { type: 'pr-review-toolkit:code-reviewer', what: 'bug e qualita del codice' },
  { type: 'pr-review-toolkit:comment-analyzer', what: 'commenti: al massimo due righe, in inglese, solo il perche; niente cronaca, date, misure o mappe di file; la docstring di una rotta API fa eccezione (e il contratto OpenAPI)' },
  { type: 'pr-review-toolkit:silent-failure-hunter', what: 'errori inghiottiti e fallback silenziosi' },
  { type: 'pr-review-toolkit:pr-test-analyzer', what: 'test mancanti, test tolti, o test che non si romperebbero se la regola si rompe' },
]

// Applies a fixer's answer; returns an end state, or null to carry on.
function absorb(fixed, where) {
  if (!fixed) return failed(where)
  rejected.push(...(fixed.rejected || []))
  history.push(
    ...(fixed.done || []).map((d) => `riparato (${where}): ${d}`),
    ...(fixed.rejected || []).map((d) => `scartato (${where}): ${d}`),
  )
  if (fixed.question) return stop(where, fixed.question)
  // A finding back after its round means the task itself is wrong: the owner decides.
  if ((fixed.repeated || []).length) {
    return stop(where, `La revisione ripropone rilievi gia trattati: ${fixed.repeated.join(' | ')}`)
  }
  return null
}

const REPEAT_RULE =
  'In `repeated` metti quelli che ripropongono, anche con altre parole, un rilievo gia riparato o ' +
  'scartato in un giro precedente, e non toccarli. Degli altri applica'

const fix = (where, what, repeatRule = REPEAT_RULE) =>
  agent(
    `${task}\n\n${what}\n\n` +
      (history.length ? `Giri precedenti:\n${history.join('\n')}\n\n` : '') +
      `Verifica ognuno sul codice. ${repeatRule} ` +
      'i fondati (in `done`) e scarta gli infondati col perche (in `rejected`). ' +
      `${DOCS_RULE} Poi rilancia pre-commit sui file toccati e i test. ${QUESTION_RULE}`,
    { phase: where.split(' ')[0], label: `fix:${where}`, schema: WORK, agentType: fixer, model: fixerModel },
  )

// After `fix`: a const cannot be called before its declaration has run.
// A relaunch after a question finds the work already in the diff: building again would undo fixes.
if (args.mode !== 'logica' && !resuming) {
  phase('Build')
  const built = await agent(
    `${task}\n\nCostruisci il compito; se il diff ne contiene gia una parte, continua da li. ${DOCS_RULE} ` +
      'Poi lancia `python -m pre_commit run --files <file toccati>` e i test toccati. Non committare. ' +
      QUESTION_RULE,
    { phase: 'Build', schema: WORK, agentType: 'sviluppatore', model: fixerModel },
  )
  if (!built) return failed('build')
  if (built.question) return stop('build', built.question)
} else if (resuming) {
  // The question may have stopped a fix half-way: only Marco's answer goes into the diff.
  phase('Review')
  const resumed = absorb(
    await fix(
      'Review ripresa',
      'Ripresa dopo una domanda: applica al diff la risposta di Marco (RISPOSTE DI MARCO) all ultima ' +
        'domanda in Giri precedenti. Non ricostruire il resto: il lavoro gia nel diff resta.',
      // The default rule would mark the questioned findings as repeated, and absorb() would stop again.
      'I rilievi nominati nell ultima domanda sono l oggetto della risposta: vanno in `done` o in ' +
        '`rejected` come dice la risposta, mai in `repeated`. Della risposta applica',
    ),
    'Review ripresa',
  )
  if (resumed) return resumed
}

async function reviewUntilDry() {
  for (let r = 0; r < MAX_REVIEW_ROUNDS; r++) {
    rounds++
    const results = await parallel(
      REVIEWERS.map((rv) => () =>
        agent(
          `${task}\n\nRivedi il diff non committato (git diff; git diff --cached), documenti compresi. ` +
            `Guarda solo: ${rv.what}. Ogni rilievo con file e riga. ${KIND_RULE} Nessun rilievo e un esito legittimo: non inventarne.` +
            (history.length ? `\n\nGiri precedenti (rilievo -> esito):\n${history.join('\n')}` : '') +
            (parked.length ? `\n\nIrrobustimenti gia parcheggiati, non riproporli:\n${parked.join('\n')}` : ''),
          { phase: 'Review', label: `review:${rv.type}#${rounds}`, schema: FINDINGS, agentType: rv.type },
        ),
      ),
    )
    const dead = REVIEWERS.filter((_, i) => !results[i]).map((rv) => rv.type)
    if (dead.length) return failed(`review ${rounds}: nessuna risposta da ${dead.join(', ')}`)
    const all = results.flatMap((x) => x.findings)
    const found = []
    const where = (f) => [f.file, f.line].filter(Boolean).join(':')
    for (const f of all) {
      if (f.kind !== HARDENING) {
        found.push(f)
        continue
      }
      const entry = `${where(f)} ${f.problem}`
      if (!parked.includes(entry)) parked.push(entry)
    }
    log(`giro ${rounds}: ${found.length} difetti, ${all.length - found.length} irrobustimenti`)
    if (!found.length) return null
    const halt = absorb(
      await fix(`Review ${rounds}`, `Rilievi della revisione:\n${JSON.stringify(found, null, 1)}`),
      `Review ${rounds}`,
    )
    if (halt) return halt
  }
  return end('not_dry', { where: `review: ${MAX_REVIEW_ROUNDS} giri senza un giro privo di difetti` })
}

const QUESTIONS = [
  'promesse: ogni cosa che il compito prometteva succede davvero, comprese le prove che i contratti in docs/domini/ nominano? Provala eseguendo.',
  'peggiorato: cosa funzionava prima e ora no, o e piu lento? Confronta con HEAD in un git worktree temporaneo.',
  'doppioni: cosa e scritto due volte (codice, costante, regola, testo)?',
  'spreco: dove costa, in numeri (tempo, query, memoria)?',
]
if (args.surface) {
  QUESTIONS.push(
    'collaudo: la superficie toccata funziona nel browser? Usa la skill collaudo-dal-vivo e guarda il ' +
      'contenuto, non solo i pulsanti. App isolata: `npm --prefix frontend run build`, poi ' +
      '`python -m astrolog` con ASTROLOG_PORT libera e ASTROLOG_DATA_DIR in una cartella temporanea; ' +
      'mai tools/dev.py, mai i dati veri di Marco, e spegnila prima di rispondere.',
  )
}

let audits = []
let checks = null
for (let cycle = 1; cycle <= MAX_CYCLES; cycle++) {
  phase('Review')
  const reviewEnd = await reviewUntilDry()
  if (reviewEnd) return reviewEnd

  phase('Audit')
  // One at a time: audits run the app and compare with HEAD, and must not step on each other.
  audits = []
  for (const q of QUESTIONS) {
    const name = q.split(':')[0]
    const verdict = await agent(`${task}\n\nDomanda dell audit -- ${q}`, {
      phase: 'Audit',
      label: `audit:${name}#${cycle}`,
      schema: VERDICT,
      agentType: name === 'collaudo' ? undefined : 'auditore',
    })
    if (!verdict) return failed(`audit ${name}: nessuna risposta`)
    audits.push({ question: q, ...verdict })
  }
  const failing = audits.filter((a) => !a.holds)
  if (failing.length) {
    if (cycle === MAX_CYCLES) return end('audit_failing', { audits })
    const halt = absorb(
      await fix(
        `Audit ${cycle}`,
        'L audit non regge:\n' + failing.map((a) => `- ${a.question}\n  ${a.issues.join('\n  ')}`).join('\n'),
      ),
      `Audit ${cycle}`,
    )
    if (halt) return halt
    continue // the diff changed: back to review before it can reach the commit
  }

  phase('Checks')
  checks = await agent(
    'Lancia `python -m pre_commit run --all-files --hook-stage manual` dalla radice del repo. ' +
      'Non modificare niente. `all_passed` e vero solo se ogni controllo dice Passed o Skipped; ' +
      'in `failed` ogni controllo caduto con le righe che dicono perche.',
    { phase: 'Checks', label: `checks#${cycle}`, schema: CHECKS },
  )
  if (!checks) return failed('checks: nessuna risposta')
  if (checks.all_passed) return end('done', { audits })
  if (cycle === MAX_CYCLES) return end('checks_failing', { audits, checks: checks.failed })
  const halt = absorb(
    await fix(`Checks ${cycle}`, `I controlli cadono:\n${checks.failed.join('\n')}`),
    `Checks ${cycle}`,
  )
  if (halt) return halt
}
