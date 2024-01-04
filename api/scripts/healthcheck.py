import sys

import requests

url = "http://localhost:8000/health"
status = requests.get(url).status_code

sys.exit(0 if 200 >= status < 300 else 1)
