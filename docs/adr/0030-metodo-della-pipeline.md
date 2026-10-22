# 0030 -- Il metodo della pipeline: un passo alla volta, provato sul vero

**Stato:** accettata, 22/10/2026 (Marco). Vale per la pipeline rifatta da zero (`docs/piano.md`).

## Contesto

La mappa della parte 1 e' stata decisa prima di guardare i file: il censimento dell'archivio di
Marco ne ha smentito dei pezzi (cartella principale collegata a un altro disco, snapshot di N.I.N.A.
scritto LIGHT, CALSTAT attribuita a SBIG per errore). Tre revisori a contesto fresco hanno trovato
difetti che un revisore solo non vedeva. Rifare da zero rischia di perdere cio' che il codice di
oggi fa gia' bene, e di lasciare Marco senza niente da guardare.

## Decisione

Ogni passo della pipeline nuova segue sette tappe, in ordine:

1. **Una mappa piccola del passo**, verificata sui file veri (corpus e archivio di Marco, sola
   lettura). La mappa generale resta direzione, non contratto.
2. **Le decisioni di Marco**, solo quelle del passo, a scelta multipla.
3. **Test sugli header veri, visti rossi, poi il codice**, in `backend/astrolog/pipeline/`.
4. **Confronto con la pipeline di oggi** sullo stesso archivio: ogni differenza ha un perche' (il
   vecchio sbagliava, o si ripara il nuovo prima del commit). La lista delle differenze e' cio'
   che Marco guarda quando il passo non ha una pagina.
5. **Revisione a contesto fresco**: per un passo del cuore, tre agenti con modelli diversi (due
   progettano prima senza vedere il codice, uno lo attacca), sei quesiti: copre tutti i casi? e'
   snello? decisioni giuste? logica giusta? codice giusto e snello? tutte le variabili? Per un
   passo piccolo un revisore; quale dei due si chiede a Marco.
6. **Mappa aggiornata e commit** nello stesso giro: la mappa dice cio' che il codice fa, e la
   mappa grafica mostra a Marco lo stato di ogni mattone (fatto, in corso, da fare).
7. **Si porta solo cio' che si usa**; cio' che resta senza uso, o doppio, si toglie.

Si leggono solo i file di N.I.N.A. e ASIAIR (ADR 0029), di loro tutte le chiavi.

## Conseguenze

- Un errore si vede nel passo che lo crea, non a pipeline finita.
- La pipeline vecchia si cancella solo quando il confronto dell'ultimo strato non ha differenze
  senza perche'.
- Costo: tre revisioni per passo del cuore (ordine di ore, non giorni).
- **Identita' della posa** (Marco, 22/10/2026, secondo audit): camera, inizio UTC normalizzato,
  dimensioni e durata dall'header (`pipeline/fingerprint.py`); i pixel solo se ne manca uno, o se
  l'inizio non ha la frazione di secondo (pose brevi nello stesso secondo; archivio: mai). Un
  `.fits` e la sua copia fpack sono la stessa posa (con la frazione); ogni file si apre una volta.
  Rischi accettati: due camere gemelle sincronizzate al millisecondo; senza frazione, la copia
  fpack conta come seconda posa. Sull'archivio di prova: stesse 15.226 pose.
- **Cartella nascosta dopo** (Marco, 22/10/2026, secondo audit): non si cammina e le sue pose non
  si giudicano, come una cartella che non risponde; la vecchia le dava "non trovate". Il cestino
  resta "sparito": un file cestinato cambia percorso.
