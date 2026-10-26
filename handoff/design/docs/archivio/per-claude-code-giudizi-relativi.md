# Per Claude Code: giudizi relativi oltre la notte

Da Claude Design, 18/10/2026. Seguito di «misure dei frame: backfocus e giudizi» (ADR 0022). Domande di Marco dopo aver visto il riepilogo di IC 1396 (Rifrattore 80/480, 1.94″/px).

## Cosa c'è oggi nel disegno

- FWHM: giudizio assoluto in ″ con il limite del corredo F. Su IC 1396 dice «non giudicabile su questo corredo» e «sottocampionata (grave)»: va bene.
- HFD: solo «fuoco peggiore», sul frame, contro la sua notte (stesso oggetto e filtro, almeno 10 frame).
- SNR: solo «SNR basso per la notte», sul frame, contro la sua notte.
- Per notte e produzione, HFD e SNR mostrano solo il numero.

## Cosa chiede Marco

1. **Il frame contro l'oggetto, non solo contro la notte.** Nel riepilogo dell'oggetto finito (tutte le notti), un frame con PSF SNR 10 quando la mediana dell'oggetto è 330 deve dirlo. Stessa regola della notte (mediana − 2 MAD per l'SNR, +5 % sulle migliori per l'HFD), calcolata sui frame dello stesso oggetto e filtro di tutte le notti. Domande:
   - si può fare con la stessa fonte (SubframeSelector, N.I.N.A.) o serve una regola diversa quando le notti hanno seeing e cielo diversi?
   - quale vince quando il frame è nella norma per la sua notte ma basso per l'oggetto? Proposta: due giudizi distinti, «… per la notte» e «… per l'oggetto», mai un voto unico.
   - minimo di frame: 10 anche per l'oggetto?

2. **L'HFD contro l'archivio.** Confrontare l'HFD di una notte o di una produzione con la mediana di tutti gli oggetti già ripresi **con lo stesso corredo e lo stesso filtro** (L con L, Hα con Hα). Ha senso? L'HFD dipende dal seeing e dal fuoco più che dall'oggetto, quindi forse sì; ditelo voi, con la fonte.

3. **L'SNR contro l'archivio: probabilmente no.** La PSF SNR dipende dall'oggetto, dal filtro, dalla posa e dal cielo. Marco chiede di confermare che fra oggetti diversi non si confronta, e che resta solo dentro la notte e dentro l'oggetto.

4. **Massa d'aria**: un giudizio ha senso (es. sopra 2, oggetto sotto 30°)? Se c'è una fonte, dite soglia e parola; altrimenti resta solo il numero.

5. **«Non giudicabile su questo corredo»**: oggi dice cosa, non perché. Proposta di testo accanto, la prima volta: «il corredo non risolve sotto F = 3.9″ (due pixel per stella)». Va bene il calcolo e la parola?

## Regole che restano

- Un giudizio per misura, mai d'insieme, mai uno scarto.
- Ogni soglia ha una fonte o è una scelta di Marco, detta così.
- Quando manca il dato, il giudizio tace e dice perché.

## Cosa ci serve indietro

Per ogni punto: sì / no, la regola, la fonte, la parola a schermo, il minimo di frame, e cosa dice quando tace. Il disegno lo facciamo dopo la risposta.
