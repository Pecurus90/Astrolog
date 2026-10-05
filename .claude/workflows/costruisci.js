export const meta = {
  name: 'costruisci',
  description: 'Build a planned feature: one review, one verification of the fixes, one running audit, checks',
  whenToUse: 'Recipe "costruisci" (docs/adr/0015). args: {task, plan, mode: "logica"|"meccanico", surface: bool, answers: [string]}',
  phases: [{ title: 'Build' }, { title: 'Review' }, { title: 'Audit' }, { title: 'Checks' }],
}

const FINDING = {
  type: 'object',
  properties: {
    file: { type: 'string' },
    line: { type: 'integer' },
    blocking: { type: 'boolean' },
    problem: { type: 'string' },
    evidence: { type: 'string' },
  },
  required: ['file', 'problem', 'blocking', 'evidence'],
}
const FINDINGS = {
  type: 'object',
  properties: { ran: { type: 'string' }, findings: { type: 'array', items: FINDING } },
  required: ['findings'],
}
const WORK = {
  type: 'object',
  properties: {
    done: { type: 'array', items: { type: 'string' } },
    rejected: { type: 'array', items: { type: 'string' } },
    question: { type: ['string', 'null'] },
  },
  required: ['question'],
}
const CHECKS = {
  type: 'object',
  properties: { all_passed: { type: 'boolean' }, failed: { type: 'array', items: { type: 'string' } } },
  required: ['all_passed', 'failed'],
}

if (!['logica', 'meccanico'].includes(args.mode)) return { status: 'failed', where: `mode: ${args.mode}` }

const answers = (args.answers || []).map((a) => `- ${a}`).join('\n')
const task =
  `COMPITO:\n${args.task}\n\nPIANO:\n${args.plan}` +
  (answers ? `\n\nRISPOSTE DI MARCO (valgono, non si richiedono):\n${answers}` : '')
// "logica" was written by the main session; fixes then go to an agent on the session model.
const builder = args.mode === 'logica' ? undefined : 'sviluppatore'

const QUESTION_RULE =
  'Se serve una decisione di Marco (prodotto, cio che vede, rischio, una dipendenza nuova), non ' +
  'decidere: metti in `question` la domanda a scelta multipla con la consigliata e fermati.'
const FIX_RULE =
  'Correggi solo i rilievi elencati, con la modifica piu piccola che li chiude. Puoi rifiutarne ' +
  'uno col perche (in `rejected`). Niente dipendenze, file o meccanismi nuovi (stati, campi, code): ' +
  'se servirebbero, e una domanda. I documenti toccati si aggiornano nello stesso diff. Poi ' +
  '`python -m pre_commit run --files <file toccati>` e i test toccati. ' + QUESTION_RULE
const BLOCKING_RULE =
  'Riporta SOLO difetti bloccanti: comportamento sbagliato, sicurezza, perdita di dati, contratto o ' +
  'richiesta violati, test tolto o indebolito. Ognuno con `evidence`: un comando eseguito, un test ' +
  'che fallisce o un controesempio preciso; senza prova non e bloccante. Parole, stile e protezioni ' +
  'per casi che oggi non nascono vanno con `blocking: false`, al massimo tre.'

const parked = []
const rejected = []
const fixed = []
const end = (status, extra) => ({ status, parked, rejected, fixed, ...extra })

// Keeps what blocks; the rest is noted once and never reopens the work.
function sort(findings) {
  const blocking = []
  for (const f of findings) {
    if (f.blocking === true && (f.evidence || '').trim()) blocking.push(f)
    else parked.push(`${f.file}${f.line ? `:${f.line}` : ''} ${f.problem}`)
  }
  return blocking
}

async function fix(where, findings) {
  const work = await agent(
    `${task}\n\nRilievi bloccanti (${where}):\n${JSON.stringify(findings, null, 1)}\n\n${FIX_RULE}`,
    { phase: where, label: `fix:${where}`, schema: WORK, agentType: builder },
  )
  if (!work) return end('failed', { where: `fix ${where}` })
  rejected.push(...(work.rejected || []))
  fixed.push(...(work.done || []))
  return work.question ? end('question', { where, question: work.question }) : null
}

