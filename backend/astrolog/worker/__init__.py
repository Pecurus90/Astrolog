"""L'unico scrittore del DB: un thread che esegue gli stadi in sequenza, si ferma in modo
cooperativo e pubblica il proprio stato. Non sa cosa sia uno stadio: esegue generatori."""
