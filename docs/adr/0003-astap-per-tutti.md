# 0003 -- ASTAP e' impacchettato per tutti, e il suo database si scarica al primo avvio

**Stato:** accettata, 9/9/2026

## Contesto

Senza un riconoscitore del cielo i frame entrano ma restano senza cielo e senza oggetto. ASTAP ha
piu' database stellari, per campi diversi, e chi dovesse sceglierne uno dovrebbe sapere cosa gli
serve. Esiste una build ufficiale aarch64 (deb, tar, riga di comando); i tempi pubblici sono di un
Raspberry Pi 4 (2-15 s a frame), nessuno di un NAS. Pesi da SourceForge `star_databases/`: D50 =
867 MB, D05 = 101 MB, G05 = 102 MB.

## Decisione

- **ASTAP sta nel pacchetto**, non e' opzionale: cosi' non c'e' da indovinare quale database
  serve a chi.
- **Nel pacchetto, il database stellare si scarica al primo avvio**, da solo, con checksum, nella
  cartella dati: nessun installer da un GB, nessun aggiornamento che lo riscarica, e l'utente non
  sceglie niente. Sara' l'unico scaricamento senza una richiesta esplicita, dichiarato a schermo.
  Oggi il pacchetto non c'e': l'app installata da sorgente non scarica niente, e il primo avvio dice
  da dove prendere ASTAP (`docs/domini/sito.md`, *Il passo del riconoscitore*).
- **Quando ASTAP non c'e' (chi installa da sorgente) l'app lo dice prima della prima scansione**:
  il passo in piu' del primo avvio e la preferenza `astap_path` stanno in
  `docs/domini/spina.md`.
- Licenze: MPL 2.0 il programma, Gaia DR3 i database, con il credito *ESA/Gaia/DPAC*
  obbligatorio. **Non** si spediscono `deep_sky.csv` e `hyperleda.csv`: non commerciali, e non
  servono.

## Conseguenze

- L'impacchettamento vive con il pacchetto (Docker e app desktop), e con lui la misura del solver
  su un NAS arm64 vero.
- Quando il pacchetto nasce, la frase di `docs/domini/sito.md` "l'app non scarica niente" prende
  l'eccezione del database stellare, nello stesso intervento.
- I crediti obbligatori entrano in `THIRD_PARTY.md`, che nasce col pacchetto.
