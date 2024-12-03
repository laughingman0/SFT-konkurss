
--
-- Table structure for table `varbūtība_un_statistika`
--

DROP TABLE IF EXISTS `varbutiba_un_statistika`;
CREATE TABLE `varbutiba_un_statistika` (
  `sasniedzamais_rezultats` varchar(5000) DEFAULT NULL,
  `uzdevuma_piemers` varchar(5000) DEFAULT NULL
);

--
-- Dumping data for table `varbūtība_un_statistika`
--

INSERT INTO `varbutiba_un_statistika` VALUES ('Prot lieto varbūtību teorijas teorēmas, pilnās\nvarbūtības formulu, izprot nosacīto\nvarbūtību.','Viduslaiku loka šāvēju sacensībās piedalās 15 dalībnieki, no kuriem 10 ir profesionāļi, 3 ir amatieri, bet pārējie ir iesācēji.\nVarbūtība, ka profesionālis trāpīs mērķī ir 90 %, varbūtība, ka amatieris trāpīs mērķī ir 60 % un varbūtība, ka iesācējs trāpīs mērķī ir 10 %. a) Aprēķini varbūtību, ka nejauši izvēlēts dalībnieks trāpīs mērķī.\nb) Nosaki varbūtību, ka šāvējs ir iesācējs, ja bulta ir trāpījusi mērķī.'),('Prot skaidrot un noteikt\ndiskrēta gadījuma lieluma varbūtību\nsadalījumu un aprēķināt nezināmos lielumus.','Apdrošināšanas sabiedrība (AS) piedāvā iegādāties 20000 eiro vērta safīra gredzena apdrošināšanas polisi. Līgums paredz:\n1) ja gredzens tiek nozagts, AS apmaksā gredzena vērtību pilnībā; 2) ja tas tiek nozaudēts, AS īpašniekam maksās 8000 eiro.\nZādzības varbūtība ir 0,0025, bet nozaudēšanas varbūtība ir 0,03.\na) Nosaki varbūtību, ka AS polises pircējam neko nemaksā.\nb) Aprēķini polises cenu, ja AS to noteikusi tādu, ka AS peļņas sagaidāmā vērtība ir 100 eiro par polisi.'),('Prot raksturot binomiālo sadalījumu,\nlietot Bernulli formulu un binomiāla sadalījuma\nsagaidāmās vērtības aprēķināšanas formulu.','Farmācijas firma ir ieviesusi jaunu diagnostikas testu, ar kuru, diagnosticējot inficētu pacientu,\n90 % gadījumu testa rezultāts ir pozitīvs. Nosaki varbūtību, ka ar šo testu tiks atklāti 4 no 5 inficētiem pacientiem.'),('Prot raksturot normālsadalījumu, lieto\nvidējo vērtību, standartnovirzi un vienas,\ndivu un trīs standartnoviržu likumu datu\nraksturošanai. ','Noteiktas putnu sugas svars atbilst normālsadalījumam ar vidējo vērtību 0,8 kg un standartnovirzi 0,12 kg.\nNosaki varbūtību, ka nejauši izvēlēta sugas putna svars ir no 0,74 kg līdz 0,95 kg.'),('Prot lietot pilnās vērtības formulu.','Sēklu paciņā ir 40 % sarkano sēklu un 60 % dzelteno sēklu. Varbūtība,\nka sarkanā sēkla uzdīgs, ir 0,9, bet dzeltenā – 0,8. Nejauši izvēlas sēklu no paciņas.\na) Aprēķini varbūtību, ka izvēlētā sēkla ir sarkana un tā uzdīgs.\nb) Aprēķini varbūtību, ka izvēlētā sēkla izdīgs.\nc) Zinot, ka sēkla ir uzdīgusi, aprēķini varbūtību, ka tā ir sarkana.');

