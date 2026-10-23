import time
import requests
from bs4 import BeautifulSoup

def create_session(user_agent):
    session = requests.Session()
    session.headers.update({
        "User-Agent": user_agent
    })
    return session

def download_html(session, url):
    time.sleep(2)
    response = session.get(
        url,
        timeout=20
    )
    response.raise_for_status()
    return response.text

def get_soup(html):
    return BeautifulSoup(
        html,
        "html.parser"
    )
