import subprocess
import typer

app = typer.Typer()

def fetch_content_table(url: str):
    output = subprocess.check_output(['you-get', '-l', '--json', url], encoding='utf-8')
    print(output)
    with open('output.json', 'w') as f:
        f.write(output)

@app.command()
def run():
    fetch_content_table('https://www.bilibili.com/video/BV1RM4y1P7pU?from=search&seid=17136688886877015681')

if __name__ == '__main__':
    app()