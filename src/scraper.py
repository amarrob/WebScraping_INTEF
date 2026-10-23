import time
import requests
from bs4 import BeautifulSoup

class CursosScraper():
    def __init__(self):
        self.url = "https://formacion.intef.es/aulaenabierto/"
        self.data = []
        self.user_agent = "Mozilla/5.0 (UOC-WebScraping-Practica)"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def __download_html(self, url):
        time.sleep(2)
        response = self.session.get(url, timeout=20)
        response.raise_for_status()
        return response.text

    def __get_categories_link(self, html):
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            if "course/index.php" in a["href"]:
                return a["href"]
        return None

    def __get_sections_links(self, html):
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            if text in ["Cursos sin registro", "Formación abierta"]:
                links.append(a["href"])
        return links

    def __get_course_links(self, html):
        soup = BeautifulSoup(html, "html.parser")
        course_links = []
        for a in soup.find_all("a", href=True):
            if "course" in a["href"]:
                course_links.append(a["href"])
        return course_links

    def scrape(self):
        home_html = self.__download_html(self.url)
        categories_url = self.__get_categories_link(home_html)
        print("Página de categorías:", categories_url)
        categories_html = self.__download_html(categories_url)
        sections = self.__get_sections_links(categories_html)
        print("Secciones encontradas:", sections)
