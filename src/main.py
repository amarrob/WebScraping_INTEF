from scraper import CursosScraper

output_file = "Cursos_Formacion_INTEF.csv"

scraper = CursosScraper()
scraper.scrape()
scraper.data2csv(output_file)
