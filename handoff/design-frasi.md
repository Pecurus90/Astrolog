# Per Claude Design -- le frasi, in tutte le pagine

Da Claude Code, 19/10/2026. v24.3 (vocabolario) controllata, poi tutte le frasi a schermo di tutte
le pagine e dei componenti: italiano, senso per un esperto, tono, glossario
(`docs/domini/glossario.md`). Il tono va bene ovunque («tu», niente prima persona, niente
esclamativi): sotto ci sono solo le correzioni. Le frasi gia' approvate da Marco restano.

## Tre scelte di Marco

1. **«Deep sky»** ovunque, non «Cielo profondo»: modi del Planner «Deep sky · Sistema solare ·
   Eventi», linguette di Archivio e Meteo, gruppi dei sensori.
2. **«Criteri»** anche in Archivio e Notti: il pulsante e la carta che aprono le scelte di ricerca;
   «Togli i criteri». «Filtri» resta solo il gruppo dei vetri.
3. **Percentuali attaccate**: «40%», ovunque (oggi «19 %», «62 %», «5 %», «{n} %»).

## Errori da correggere

**Grammatica e grafia**
- «illuminata al 83%» -> articolo calcolato: «all'» davanti a 8, 11, 80-89 (PlannerSolare 247 e
  249, Eventi, elongazioni, Notti `n.luna`, Meteo 465 e 589). Meteo lo fa gia' per le nuvole.
- «30°per almeno 1 h» -> «30° per almeno 1 h» (Planner 289).
- Costellazioni con le maiuscole: Orsa Maggiore, Cane Maggiore, Croce del Sud, Cani da Caccia,
  Corona Boreale, Pesce Australe, Uccello del Paradiso, Macchina Pneumatica, Idra Maschio, Leone
  Minore, Pesce Volante, Triangolo Australe, Cane Minore, Corona Australe, Orsa Minore (Planner 505).
- «senza ora: Non disponibile» -> «non disponibile» (Archivio, Aggiungi).
- Un apostrofo solo: oggi «L'archivio» dritto e «L’app» curvo insieme. Il dritto.
- «IC 5070 - Nebulosa Pellicano» -> «IC 5070 · Nebulosa Pellicano» (Da confermare 267).
- “Filtro 5” -> «Filtro 5» (Dashboard 547).
- «nel sistema solare» -> «nel Sistema solare» (Dashboard 381).
- «Seeing: meteoblue» -> «Meteoblue» (Meteo 82).
- «est-nordest» -> «est-nord-est» (Dashboard 551).

**Numeri col punto** (regola v16.1)
- «1.366 m» -> «1366 m» (Impostazioni): col punto decimale si legge un metro e 366.
- «0,45», «0,71», «0,52» (Misure, MisureFrame); «2,1″», «1,8″» (Archivio, Aggiungi); «7,5 mm»,
  «0,5 mm», «0,7x» (Attrezzatura); «1,8″», «0,08», «18,4 giorni» (Dashboard 297, 301, 551) -> col
  punto.

**Vocabolario (resti)**
- «Togli i filtri» e la × «Togli il filtro» delle pillole di Trova -> criteri (Planner 286).
- «senza filtro» -> «nessun filtro» (PlannerSolare 262, Da confermare 185 «A colori, nessun
  filtro», Misure, testo SQM).
- Archivio: colonna «ore» -> «Integrazione»; «Per ore» -> «Per integrazione»; «dalle più ore» ->
  «dalla più lunga»; Riepilogo `H.oreL` «6 h 36 ore» -> titolo «Integrazione», valore «6 h 36».
- Notti: intestazione «ore» -> «Integrazione».
- Luna «mosaico di 6 riprese» -> «mosaico di 6 pannelli» (Archivio 313).
- Hα, una grafia sola: oggi «H-alfa», «Ha», «H-alpha», «Hα» (Archivio, Filtri, Da confermare,
  Dashboard 147 «in Ha»). I nomi dei prodotti restano come li scrive il produttore.
- «quadribanda» -> «quad band» (Filtri).
- Nome del setup sempre «ottica · camera» (oggi anche «Askar FRA400 + ZWO ASI2600MM Pro» e
  «camera · ottica»: Misure, Da confermare 277, Progetti).
- «Bit dell'ADC» -> «Bit del convertitore» (Attrezzatura 407): ADC ora e' il correttore.
- «torna a novembre» -> «torna buono a novembre» (Progetti, elenco e badge).
- «Apri il piano» / «Chiudi il piano» -> «Apri il foglio» / «Chiudi il foglio» (Planner 776,
  PlannerSolare): «piano» e' vietato.
- Menu: «Ferma» -> «Interrompi» (scansione); «siti, temi, cartelle, notifiche» -> «siti, tema,
  cartelle, servizi» (le notifiche non esistono).
