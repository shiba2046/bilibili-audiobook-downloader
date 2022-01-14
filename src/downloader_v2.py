
import typer
import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import subprocess
import ffmpeg
import multiprocessing as mp

app = typer.Typer()


class Book(object):
    def __init__(self, book_data: dict):
        self.video_data = book_data
        self.count = book_data['videos']
        
        self.desc = book_data['desc']
        self.video_id = book_data['bvid']
        self.episodes = [Episode(x, self) for x in book_data['pages']]
    
        self.title = book_data['title']
        if len(self.title) > 10:
            self.title = input(f"书籍名称 [{self.title}] : ") or self.title
        
        self.author = input(f"作者名称  : ") 


class Episode(object):
    def __init__(self, episode_data: dict, book: object = None):
        # typer.echo(episode_data)
        self.raw_data = episode_data
        
        self.index = episode_data['page'] 
        
        self.title = episode_data['part']
        self.filename = f"{self.index:02}.{self.title}".replace(' ', '.')
        
        

class BilibiliAudiobookDownloader(object):
    def __init__(self, 
            url: str, 
            download_path: str = './download',
            audio_path: str = './audio',
            book_title: str = None,
            author: str = None,
            dry_run: bool = False):

        
        self.data = self.fetch_content_table(url)
        self.video_data = self.data['videoData']
        # Create book
        self.book = Book(self.video_data)

        self.download_path = Path(download_path) / self.book.title
        self.download_path.mkdir(parents=True, exist_ok=True)
        self.audio_path = Path(audio_path) / self.book.title
        self.audio_path.mkdir(parents=True, exist_ok=True)



    def fetch_content_table(self, url: str):
        # Only keep the top most parts

        url_parts = requests.utils.urlparse(url)
        self.base_url = requests.utils.urlunparse((url_parts.scheme, url_parts.netloc, url_parts.path, "", "", ""))

        html = requests.get(url)
        
        if html.status_code != 200:
            typer.secho(f"Failed to fetch the page. Error code {html.status_code}", fg="red")
            typer.Exit(-1)

        soup = BeautifulSoup(html.text, "html.parser")
        
        

        # TODO: IF BILIBILI CHANGES WEBSITE THIS NEEDS TO CHANGE
        text = soup.find_all('script')[4].text
        start_pos = text.find('{')
        end_pos = text.find('};') + 1

        # data = json.loads(text[start_pos:end_pos])
        # print(data.keys)

        # temp = Path('./temp')
        # temp.mkdir(parents=True, exist_ok=True)
        # TODO: FOR DEBUGGING
        # with open(self.download_path / 'debug.html', 'w') as f:
        #     f.write(text)

        # with open(self.download_path / 'debug.txt', 'w') as f:
        #     f.write(text[start_pos:end_pos])

        # filename = f'{self.download_path / self.book.title}.json' 
        # with open(filename, 'w', encoding='utf-8') as f:
        #     json.dump(self.data, f, ensure_ascii=False, indent=4)        
        
        return json.loads(text[start_pos:end_pos])


    def download_episode(self, episode: Episode):

        url = f"{self.base_url}?p={episode.index}"
        download_file = (self.download_path / str(episode.index)).as_posix()
        audio_file = (self.audio_path / f"{episode.filename}.m4b").as_posix()

        # Download the video
        typer.echo(f"Downloading {episode.title}")
        subprocess.run(['you-get', '--no-caption', '-O', download_file, url])

        download_file = next(self.download_path.glob(f"{episode.index}.*")).as_posix()
        metadata = {
            'title': episode.title,
            'track': episode.index,
            'album': self.book.title,
            'artist': self.book.author,
            'album_artist': self.book.author,
            'description': self.book.desc,
        }
        meta = {}
        for key in metadata.keys():
            meta[f'metadata:g:{key}'] = f"{key}={metadata[key]}"
        
        typer.echo(f"Converting {episode.title}; meta: {meta}")
        out = (ffmpeg
            .input(download_file)
            .output(audio_file, vn=None, acodec='copy', **meta)
            # .overwrite_output()
            .global_args('-loglevel', 'quiet')
            .run()
        )

    

    def download_all_episodes_mp(self):
        with mp.Pool(mp.cpu_count()) as pool:
            pool.map(self.download_episode, self.book.episodes)


        
    
    def download_all_episodes(self):
        for episode in self.book.episodes:
            self.download_episode_mp(episode)

@app.command()
def download(
    url: str = None, 
    download_path: str = './download', 
    audio_path: str = './audiobooks',
    book_title: str = None,
    author: str = None,
    dry_run: bool = False,
    ):
    
    if url is None:
        url = input("Bilibili Audio Book URL : ")
    
    b = BilibiliAudiobookDownloader(url= url, 
            download_path= download_path, 
            audio_path= audio_path,
            book_title= book_title,
            author= author,
            dry_run = dry_run)

    
    b.download_all_episodes()
    # b.download_all_episodes_mp()
    # b.download_episode(b.book.episodes[23])
    # b.download_episode(b.book.episodes[26])

@app.command()
def extract_audio(path: str):
    typer.echo(f"Extracting audio from {path}")
    out = (ffmpeg
        .input(path)
        .output(f"{path}.m4b", vn=None, acodec='copy')
        .overwrite_output()
        .global_args('-loglevel', 'quiet')
        .run()
    )

@app.command()
def down_sample(path: str):
    path = Path(path)
    if not path.exists():
        typer.secho(f"{path} does not exist", fg="red")
        typer.Exit(-1)
    typer.echo(f"Downsizing {path}")

    files = list(path.glob('*.m4b'))
    typer.echo(f"Found {len(files)} files")

    for file in files:
        ffmpeg_64k(file)

    # with mp.Pool(mp.cpu_count()) as pool:
    #     pool.map(ffmpeg_64k, files)

def ffmpeg_64k(file):
    typer.echo(f"Downsampling {file}")
    out = (ffmpeg
        .input(file)
        .output(f"{file.stem}.64k.m4b", ba='64k')
        .global_args('-loglevel', 'quiet')
        .run()
    )
    print(f"{file.stem}.64k.m4b")

if __name__ == '__main__':
    app()