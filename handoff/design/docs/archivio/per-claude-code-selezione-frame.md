# Per Claude Code — Selezione dei frame v36.3

Da Claude Design, 23/10/2026; v36.2 dopo le vostre correzioni, v36.3 dopo i ritocchi dello stesso giorno (tutti fatti, vedi qui sotto).

## Cambiato nella v36.3

- Eccentricità: accesa parte a valore, > 0,6 (scelta di Marco: nessuna soglia ufficiale, i forum stanno fra 0,5 e 0,6).
- «scartate» ovunque, anche la carta «In scartate».
- Il motivo di una soglia dalla mediana dice il valore calcolato: «FWHM > mediana + 2,5 MAD (3.42″)».
- Cambiare il tipo di una riga (valore ↔ dalla mediana) e' una modifica da applicare, anche con lo stesso numero.
- Testi della consegna allineati (gruppo con posa e guadagno, altezza dall'app, velocità di Riproduci, mosaico 3 × 3). Risposta alla brief della Selezione dei frame (ADR 0032; misure e giudizi da ADR 0022). Pagina `pagine/Selezione dei frame.dc.html`, tavola `pagine/Selezione dei frame stati.dc.html` (dieci stati desktop, tre del telefono). Approvata da Marco dopo sette giri: le decisioni sono in `docs/DECISIONI.md`, v36, dal giro piu' recente in giu'. Nella pagina tutto e' simulato; qui sotto cosa deve mandare e fare l'app.

## Cambiato nella v36.2

- **Partenze uguali per ogni setup**, dal vostro §1: FWHM accesa > mediana + 2,5 MAD; eccentricità spenta (valore, > 0,6 dalla v36.3); stelle e SNR accese < mediana − 2,5 MAD; fondo cielo spento > mediana + 2,5 MAD; altezza spenta < 30°. MAD scalato (1,4826 × la mediana degli scarti). La tabella per setup e' uscita.
- **FWHM**: dalla mediana (partenza) o a valore, con un segmentato nella riga. A valore sotto il limite F del setup la riga dice «✕ sotto il limite del setup (3.88″): scarterebbe tutto». FWHM simulata = HFD × 1,15 (circa 2,1 px sulla FRA400, 2,4 px sull'Askar 103).
- **Al limite** solo per le soglie dalla mediana, entro 1 MAD; il 5 % e' uscito.
- **Gruppo** = oggetto + setup + filtro + posa + guadagno. Nel simulato M 31 L ha due pose (300 s e 180 s, 20 frame il 18/10): le pillole del grafico diventano «L · 300 s» / «L · 180 s» quando un filtro ha piu' pose, e nel progetto compare «Per filtro e posa». Il riquadro del frame dice posa e gain.
- **Setup** al posto di corredo in tutta la pagina e nelle Impostazioni («Soglie dei setup ↗», «Soglie per setup», «setup e filtro»).
- **«scartate»** nella radice dell'archivio, con lo stesso percorso: D:\Astro\2026-10-05\M 31\L\… → D:\Astro\scartate\2026-10-05\M 31\L\…. La colonna «dove» della finestra mostra questi percorsi.
- **Elimina**: col cestino «Mettere N frame nel cestino?», «I file vanno nel cestino del computer: da lì si possono ancora recuperare.», bottone «Metti nel cestino»; senza cestino (NAS) segno !, «Eliminare N frame per sempre?», «Su questa cartella non c'è il cestino: i file si cancellano per sempre. Non si recuperano.», bottone rosso «Elimina per sempre»; misto: la riga dice quanti sono sul NAS e il bottone «Elimina · N per sempre». Ogni cartella dice «nel cestino» o «senza cestino». Tavola: stati 09 e 10.
- **Riproduci**: accanto a ▶ un tasto che gira fra 0,1 · 0,3 · 0,5 · 1 · 2 s (partenza 0,5 s).
- **Angoli e bordi**: il mosaico 3 × 3 (centro, angoli, bordi) al posto dei quattro angoli.
- **Come funzionano**: la riga del MAD, il gruppo con posa e guadagno, «al limite» solo per le soglie dalla mediana, eccentricità e altezza spente.
- Le sezioni 3 e 4 qui sotto sono aggiornate. I calcoli (altezza, statistiche del gruppo, conteggi della bozza, formula) li manda l'app, come dite al §6.

## 0. Cosa e' cambiato rispetto alla vostra brief

- **Parti da**: Un progetto in corso · Delle notti. L'archivio e' gia' pulito (lo stacking e' fatto) e non si sceglie; il setup non si sceglie (lo stesso oggetto ad altezze e Lune diverse non si confronta).
- **Niente tabella dei frame, niente riepilogo a carta.** Il lavoro si fa sul grafico «Frame per frame» (lo stesso del riepilogo di Notti e Archivio) e sul riquadro del frame con l'immagine.
- **Stati**: tenuto · da scartare (soglie o a mano) · tenuto a mano · non misurato · in «scartate». «Proposto» e «Applica le proposte» sono usciti: le soglie segnano direttamente.
- **Le regole** non sono piu' «soglie relative + espressioni a parole»: sono sei righe per **setup e filtro** piu' una formula, e valgono dopo «Applica» (sez. 3).
- **Eliminare** e' in due passi: «Sposta in «scartate»» (si annulla), poi «Elimina dal disco…» dalla carta «In scartate», con la conferma.
- **Telefono solo per guardare**: niente ✕ ✓, Sposta, Elimina.

## 1. Cosa deve mandare l'app

### I frame della scelta
Per un progetto in corso (tutte le sue notti) o per le notti scelte (tutti gli oggetti), un elemento per frame:
- id, nome del file, cartella (disco compreso: serve agli errori), dimensione in MB;
- oggetto, setup, filtro, posa in s, notte (data della sera), ora di inizio;
- le misure di ADR 0022: FWHM (″), HFD (″), eccentricita', stelle, SNR, fondo cielo (ADU), gradiente (%), massa d'aria, luminosita' del cielo (SQM, dove c'e'), e l'altezza, calcolata dall'app con le effemeridi;
- posa e guadagno (fanno parte del gruppo);
- `misurato: false` finche' le misure non ci sono (la pagina lo dice e le soglie non toccano il frame);
- la scelta a mano gia' salvata (`tenuto` / `escluso`) col motivo, se c'e' («scia di satellite»), e se il frame e' gia' in «scartate».

### Le statistiche del gruppo
Gruppo = oggetto + setup + filtro + posa + guadagno, tutte le notti, solo frame misurati. Per ogni misura: mediana, MAD, minimo, massimo, numero di frame. Servono alle soglie relative, alla formula (`_mediana _mad _min _max`), alla riga «mediana · minimo–massimo» sotto ogni soglia. Sotto 10 frame la soglia relativa non vale e la pagina lo dice.

### I progetti in corso
Nome, nome comune, gruppi (oggetto + setup + filtro + posa + guadagno) che ne fanno parte, obiettivo in ore per filtro. L'anello e le barre per filtro sono quelli di Progetti, con le ore **dei soli frame tenuti**: si aggiornano mentre si scarta. Con zero progetti in corso la pagina mostra «Nessun progetto in corso» e «Parti dalle notti».

### Le notti
Le notti con frame della scelta (accese con la stella nel calendario). Nel simulato sono tre, tutte in ottobre: le frecce del mese sono spente.

## 2. L'immagine del frame (la parte che il disegno non puo' fare)

Nel disegno il frame e' un campo di stelle disegnato: le stelle si allargano con la FWHM, si allungano con l'eccentricita', il fondo si schiarisce col fondo cielo, la scia si vede se il motivo dice «satellite». Nell'app:
- **Miniature**: una per frame, fatte alla scansione o alla prima apertura e tenute in cache (proposta: lato lungo 1200 px, debayer per le camere a colori, JPEG o WebP). Servono anche alla riproduzione (▶): la velocità la sceglie l'utente (0,1 · 0,3 · 0,5 · 1 · 2 s, partenza 0,5 s).
- **Stretch uguale per tutti** (partenza, come il Blink di PixInsight): un solo stretch calcolato su un frame di riferimento del gruppo (proposta: quello con la mediana del fondo piu' vicina alla mediana del gruppo) e applicato a tutti, cosi' un cielo piu' chiaro si vede piu' chiaro. **Per frame**: lo stretch automatico di ciascuno. Proposta: STF di PixInsight (shadows clipping −2,8 MAD, target background 0,25).
- **Centro ingrandito** e **mosaico 3 × 3** (centro, angoli, bordi, come ASTAP e AberrationInspector): ritagli al 100 % (nel disegno 90 × 60 del campo per vista); servono a vedere tilt e stelle allungate. **Schermo intero**: la miniatura grande; frecce, S scarta, T tiene, Esc torna.
- Le miniature le fa l'app; dimensione e spazio li misurate voi alla costruzione.

## 3. Le soglie

Per **setup e filtro** (la formula per setup), salvate nelle Impostazioni › Selezione dei frame e modificabili anche dalla pagina. Una riga per misura: acceso/spento, confronto (`>` `≥` `<` `≤`), valore. Le partenze sono le stesse per ogni setup:

Ogni riga sceglie «dalla mediana» (in MAD) o «valore» (decisione di Marco, dopo la v36.2); la tabella dice la partenza.

| misura | tipo | partenza |
|---|---|---|
| FWHM | dalla mediana (o valore, a scelta) | accesa, > mediana + 2,5 MAD |
| Eccentricità | valore | spenta; accesa parte da > 0,6 (scelta di Marco: nessuna soglia ufficiale, i forum stanno fra 0,5 e 0,6) |
| Stelle | dalla mediana | accesa, < mediana − 2,5 MAD |
| SNR | dalla mediana | accesa, < mediana − 2,5 MAD |
| Fondo cielo | dalla mediana | spenta, > mediana + 2,5 MAD |
| Altezza | valore (°) | spenta, < 30° |

MAD scalato: 1,4826 × la mediana degli scarti dalla mediana (Leys et al. 2013). Sotto 10 frame nel gruppo la soglia dalla mediana non vale e la riga lo dice. FWHM a valore sotto F = max(2 × scala, 116/D) ⇒ «sotto il limite del setup (…″): scarterebbe tutto».

- Il frame e' **da scartare** se almeno una riga accesa lo prende o se la formula e' vera. Il motivo e' il nome della riga, che resta sul frame; per una soglia dalla mediana dice anche il valore calcolato: «FWHM > mediana + 2,5 MAD (3.42″)».
- **Al limite** (giudizio, non scarta): solo per le soglie dalla mediana, dalla parte buona, entro 1 MAD dalla soglia (come avviso e azione delle carte di controllo). Una soglia a valore non ha «al limite». Lo usano il riquadro del frame, il riquadro del grafico e la lista del telefono («Da scartare o al limite»).
- **Applica**: la pagina scrive una bozza (anche il cambio di tipo, valore ↔ dalla mediana, e' una modifica); i conteggi della tabella dicono cosa scarterebbe, i frame cambiano solo dopo Applica. Una formula con errore spegne Applica.
- La scelta a mano vince sempre, anche se poi la soglia cambia.

### La formula
Grammatica (la simula `formula()` nella pagina; vi chiediamo la stessa, con gli stessi messaggi d'errore):
- misure: `FWHM` `HFD` `Eccentricità` `Stelle` `SNR` `Fondo` `Gradiente` `Altezza`, anche con `_mediana` `_mad` `_min` `_max` del gruppo (`FWHM_mediana`);
- numeri col punto o la virgola; `+ − × ÷` (anche `- * /`), parentesi; confronti `< > ≤ ≥` (anche `<= >=`); `e` / `o` (anche `&&` `||`), «e» prima di «o»;
- deve finire in un confronto; vera = il frame si scarta; se a un frame manca una misura usata, la formula non lo tocca; divisione per zero = non vale.
- Errori in parole: «Prima di «>» manca un numero o una misura.», «Manca una parentesi chiusa.», ««xyz» non è una misura: …», «Manca il confronto: aggiungi per esempio > 0.012.».

## 4. Le azioni sui file

- **Sposta in «scartate»**: ogni frame da scartare va nella cartella `scartate` nella radice dell'archivio, rifacendo lo stesso percorso, sullo stesso disco della radice (il «+ Directory» di WBPP scende nelle sottocartelle). L'app tiene l'elenco dei percorsi. Si annulla («Riporta indietro» nell'avviso, nella carta, nel riquadro).
- **Elimina dal disco…**: solo dalla carta «In scartate», con la finestra di conferma (frame, MB, cartelle). I file vanno nel cestino; sul NAS e in Docker il cestino non c'e' e si cancellano per sempre: la finestra lo dice e il bottone diventa «Elimina per sempre».
- Errori (Tweaks «errore»): NAS in sola lettura, disco staccato, file aperto da un altro programma. L'avviso dice quanti si', quanti no e perche', con «Riprova».

## 5. I testi da far approvare a Marco

Le righe in testa (desktop e telefono), «Scarta i frame con…», «! modifiche da applicare», «Pronta: accendila e premi Applica.», «In uso: scarta i frame per cui è vera.», «meno di 10 frame nel gruppo: la soglia non vale», «Le misure di questi frame non ci sono ancora: l'app le calcola dopo la scansione…», «Nessun progetto in corso» e la riga sotto, «Stretch uguale per tutti» / «Per frame» con le due spiegazioni, «Perché? per esempio scia di satellite», le cinque righe di «Come funzionano».

## 6. Ingressi

- «Altro» → Selezione dei frame (computer e telefono).
- Progetti, scheda di un progetto in corso: «Seleziona i frame ↗» → `?progetto=<id>`.
- Notti, riepilogo della notte, accanto a «Frame per frame»: «Seleziona i frame ↗» → `?notte=AAAA-MM-GG` (nel simulato apre sempre il 12 ottobre: serve la data della notte aperta).
- La pagina legge anche `?modo=` e `?accento=` (per le catture).

## 7. Cio' che non si porta

Il generatore di frame (`archivio()`), l'immagine disegnata, `formula()` come motore (la grammatica si', il codice no), `alPronto()`, la tavola degli stati.
