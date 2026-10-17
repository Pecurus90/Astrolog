# Per Claude Design -- ultimi ritocchi alla v10 prima del porting

Da Claude Code, 17/10/2026. Ho controllato la v10 contro l'app: parole, qualita', scansione,
stati, linguette, `astrolog.css`, caratteri. Quasi tutto e' a posto. Restano queste cose, tutte
piccole. Estetica e comportamenti non cambiano.

## 1. Il verdetto: deciso ora da Marco

Nella v10 il verdetto viene dalle ore utili ("buona da 6 ore, incerta da 3"), scritto come
"soglie di Marco". Marco non le aveva decise. Le ha decise oggi (ADR 0020 dell'app):
- **Il verdetto viene dal punteggio della notte**, cioe' la media 0-100 delle ore di buio:
  **buona da 70, incerta da 40**, sotto non adatta. Vale per stanotte, le prossime notti, le
  notti passate (Notti, calendario, Riepilogo) e il giorno del Sole (media delle ore della finestra di giorno).
- **Ora utile: qualita' da 60.** Resta il numero grande "Ore utili", ma non decide il verdetto.
- In `soglie.js`: via `oreEsito`; il verdetto si simula da `livello` sulla media della notte,
  con 70 / 40. Togliete "soglie di Marco" dal commento.
- In DECISIONI: correggete "il verdetto dal punteggio, con le soglie di Marco: buona da 6 ore
  utili, incerta da 3", e nelle Notti "Esito di una notte passata: dalle ore utili con
  `ALsoglie.oreEsito`".
- Effetto voluto sui dati d'esempio: qualche notte puo' cambiare parola. Ditelo nel CHANGELOG.

## 2. I gradini dei giudizi (avete chiesto conferma)

Dove l'app ha un gradino solo, il gradino e' **non adatto**, non incerto:
- **jet stream da 126 km/h: non adatto** (in `soglie.js` oggi `jet` da' 1);
- **condensa sotto 3 °C: non adatto** (oggi `condensa` da' 1);
- visibilita' sotto 1 km e pioggia: non adatto (giusto cosi').
- **Aerosol**: sotto 0,1 buono, **da 0,1 a 1 nessuna parola** (barretta neutra, nessuna
  pillola), da 1 non adatto. Oggi in mezzo da' "incerto".

Le curve di `qualita` in `soglie.js` sono simulate, va bene. Se le toccate, usate gli estremi
dell'ADR: pieni fino alla soglia buona, zero dalla non adatta (nuvole 25 / 50 %, seeing 2 / 4″,
vento 20 / 29 km/h, condensa 3 / 0 °C, aerosol 0,1 / 1, jet 90 / 126 km/h).

## 3. Parole rimaste

- Notti, scheletro: "Leggo le notti dell'archivio…" -> **Caricamento…**
- Notti, errore: "Non sono riuscito a leggere le notti" -> **Le notti non si possono leggere**
  (niente prima persona).
- Riepilogo, scheletro: "Leggo le misure dei frame…" -> **Caricamento…**
- Notti, frase del cielo: `nuv()` usa 20 / 45 % per "poco / parzialmente / molto nuvoloso".
  Usate **25 / 50 %**, come i giudizi delle nuvole.
- DECISIONI, sezioni vecchie (Dashboard stati, Meteo, Notti, Riepilogo, Archivio): restano
  "ore di posa", "senza tempo", "dato mancante", "Collega la cartella", "Calcolo la notte a…",
  "Chiedo la previsione…", "Previsione non raggiungibile", "foto in arrivo", "polvere",
  "Astropy", "soglia 20%". Segnatele superate dalla v10 o correggetele: chi legge DECISIONI per
  il porting deve trovare una versione sola.

## 4. Dopo

CHANGELOG v11. Poi, quando volete: **primo avvio**, **Attrezzatura**, **Da confermare** come
pagina, **Impostazioni**, **Scansioni**, **Cerca**. Il porting parte da Dashboard, Meteo, Notti
e Archivio come sono ora: questi ritocchi non lo fermano.
