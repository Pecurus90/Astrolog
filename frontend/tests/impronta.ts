/**
 * L'impronta FNV-1a di un testo (un disegno, un markup): ferma tutto cio' che un'asserzione
 * puntuale non dice. Un ritocco voluto riscrive l'impronta attesa.
 */
export function impronta(testo: string): string {
  let h = 0x811c9dc5
  for (let i = 0; i < testo.length; i++) h = Math.imul(h ^ testo.charCodeAt(i), 0x01000193)
  return (h >>> 0).toString(16)
}
