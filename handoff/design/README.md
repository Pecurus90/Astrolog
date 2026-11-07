# AstroLog

Il design dell'app nel linguaggio «bento», versione finale v73 (7/11/2026). E' la fonte del porting: Claude Code la mette in `handoff/design/` al posto della v58.6 e riparte da qui.

| dove | cos'e' |
|---|---|
| `pagine/*.dc.html` | le pagine vere, desktop e telefono nello stesso file (formato automatico, oppure `?formato=telefono`) |
| `pagine/* stati.dc.html` | gli stati difficili di ogni pagina, desktop e telefono |
| `pagine/Sistema.dc.html` | token, telaio e mattoni |
| `pagine/componenti/` | i componenti (`.dc.html`) e i dati simulati e i calcoli (`.js`) |
| `pagine/astrolog.css` | il foglio unico: token, componenti, pagine |
| `docs/DECISIONI.md` | cosa si e' deciso e perche' |
| `docs/CHANGELOG.md` | cosa e' cambiato |
| `docs/per-claude-code-porting.md` | la consegna per Claude Code: foglio, pagine, cosa e' simulato, cosa cambia con v60–v73 |
| `docs/COMPONENTI.md` | l'elenco dei componenti (Planner aggiornati alla v58; gli altri alla v32) |
| `pagine/Mappa del transito.html` | la mappa dei posti per i transiti (Leaflet, aperta dal Planner degli Eventi) |
| `docs/archivio/` | brief e note gia' chiusi, e i testi di partenza (`testi/`) |
| `consegna/` | il pacchetto per Claude Code (`astrolog-v73.zip`) e il suo LEGGIMI |
| `CLAUDE.md` | come si lavora |

Tutti i dati a schermo sono simulati.