// One verification, on the fixes only: what is still open stops the work instead of looping.
async function verify(where, findings) {
  const check = await agent(
    `${task}\n\nVerifica SOLO che questi rilievi siano chiusi e che le correzioni non abbiano rotto ` +
      `altro: ${JSON.stringify(findings, null, 1)}\n\n${BLOCKING_RULE}`,
    { phase: where, label: `verify:${where}`, schema: FINDINGS, agentType: 'revisore' },
  )
  if (!check) return end('failed', { where: `verify ${where}` })
  const open = sort(check.findings)
  return open.length ? end('stopped', { where, open }) : null
}

async function reviewAndFix(where, findings) {
  const blocking = sort(findings)
  if (!blocking.length) return null
  return (await fix(where, blocking)) || (await verify(where, blocking))
}

if (args.mode !== 'logica') {
  phase('Build')
  const built = await agent(
    `${task}\n\nCostruisci il compito: test prima, visti rossi; i documenti nello stesso diff; ogni ` +
      'file nuovo con `git add -N`. Poi `python -m pre_commit run --files <file toccati>`. ' +
      QUESTION_RULE,
    { phase: 'Build', schema: WORK, agentType: 'sviluppatore' },
  )
  if (!built) return end('failed', { where: 'build' })
  if (built.question) return end('question', { where: 'build', question: built.question })
}

phase('Review')
const review = await agent(
  `${task}\n\nRivedi una volta il diff non committato (git diff; git diff --cached). Domanda: fa ` +
    `cio che il compito chiede e nient altro? ${BLOCKING_RULE}`,
  { phase: 'Review', label: 'review', schema: FINDINGS, agentType: 'revisore' },
)
if (!review) return end('failed', { where: 'review' })
const afterReview = await reviewAndFix('Review', review.findings)
if (afterReview) return afterReview

phase('Audit')
const questions = ['promesse: ogni cosa che il compito prometteva succede davvero? Provala eseguendo.']
if (args.surface) {
  questions.push(
    'collaudo: la superficie toccata funziona nel browser? Skill collaudo-dal-vivo, app isolata ' +
      '(ASTROLOG_PORT libera, ASTROLOG_DATA_DIR temporanea), mai i dati veri di Marco; spegnila.',
  )
}
const audits = []
for (const q of questions) {
  const name = q.split(':')[0]
  const verdict = await agent(`${task}\n\nDomanda dell audit -- ${q}\n\n${BLOCKING_RULE}`, {
    phase: 'Audit',
    label: `audit:${name}`,
    schema: FINDINGS,
    agentType: name === 'collaudo' ? undefined : 'auditore',
  })
  if (!verdict) return end('failed', { where: `audit ${name}` })
  audits.push({ question: name, ran: verdict.ran || '', findings: verdict.findings })
}
const afterAudit = await reviewAndFix('Audit', audits.flatMap((a) => a.findings))
if (afterAudit) return afterAudit

phase('Checks')
const runChecks = (label) =>
  agent(
    'Lancia `python -m pre_commit run --all-files --hook-stage manual` dalla radice del repo. Non ' +
      'modificare niente. `all_passed` e vero solo se ogni controllo dice Passed o Skipped; in ' +
      '`failed` ogni controllo caduto con le righe che dicono perche.',
    { phase: 'Checks', label, schema: CHECKS, model: 'sonnet' },
  )
let checks = await runChecks('checks')
if (!checks) return end('failed', { where: 'checks' })
if (!checks.all_passed) {
  const failing = checks.failed.map((f) => ({ file: '', problem: f, blocking: true, evidence: f }))
  const halt = await fix('Checks', failing)
  if (halt) return halt
  checks = await runChecks('checks:again')
  if (!checks) return end('failed', { where: 'checks' })
  if (!checks.all_passed) return end('checks_failing', { failed: checks.failed, audits })
}
return end('done', { audits })