- Dashboard: «Prima scansione al lavoro» -> «in corso» (542); «dopo la prima lettura», «Dopo la
  lettura:» -> «scansione» (103, 545); «Le foto restano dove sono.» -> «I file restano dove sono.»
  (544); «Il sito di ripresa» -> «Il sito di osservazione» (539).
- Cerca: «i file non lo dicono» -> «non indicato nei file»; «non ancora contato» -> «conteggio in
  corso». Attrezzatura 146: «Planetarie, in conteggio» -> «Planetarie · conteggio in corso».

**Meteo**
- «rugiada 2 °C», «Temperatura e rugiada», «temperatura meno rugiada» -> «punto di rugiada» (Meteo
  259, 264, 271, 462; Dashboard 300).
- «nubi» -> «nuvole», «Nubi alte / basse» -> «Nuvole alte / basse» (Meteo 393, 533, 587, 629;
  Dashboard 386, 533; CardMeteo).
- Dashboard 385: pillola «✕ notte coperta» -> «✕ non adatta» (e' il verdetto; «coperta» nella riga
  sotto).
- Dashboard 313: «nessuna ora serena» in una notte normale -> «nessuna ora utile» («ore serene»
  vale solo dove il buio non arriva).
- Meteo 458: «Ore buone / incerte / non adatte» -> «Diventa buona / incerta / non adatta».
- Meteo 493: «Nessuna notte astronomica» -> «Nessun buio».
- Meteo 394, 629, CardMeteo: «Il seeing richiede una chiave API Meteoblue (gratuita).» -> «Il
  seeing richiede una chiave Meteoblue.», una forma sola.
- «accordo dei modelli 3 su 4» -> «3 modelli d'accordo su 4» (Meteo 257 e seguenti).
- Dashboard: «tramonta 15:17 di domani» / «sorge domani 07:26» -> una forma: «domani 15:17».
- «raffiche fino a 13» -> «fino a 13 km/h» (Dashboard 299).
- «Inizia il buio» / «Comincia la pioggia» -> un verbo solo: «Inizia».
- Meteo 82: il credito Copernicus tutto come chiede la licenza, non meta' tradotto.

**Eventi**
- Eclisse di Luna: «Grandezza dal sito» -> «Grandezza» (e' uguale per tutti; «dal sito» solo col
  Sole).

## Frasi da rendere piu' chiare

- PlannerSolare 381: «… serve il correttore di dispersione atmosferica (ADC): sotto 35°, da
  Impostazioni.» -> «… serve il correttore di dispersione atmosferica (ADC). Soglia 35°, da
  Impostazioni.»
- PlannerSolare 486: «tratto spesso = adatta» -> «tratto spesso = ore adatte».
- Impostazioni, aiuto del disegno: «Maiuscolo più frecce di 15» -> «Frecce: un grado. Maiusc e
  frecce: 15°.»
- Progetti, ore a zero: «nessuna ora di 8 h» -> «0 h di 8 h» (zero e' una misura).
- MisureFrame 333-334: «Senza sito: niente zenit.» -> «Senza sito: niente FWHM allo zenit.»
- MisureFrame 29: «La FWHM è quella vera: … sotto PixInsight, che le legge più grandi.» -> «La FWHM <!-- software-ok -->
  di ASTAP: sulle stelle piccole circa 14% sotto altri programmi.» (niente polemica, niente nomi
  di programmi non supportati).
- MisureFrame 102: «lo stesso guadagno» -> «lo stesso gain» (come bin e offset).
- Primo avvio 41: «Inseribili anche senza connessione.» -> «Si scrivono anche senza rete.»
- Primo avvio 286: «Le impostazioni non hanno risposto. Riprova.» -> «L'app non ha risposto.
  Riprova.»
- Archivio, Aggiungi: «Le calcola l'app» -> «Calcolate dall'app».
- Attrezzatura 263: «chi è» -> «nome e modello».
- Primo avvio 28, Da confermare 23: «verranno rilette», «vengono salvate» -> «si rileggono», «si
  salvano»; Notti: «Le notti vengono create dai frame delle cartelle aggiunte.» -> «Le notti
  nascono dai frame delle tue cartelle.»; «…non possono essere assegnati a una notte.» -> «…senza
  un sito non hanno una notte.»; «Nel file non c'è il tempo» -> «Nei file» (sono piu' frame).
- Meteo 204: «le notti non sono calcolabili» -> «le notti non si possono calcolare».
- Telaio e Cerca: una frase sola per il segnaposto della ricerca: «Cerca oggetto, notte,
  attrezzatura, sito o pagina».

Resta come oggi la carta del Sole in Dashboard e Archivio (attivita', macchie, Kp): e' decisa in
ADR 0019.

CHANGELOG e DECISIONI come al solito, con le pagine toccate.
