# Per Claude Design -- ritocchi alla v12 (primo avvio)

Da Claude Code, 17/10/2026. Ho controllato la v12 contro l'app: passi, tema, stati, chiusura, i
tre difetti. E' a posto: struttura, `SceltaTema`, "saltato", la riga della scansione, il
telefono. Restano testi che si discostano da quelli dell'app senza motivo. Estetica e
comportamenti non cambiano.

## 1. Bortle: le frasi dell'app, che hanno una fonte

Le nove descrizioni nella v12 sono riscritte. Quelle dell'app vengono dalla voce *Bortle scale*
di Wikipedia (la stessa fonte del numero) e non si cambiano a gusto. I nomi delle classi sono
gia' giusti. Usate queste, parola per parola:

1. cielo eccellente, buio pieno -- La Via Lattea proietta ombre, e il cielo stesso ha un suo
   debole bagliore naturale; a occhio nudo si arriva a M33 e a molti oggetti Messier.
2. cielo buio vero -- La luce zodiacale e' gialla e fa ombra, la Via Lattea d'estate e' piena di
   struttura, e M33 si vede a occhio nudo senza fatica.
3. cielo di campagna -- Qualche alone di luce basso sull'orizzonte, ma la Via Lattea d'estate e'
   ancora complessa e M33 si vede con la visione distolta.
4. campagna piu' chiara -- Gli aloni delle luci si vedono in piu' direzioni; la Via Lattea e'
   ancora bella ma senza dettagli, e la luce zodiacale non arriva a meta' cielo.
5. cielo di periferia -- Solo accenni di luce zodiacale nelle notti migliori; la Via Lattea
   sbiadisce allo zenit e sparisce verso l'orizzonte, e le luci si vedono quasi ovunque.
6. periferia luminosa -- Niente luce zodiacale; il cielo basso e' grigio-bianco e la Via Lattea
   si intravede solo allo zenit. M33 solo col binocolo.
7. fra periferia e citta' -- Tutto il cielo e' grigio chiaro, con sorgenti di luce forte in ogni
   direzione; la Via Lattea quasi non si vede.
8. cielo di citta' -- Il cielo e' grigio o arancione e ci si legge; molte stelle delle
   costellazioni sono deboli o non si vedono affatto.
9. centro citta' -- Le costellazioni si perdono e, a occhio nudo, a parte le Pleiadi non si vede
   nessun oggetto Messier: restano Luna, pianeti e gli ammassi piu' luminosi.

## 2. ASTAP senza catalogo: i testi dell'app

- Perche' del passo: "ASTAP e' installato, ma manca il catalogo stellare. Si scarica a parte,
  anche dopo."
- Avviso "Catalogo stellare mancante": "ASTAP richiede un catalogo stellare, che si scarica a
  parte. Senza catalogo gli oggetti non vengono identificati." Sotto: "Catalogo consigliato: D80
  (circa 1,25 GB), nella stessa cartella di ASTAP."
- Esito della verifica, trovato senza catalogo: titolo "ASTAP trovato, catalogo mancante" va
  bene; il testo e' "Catalogo stellare mancante: senza, gli oggetti non vengono identificati."

## 3. Cartella gia' registrata

Testo dell'app: "Corrisponde a \\nas\astro\2026: stessi file. I dati associati vengono
mantenuti." (al posto di "E' la stessa cartella registrata come ...").

## 4. Dopo

CHANGELOG v12.1. I testi nuovi del primo avvio (tema, chiusura, "saltato") li ha approvati Marco.
