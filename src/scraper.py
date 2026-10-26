import re
import pandas as pd
from utils import (create_session,download_html,get_soup)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager

class CursosScraper():        
    def __init__(self):
            self.base_url = "https://formacion.intef.es"
            self.aula_url = "https://formacion.intef.es/aulaenabierto/"
            self.abierta_url = "https://formacion.intef.es/abierta/"
            self.aula_virtual_url = "https://formacion.intef.es/aulavirtual/course/index.php?categoryid=3"
            self.user_agent = "Mozilla/5.0 (UOC-WebScraping-Practica)"
            self.session = create_session(self.user_agent)       
            self.data = []

    def __get_categories_link(self, html):
        soup = get_soup(html)
        for a in soup.find_all("a", href=True):
            if "course/index.php" in a["href"]:
                return a["href"]
        return None

    def __get_sections_links(self, html):
        soup = get_soup(html)
        sections= []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            if "categoryid=" in href:
                sections.append({"nombre": text, "url": href})
        return sections

    def __get_course_links(self, html):
        soup = get_soup(html)
        courses = []
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            if "course/view.php?id=" in href and href not in seen:
                seen.add(href)
                courses.append({"titulo": text.replace("Curso:", "").strip(),"url": href})
        return courses

    def __get_course_id(self, url):
        match = re.search(r"id=(\d+)", url)
        return match.group(1) if match else None

    def __get_modal_id(self, card):
        target = card.get("data-target")
        if not target:
            return None
        match = re.search(r"courseModal_\d+_(\d+)", target)
        return match.group(1) if match else None
    
    def __get_course_url(self, modal):
        for a in modal.find_all("a", href=True):
            href = a["href"]
            if "course/view.php?id=" in href:
                return href
        return ""
    
    def __extract_metadata(self, text):
        modalidad = re.search(r"\b(MOOC|NOOC|SPOOC|Curso)\b",text,re.I)
        duracion = re.search(r"\d+\s*(?:horas|h)",text,re.I)
        fechas = re.findall(r"\d{1,2}\s+[a-záéíóú]+\s*,?\s*\d{4}",text,re.I)
        estado = re.search(r"(Finalizado|En curso|Abierto|Próximamente)",text,re.I)
        return {
            "modalidad": modalidad.group(0) if modalidad else None,
            "duracion": duracion.group(0) if duracion else None,
            "estado": estado.group(0) if estado else None,
            "fechas": " | ".join(dict.fromkeys(fechas)) if fechas else None
        }

    def __extract_modal_fields(self, modal):
        text = modal.get_text("\n", strip=True)
        titulo = modal.find("h5")
        return {
            "titulo": titulo.get_text(strip=True) if titulo else None,
            "descripcion": self.__extract_section(text, "Descripción general", "Objetivos"),
            "objetivos": self.__extract_section(text, "Objetivos", "Competencia digital docente"),
            "competencia_digital": self.__extract_section(text, "Competencia digital docente", "Público objetivo"),
            "publico_objetivo": self.__extract_section(text, "Público objetivo", "Requisitos recomendados"),
            "requisitos": self.__extract_section(text, "Requisitos recomendados", "Cerrar")
        }

    def __extract_section(self, text, inicio, fin):
        try:
            return text.split(inicio)[1].split(fin)[0].strip()
        except:
           return ""
            
    def __get_formacion_abierta_pages(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument(f"user-agent={self.user_agent}")
        driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()),options=options)
        driver.get(self.abierta_url)
        pages_html = []
        while True:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "course-list")))
            pages_html.append(driver.page_source)
            try:
                next_button = driver.find_element(By.XPATH,"//a[contains(text(),'»')]")
                parent = next_button.find_element(By.XPATH, "..")
                if "disabled" in parent.get_attribute("class"):
                    break
                driver.execute_script("arguments[0].click();",next_button)
                WebDriverWait(driver, 10).until(EC.staleness_of(parent))
            except:
                break
        driver.quit()
        return pages_html

    def __requires_login(self,url):
        response = self.session.get(url,timeout=20,allow_redirects=True)
        return "login/index.php" in response.url

    def __get_virutal_course_links(self,htmil):
        soup = get_soup(html)
        courses = []
        seen = set()
        for a in soup.find_all("a",href=Ture):
            href = a["href"]
            if "course/view.php?id=" in href and href not in seen:
                seen.add(href)
                courses.append({"titulo": a.get_text(strip=True),"url":href})
        return courses
    
    def __scrape_course(self, course):
        html = download_html(self.session, course["url"])
        soup = get_soup(html)
        title = soup.find("h1")
        text = soup.get_text(" ", strip=True)
        actualizacion = re.search(r"Última actualización:\s*(.+)",text)
        temas = re.findall(r"\d+\.\s+[^\n]+",text)
        return {
            "id_curso": self.__get_course_id(course["url"]),
            "titulo": title.get_text(strip=True) if title else course["titulo"],
            "url": course["url"],
            "ultima_actualizacion": actualizacion.group(1) if actualizacion else "",
            "temas": " | ".join(temas),
            "descripcion": text[:3000]
        } 
        
    def scrape_aula_abierta(self):
        html = download_html(self.session,self.aula_url)
        categories_url = self.__get_categories_link(html)
        html = download_html(self.session,categories_url)
        sections =(self.__get_sections_links(html))
        for section in sections:
            if (section["nombre"]=="Catálogo de materiales"):
                html = download_html(self.session,section["url"])
                courses = self.__get_course_links(html)
                for course in courses:
                    course_data = self.__scrape_course(course)
                    course_data["origen"] = "Aula en Abierto"
                    self.data.append(course_data)
                    
    def scrape_formacion_abierta(self):
        pages = self.__get_formacion_abierta_pages()
        print(f"Páginas encontradas: {len(pages)}")
        for html in pages:
            soup = get_soup(html)
            modals = soup.find_all("div",attrs={"data-region":"block_coursecatalog_course_modal"})
            print(f"Cursos encontrados: {len(modals)}")
            for modal in modals:
                datos = self.__extract_modal_fields(modal)
                texto = modal.get_text(" ",strip=True)
                metadata = self.__extract_metadata(texto)
                self.data.append({
                    "id_curso": modal.get("id"),
                    "origen": "Formación Abierta",
                    "titulo": datos["titulo"],
                    "url": self.__get_course_url(modal),
                    "estado": metadata["estado"],
                    "modalidad": metadata["modalidad"],
                    "duracion": metadata["duracion"],
                    "fechas": metadata["fechas"],
                    "descripcion": datos["descripcion"],
                    "objetivos": datos["objetivos"],
                    "competencia_digital": datos["competencia_digital"],
                    "publico_objetivo": datos["publico_objetivo"],
                    "requisitos": datos["requisitos"]
                })

    def scrape_virtual_course(self,course):
        response = self.session.get(course["rul"],timeout=20,allow_redirects=True)
        acceso_restringido = (
            "Sí"
            if "login/index.php" in response.url
            else "No"
        )
        html = response.text
        soup = get_soup(html)
        descripcion = ""
        summary = soup.find("div",class_="content")
        if summary:
            descripcion = summary.get_text("",strip=True)
        return {
            "id_curso": self.__get_course_id(
                course["url"]
            ),
            "titulo": course["titulo"],
            "url": course["url"],
            "descripcion": descripcion,
            "acceso_restringido": acceso_restringido,
            "estado": "",
            "modalidad": "",
            "duracion": "",
            "fechas": "",
            "objetivos": "",
            "competencia_digital": "",
            "publico_objetivo": "",
            "requisitos": "",
            "ultima_actualizacion": "",
            "temas": ""
        }

    def scrape_aula_virtual(self):
        print("Extrayendo cursos de Aula Virtual...")
        html = download_html(self.session,self.virtual_url)
        courses = self.__get_virtual_course_links(html)
        print(f"Cursos encontrados: {len(courses)}")
        for course in courses:
            course_data = (self.__scrape_virtual_course(course))
            course_data["origen"] = ("Aula Virtual")
            self.data.append(course_data)
   
    def scrape(self):
        print("Extrayendo cursos de Formación Abierta...")
        self.scrape_formacion_abierta()
        print("Extrayendo cursos de Aula en Abierto...")
        self.scrape_aula_abierta()
        print("Extrayendo cursos de Aula Virtual...")
        self.scrape_aula_virtual()
        print(f"Total cursos recopilados: {len(self.data)}")

    def data2csv(self, filename):
        print("\nProceso finalizado.")
        print(f"Número de cursos encontrados: {len(self.data)}")
        df = pd.DataFrame(self.data)
        print("\nPrimeros registros:")
        print(df.head())
        print("\nInformación del dataset:")
        print(df.info())
        df.to_csv(
            filename,
            index=False,
            encoding="utf-8-sig"
        )
        print(f"\nDataset guardado correctamente en: {filename}")
        """ Dataset de muestra para GitHub"""
        sample_file = filename.replace(".csv", "_sample.csv")
        df.head(20).to_csv(sample_file,index=False,encoding="utf-8-sig")
        print(f"Muestra guardada correctamente en: {sample_file}")
        df[df["origen"] == "Formación Abierta"][["titulo", "url"]].head(20)
