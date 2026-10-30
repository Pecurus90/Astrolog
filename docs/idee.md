# Le idee

Idee di Marco e proposte non ancora decise, una per voce, con la data in cui sono nate (ADR 0027).
Un'idea non diventa lavoro finche' Marco non dice di farla: allora va nel [piano](piano.json). A
ogni tappa del piano si rilegge: si fa, resta o si cancella; ferma da tre tappe si cancella.

- **La previsione accanto al meteo vero** (1/10/2026): tenere la previsione di una notte passata
  per misurare quanto ci azzeccava su quel sito, e il seeing previsto per notte (oggi si butta).
- **Dividere i frame di una notte dal fondo cielo** (1/10/2026): il fondo separa bande larghe e
  strette di ordini di grandezza; si cercano gli scalini, non le soglie, campione i frame che il
  filtro lo scrivono. Il fondo lo misura `measure` (`pipeline_measures`); la divisione a mano resta.
- **Il cielo dentro l'app senza chiave** (1/10/2026): il dato di luminosita' a 30" pesa 2,9 GB,
  ridotto la casella diventa di 9 km. Si riapre se qualcuno pubblica un dato piu' compatto.
- **Il dubbio sull'oggetto, non sul frame** (1/10/2026): un frame sbagliato dentro un oggetto
  lucchettato non fa arrivare domande. Voluto; si riapre con una vista per questo genere di segnale.
- **La relazione parte/adiacenza fra oggetti** (1/10/2026): `NGC 2244` nella Rosetta, `M 110`
  accanto a `M 31`. In `old/` misurata, mai costruita; serve al Planner e alla Carta del cielo.
- **Cosa il cielo ha trovato accanto a un gruppo senza nome** (1/10/2026): negli altri frame della
  stessa notte e dello stesso puntamento; servirebbe un campo `subjects` sul gruppo.
- **Il setup simulato del Planner** (19/10/2026): "e se avessi", l'unico caso in cui il campo si
  deriva invece di misurarsi.
- **Occultazioni di asteroidi nel Planner** (19/10/2026): campagne coi dati IOTA (Occult, <!-- software-ok -->
  OccultWatcher). Gli altri eventi del Sistema solare sono decisi (ADR 0023).
- **Meteo, le aggiunte** (12/10/2026, dal confronto con Astrospheric, Clear Outside, Clear Sky
  Chart, 7Timer, meteoblue): probabilita' di sereno dai membri dell'ensemble (Open-Meteo,
  `cloud_cover`, si mostra il numero: nessuna convenzione da' una soglia); previsto contro ripreso
  nelle notti con frame (vuole le previsioni archiviate); via le carte doppie (*Vento a 200 hPa*
  ripete il jet stream a 250; *Umidita'* e *Temperatura e rugiada* da pesare contro la *Condensa*).
  Fuori: trasparenza, instabilita', aurora, satelliti.
- **Dashboard, le colonne dei progetti** (12/10/2026, dal confronto con Target Scheduler, Voyager,
  Telescopius, SkyTools, TheAstroImagingPlanner): distanza dalla Luna stanotte; ore utili stanotte
  al posto di *sopra 30 gradi*; transito e finestra che si chiude, e con le tre l'ordine *meglio
  stanotte*; ore per filtro e per pannello; qualita' dell'ultima notte (aspetta `measure`).
- **Il seeing di una notte passata** (17/10/2026): nessun servizio pubblico lo archivia. Strade:
  la FWHM dei frame in arcosecondi (`measure`), il seeing vero; archiviare da oggi la previsione;
  `history_days` 1-4 del Package API di Meteoblue, se il pacchetto del seeing lo accetta (non
  verificato); stimarlo da ERA5 con Osborn e Sarazin, solo come "stimato" e solo se Marco lo vuole.
- **Il fuoco e la temperatura** (Marco, 22/10/2026, con `measure`): dalla posizione e dalla
  temperatura del focheggiatore (gia' nella scheda del file) lo spostamento in step per grado, per
  notte e setup, come il coefficiente di N.I.N.A.; con la nitidezza delle stelle, le pose sfocate
  e se il fuoco ha seguito la temperatura.
- **La durata della posa per filtro** (Marco, 27/10/2026, da The Night Manager): dal fondo cielo
  misurato sui frame (`measure`) e dal rumore di lettura della camera, la posa piu' corta che
  rende trascurabile il rumore di lettura, col metodo di Robin Glover (SharpCap Brain); <!-- software-ok -->
  formula da verificare sulla fonte e da citare; serve il rumore di lettura per guadagno.
- **La scheda di un NEO o di una cometa in Ricerca** (Marco, 23/10/2026): toccato l'oggetto, una
  finestra coi dati scaricati (Marco dice "NPC": MPC o JPL, da scegliere): grandezza, periodo,
  velocita' e velocita' angolare, distanza dalla Terra; accanto il Sistema solare in scala con
  l'orbita dell'oggetto, dove sta adesso e dove andra', rispetto alla Terra.
- **Pesi e approvazione dei frame come Image Analysis** (30/10/2026, ADR 0042): le sue espressioni
  di approvazione e di peso con media biweight, Qn e z-score sulla serie, al posto delle nostre
  soglie relative (mediana +- 2,5 Qn); da decidere prima del passo 40.1. <!-- software-ok -->
