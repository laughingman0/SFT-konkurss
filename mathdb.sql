-- MySQL dump 10.13  Distrib 8.0.40, for Win64 (x86_64)
--
-- Host: localhost    Database: testdb
-- ------------------------------------------------------
-- Server version	8.0.40

--
-- Table structure for table `indukcija`
--

DROP TABLE IF EXISTS `indukcija`;
CREATE TABLE `indukcija` (
  `sasniedzamais_rezultats` varchar(1000) DEFAULT NULL,
  `piemeri` varchar(1000) DEFAULT NULL
);

--
-- Dumping data for table `indukcija`
--


INSERT INTO `indukcija` VALUES ('Skaidro ar matemātiskās indukcijas principu saistītos jēdzienus, simbolisko\npierakstu, pierādīšanas gaitu un lieto matemātiskās indukcijas principu','Dota skaitļu virkne 1; 2; 4; 8; …, kuras katrs nākamais loceklis ir divas reizes lielāks nekā iepriekšējais. Jāpierāda, ka katru divu\npēc kārtas ņemtu virknes locekļu summa dalās ar 3. Vispirms apraksti risinājumu vārdiski, tad to pieraksti, lietojot simbolisko\nvalodu.'),('Lieto kombinatorikas formulas, situāciju aprakstot ar vienādojumu vai nevienādību naturālo skaitļu kopā. ','Plaknē novilka 6 paralēlas taisnes un pēc tam vēl novilka savā starpā paralēlas taisnes, kuras krusto sākumā novilktās,\nizveidojot 150 paralelogramus. Nosaki to taišņu skaitu, kas krusto 6 paralēlas taisnes.'),('Lieto Ņūtona binomu matemātiskos kontekstos. ','Pierādi, ka 11^10 - 1  dalās ar 100'),('Formulē likumsakarības Paskāla trijstūrī; atsevišķas no tām pierāda.  ','Par slīpni sauksim jebkuru skaitļu novietojumu Paskāla trijstūrī, kas paralēls vieninieku novietojumam. Veic izpēti un konkrētos\npiemēros apraksti likumsakarību, kas ļauj noteikt “jebkuras slīpnes visu, sākot no 1, pēc kārtas galīgā skaitā ņemtu skaitļu summu”.\nFormulē vispārinājumu.'),('Pēta, formulē un pierāda likumsakarības\n“figūru virknēs”, vispārīgi uzdotās algebriskās\nizteiksmēs. ','Figūras tiek veidotas no vienāda garuma nogriežņiem pēc noteiktas\nlikumsakarības (sk. attēlu). Ar s(n) apzīmē vienādo nogriežņu skaitu,\nkas izmantoti n vērtībai atbilstošās figūras izveidei. Izvēlies secību uzdevumu a) un b) risināšanai.\na) Nosaki s(10), parādi risinājumu. b) Uzraksti formulu s(n)\naprēķināšanai, paskaidro, kā to ieguvi. Pierādi, ka formula patiesa\nvisiem naturāliem n.');


-- Dump completed on 2024-11-03 20:15:35
