# 0004 -- Su Windows e Mac l'app e' un'app vera: Tauri 2 col backend come sidecar

**Stato:** accettata, 4/9/2026; la scelta fra Tauri ed Electron la chiude il prototipo

## Contesto

Su Windows e Mac l'utente si aspetta un programma da installare e aprire, non un server da
lanciare e una pagina da puntare. Il backend e' Python, e i due sistemi bloccano cio' che non e'
firmato.

## Decisione

- **Tauri 2, con il backend Python come sidecar** (PyInstaller), installer firmati e updater
  firmato. Se il prototipo non passa la notarizzazione su macOS, **Electron** (+80 MB).
- Il sidecar PyInstaller e' **onedir, mai onefile**. Il bundler di Tauri 2 firma da solo i
  sidecar; l'issue aperta e' la #11992 ("signature of the binary is invalid" con `externalBin`),
  e si diagnostica con `xcrun notarytool log`. Gli entitlements stanno in un `entitlements.plist`
  a parte e valgono anche per il sidecar (`allow-jit`, `allow-unsigned-executable-memory`,
  `disable-library-validation`).
- **macOS**: serve l'Apple Developer Program (99 USD/anno). Senza, da Sequoia l'utente passa da
  Impostazioni > Privacy > "Apri comunque"; l'alternativa senza account e' Homebrew cask.
- **Windows**: senza firma SmartScreen blocca, un certificato EV non lo salta piu', Azure Artifact
  Signing accetta individui solo in USA e Canada. Per un progetto open source **SignPath
  Foundation firma gratis** (licenza OSI, build riproducibile dalla CI): e' la strada.

## Conseguenze

- Il prototipo -- Tauri 2, un sidecar Python vuoto e ASTAP, firmato e notarizzato su macOS -- si
  fa prima che il pacchetto costi.
- Sul NAS resta l'immagine Docker, multi-arch.
