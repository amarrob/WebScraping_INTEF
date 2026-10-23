import re
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin


def connect(url, user_agent, timeout=20):
    """
    Establece conexión con la página y devuelve:
    - response
    - soup
    - session
    """

    session = requests.Session()

    session.headers.update({
        "User-Agent": user_agent
    })

    response = session.get(
        url,
        timeout=timeout
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    return response, soup, session


def get_sesskey(html):
    """
    Extrae el sesskey presente en el código fuente.
    """

    match = re.search(
        r'"sesskey"\s*:\s*"([^"]+)"',
        html
    )

    if not match:
        raise ValueError(
            "No se ha encontrado el sesskey en el HTML"
        )

    return match.group(1)


def get_ajax_url(base_url):
    """
    Construye la URL del servicio AJAX de Moodle.
    """

    return urljoin(
        base_url,
        "lib/ajax/service.php"
    )
