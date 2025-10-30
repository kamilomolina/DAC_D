import requests

def get_laravel_content(site):
    url = site
    response = requests.get(site)
    if response.status_code == 200:
        return response.text
    else:
        return 'Contenido no disponible'