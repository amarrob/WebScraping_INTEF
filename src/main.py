from scraper import cursos

output_file = "Cursos_Formacion_INTEF.csv"

scraper = cursos();
scraper.scrape();
scraper.data2csv(output_file);
