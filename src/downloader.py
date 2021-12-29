
url = "https://www.bilibili.com/video/BV1Ti4y1Z7nP?from=search&seid=16593024632196733175&spm_id_from=333.337.0.0"
author = '罗伯特·戴博德'
title='蛤蟆先生去看心理医生'


import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from pathlib import Path

import you_get, sys
import subprocess
import ffmpeg

def download(url, output_name):
    sys.argv = ['you-get', '-o', download_dir, '-O', output_name, url]
    you_get.main()

def extract_sound(video_file):
    audio_file = f"test.m4b"
    cmd = f"ffmpeg -i {video_file} -vn -acodec copy {audio_file}"


def extract_audio(episode : dict):
    """
    command = ffmpeg 
        -y
        -hide_banner
        -i {input_file}
        -vn 
        -acodec copy 
        -metadata title="{chapter_title}"
        -metadata track="{chapter}"
        -metadata artist="{author}"
        -metadata desc="{desc}"
        -metadata composer="{data['owner']['name']}"
        "{audio_file}" 
    subprocess.run(command)    
    
    """

    input_file = list(Path(download_dir).glob(f"{episode['page']}.*"))[0].as_posix()


    metadata = {
        'title': episode['part'],
        'track': f"{episode['page']:02}" if episodes_num < 100 else f"{episode['page']:03}",
        'artist': author,
        'desc': desc,
        'composer': data['owner']['name']
    }
    meta = {}
    for key in metadata.keys():
        meta[f'metadata:g:{key}'] = f"{key}={metadata[key]}"
    
    print(meta)
    out = (ffmpeg
        .input(input_file)
        .output(audio_file, vn=None, acodec='copy', **meta)
        .overwrite_output()
        .run()
    )
    # print(command)


download_dir = Path(f'./download/{author}/{title}')
audio_dir = Path(f'./audio/{author}/{title}')

download_dir.mkdir(parents=True, exist_ok=True)
audio_dir.mkdir(parents=True, exist_ok=True)

# Remove the parameters
parts = requests.utils.urlparse(url)
url = requests.utils.urlunparse((parts.scheme, parts.netloc, parts.path, "", "", ""))

html = requests.get(url)
soup = BeautifulSoup(html.text, "html.parser")

text = soup.find_all('script')[4].text
start_pos = text.find('{')
end_pos = text.find(';')

data = json.loads(text[start_pos:end_pos])['videoData']

title = title if title else data['title']
desc = data['desc']


episodes = data['pages']
episodes_num = len(episodes)
for episode in episodes:
    """
    "cid": 455646461,
    "page": 1,
    "from": "vupload",
    "part": "01 整个人都不太好",
    "duration": 629,
    "vid": "",
    "weblink": "",
    "dimension": {
        "width": 320,
        "height": 240,
        "rotate": 0
    },
    """
    chapter = f"{episode['page']:02}" if episodes_num < 100 else f"{episode['page']:03}"
    chapter_title = episode['part']
    download_file = (download_dir / chapter).as_posix()
    episode_url = f'{url}?p={episode["page"]}'

    audio_file = ((audio_dir) / f"{chapter}_{chapter_title.replace(' ', '_')}.m4b").as_posix()

    episode['url'] = episode_url
    episode['download_file'] = download_file
    episode['audio_file'] = (audio_dir / audio_file).as_posix()
    # Download
    episode['download_cmd'] = ' '.join(f"""you-get
        -O {download_file} {episode_url}
    """.split())
    # FFMPEG command
    # episode['ffmpeg']  = ' '.join(f"""ffmpeg 
    #     -y
    #     -hide_banner
    #     -i $(ls {download_file}.*)
    #     -vn 
    #     -acodec copy 
    #     -metadata title="{chapter_title}"
    #     -metadata track="{chapter}"
    #     -metadata artist="{author}"
    #     -metadata desc="{desc}"
    #     -metadata composer="{data['owner']['name']}"
    #     "{audio_file}" """.split()) #.replace('\n', ' ')
    # episode['ffmpeg'] = [
    #     'ffmpeg',
    #     '-y',
    #     '-hide_banner',
    #     '-i', f"{download_file}.mp4",
    #     '-vn',
    #     '-acodec', 'copy',
    #     audio_file
    # ]

    # print(e)



for episode in [episodes[10]]:
    print(episode)
    print(episode['download_cmd'])
    # subprocess.check_output(episode['download_cmd'].split())
    
    # print(episode['ffmpeg'])
    # subprocess.run(episode['ffmpeg'].split())
    extract_audio(episode)
    # out = (
    #     ffmpeg
    #     .input(episode['download_file'])
    #     .output(episode['audio_file'])
    #     .overwrite_output()
    #     .run_async(pipe_stdout=True, pipe_stderr=True)
    # )


    # out.wait()



# episodes = pd.DataFrame.from_dict(data['pages'])
# episodes['title'] = title
# episodes['desc'] = desc

# episodes['url'] = f"{url}?p=" + episodes['page'].astype(str)

# download(episodes.loc[0, 'url'])

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

# episodes.to_csv('episodes.csv', index=False)