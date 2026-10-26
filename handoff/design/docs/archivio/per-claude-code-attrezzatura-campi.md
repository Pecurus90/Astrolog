# Per Claude Code — i campi dell'attrezzatura (18 ottobre 2026)

Marco ha visto che nei moduli di Attrezzatura (`pagine/componenti/Modulo.dc.html`, usato da `pagine/Attrezzatura v2.dc.html`) mancano dei campi. Serve l'elenco completo dall'app, tipo per tipo, con le parole esatte, l'unità, se è obbligatorio, se arriva dai file FITS (e da quale header) e se è calcolato.

## Cosa c'è oggi nel disegno

Per tutti (blocco "chi è"): Nome (obbligatorio), Marca (tendina + "altra…" → Nuova marca), Modello, Note (non nei filtri).

Dati tecnici:
- ottica: Apertura (mm), Focale nativa (mm), Peso (kg); Rapporto focale calcolato
- camera: Tipo di sensore (mono / a colori), Pixel (µm), Peso (kg)
- montatura: Carico utile (kg), Peso (kg)
- riduttore: Fattore, Peso (kg)
- ruota portafiltri: Numero di posizioni, Peso (kg)
- ottica di guida, camera di guida, focheggiatore: Peso (kg)
- Filtro: Quante bande (1–4), per banda: Banda (L, R, G, B, HA, HB, OIII, SII) e Larghezza (nm)
- Corredo: Ottica, Camera, Focale effettiva (mm)
- In modifica: Unisci a

La scheda dei pezzi mostra anche backfocus del riduttore e "pixel (calcolato)", che nel modulo non hanno un campo.

## Domande

1. Per ogni tipo, quali campi ha l'app che qui mancano? Esempi possibili, da confermare o no: dimensioni del sensore e risoluzione della camera, raffreddamento, backfocus, diametro della guida, focale della guida, tipo di montatura (equatoriale, altazimutale), dimensione dei filtri, programma di ripresa come tipo a sé.
2. Quali sono obbligatori, oltre al nome?
3. Quali arrivano dai file (per mettere "dai file") e quali sono calcolati?
4. I valori ammessi delle tendine (bande, tipi, marche) vengono da una lista fissa o dall'archivio?
