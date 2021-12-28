import requests
from bs4 import BeautifulSoup
import json
import pandas as pd

import you_get, sys

def download(url):
    sys.argv = ['you-get', '-o', './', url]
    you_get.main()

url = "https://www.bilibili.com/video/BV1oX4y1V7fT"
html = requests.get(url)
soup = BeautifulSoup(html.text, "html.parser")

text = soup.find_all('script')[4].text
start_pos = text.find('{')
end_pos = text.find(';')

data = json.loads(text[start_pos:end_pos])['videoData']

title = data['title']
desc = data['desc']
episodes = pd.DataFrame.from_dict(data['pages'])
episodes['title'] = title
episodes['desc'] = desc

episodes['url'] = f"{url}?p=" + episodes['page'].astype(str)

download(episodes.loc[0, 'url'])

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

episodes.to_csv('episodes.csv', index=False)