// AstroLog · catalogo (il nome comune c'e' per il 3 % circa degli oggetti; la riga principale e' il nome di catalogo)
// AstroLog · catalogo degli oggetti (dati veri), come lo da' l'app (v80): nome comune in inglese, costellazione latina IAU; nome comune, tipo, costellazione, distanza in anni luce (null = non nota: succede spesso), dimensione maggiore in primi d'arco.
window.ALcat = {
  'NGC 7000': ['North America Nebula', 'nebulosa a emissione', 'Cygnus', 2590, 120],
  'IC 5070': ['Pelican Nebula', 'nebulosa a emissione', 'Cygnus', 1800, 60],
  'M 31': ['Andromeda Galaxy', 'galassia a spirale', 'Andromeda', 2500000, 190],
  'NGC 7331': ['', 'galassia a spirale', 'Pegasus', 40000000, 10],
  'M 33': ['Triangulum Galaxy', 'galassia a spirale', 'Triangulum', 2700000, 70],
  'NGC 6992': ['Eastern Veil Nebula', 'resto di supernova', 'Cygnus', 2400, 60],
  'NGC 6960': ['Western Veil Nebula', 'resto di supernova', 'Cygnus', 2400, 70],
  'IC 1396': ['Elephant\u0027s Trunk Nebula', 'nebulosa a emissione', 'Cepheus', 2400, 170],
  'NGC 7635': ['Bubble Nebula', 'nebulosa a emissione', 'Cassiopeia', 7100, 15],
  'M 45': ['Pleiades', 'ammasso aperto', 'Taurus', 444, 110],
  'NGC 891': ['', 'galassia a spirale vista di taglio', 'Andromeda', 30000000, 13],
  'IC 5146': ['Cocoon Nebula', 'nebulosa a emissione e riflessione', 'Cygnus', null, 12],
  'NGC 7293': ['Helix Nebula', 'nebulosa planetaria', 'Aquarius', 650, 25],
  'M 15': ['', 'ammasso globulare', 'Pegasus', 33600, 18],
  'NGC 253': ['Sculptor Galaxy', 'galassia a spirale', 'Sculptor', 11000000, 27],
  'M 39': ['', 'ammasso aperto', 'Cygnus', 825, 32],
  'M 13': ['Hercules Globular Cluster', 'ammasso globulare', 'Hercules', 22200, 20],
  'M 92': ['', 'ammasso globulare', 'Hercules', 26700, 14],
  'M 27': ['Dumbbell Nebula', 'nebulosa planetaria', 'Vulpecula', 1360, 8],
  'M 57': ['Ring Nebula', 'nebulosa planetaria', 'Lyra', 2570, 1.4],
  'M 103': ['', 'ammasso aperto', 'Cassiopeia', null, 6],
  'NGC 6995': ['', 'resto di supernova', 'Cygnus', null, 12],
  'Velo intero': ['Veil Nebula', 'resto di supernova', 'Cygnus', 2400, 180],
  'Sh2-155': ['Cave Nebula', 'nebulosa a emissione', 'Cepheus', 2400, 50]
};
// Nomi comuni (in inglese, come li da' il catalogo dell'app) degli oggetti che non sono in ALcat: la Carta del cielo, i progetti, la ricerca.
window.ALnomi = {
  'M 1': 'Crab Nebula', 'M 6': 'Butterfly Cluster', 'M 7': 'Ptolemy Cluster', 'M 8': 'Lagoon Nebula', 'M 11': 'Wild Duck Cluster', 'M 16': 'Eagle Nebula', 'M 17': 'Omega Nebula', 'M 20': 'Trifid Nebula',
  'M 24': 'Sagittarius Star Cloud', 'M 42': 'Orion Nebula', 'M 43': 'De Mairan\u0027s Nebula', 'M 44': 'Beehive Cluster', 'M 51': 'Whirlpool Galaxy', 'M 63': 'Sunflower Galaxy', 'M 64': 'Black Eye Galaxy',
  'M 65': 'Leo Triplet', 'M 66': 'Leo Triplet', 'M 74': 'Phantom Galaxy', 'M 76': 'Little Dumbbell Nebula', 'M 81': 'Bode\u0027s Galaxy', 'M 82': 'Cigar Galaxy', 'M 83': 'Southern Pinwheel Galaxy', 'M 97': 'Owl Nebula', 'M 101': 'Pinwheel Galaxy',
  'M 104': 'Sombrero Galaxy', 'NGC 281': 'Pacman Nebula', 'IC 1805': 'Heart Nebula', 'IC 1848': 'Soul Nebula', 'IC 434': 'Horsehead Nebula', 'NGC 2024': 'Flame Nebula', 'IC 405': 'Flaming Star Nebula',
  'IC 410': 'Tadpoles Nebula', 'NGC 1499': 'California Nebula', 'NGC 6888': 'Crescent Nebula', 'NGC 6946': 'Fireworks Galaxy', 'NGC 2264': 'Christmas Tree Cluster', 'NGC 7023': 'Iris Nebula', 'NGC 6543': 'Cat\u0027s Eye Nebula',
  'NGC 1977': 'Running Man Nebula', 'NGC 2359': 'Thor\u0027s Helmet', 'NGC 3628': 'Hamburger Galaxy', 'NGC 4631': 'Whale Galaxy', 'IC 443': 'Jellyfish Nebula', 'NGC 7380': 'Wizard Nebula', 'IC 63': 'Ghost of Cassiopeia',
  'NGC 869': 'Double Cluster', 'NGC 884': 'Double Cluster', 'NGC 2237': 'Rosette Nebula', 'NGC 2174': 'Monkey Head Nebula', 'NGC 4565': 'Needle Galaxy', 'IC 2118': 'Witch Head Nebula', 'NGC 3372': 'Carina Nebula',
  'NGC 5128': 'Centaurus A', 'NGC 2392': 'Eskimo Nebula', 'NGC 4038': 'Antennae Galaxies', 'IC 342': 'Hidden Galaxy', 'NGC 6334': 'Cat\u0027s Paw Nebula', 'NGC 6357': 'Lobster Nebula', 'IC 4604': 'Rho Ophiuchi Cloud Complex',
  'NGC 7662': 'Blue Snowball Nebula', 'IC 1318': 'Sadr Region', 'Sh2-101': 'Tulip Nebula'
};
// Il nome comune di un oggetto: prima ALcat (anche quando dice che non c'e'), poi ALnomi; '' se non ce l'ha
window.ALnome = n => window.ALcat[n] ? window.ALcat[n][0] : (window.ALnomi[n] || '');
