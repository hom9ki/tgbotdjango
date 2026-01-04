from zipfile import ZipFile
from pathlib import Path




def file_compress(file):
    folder = Path.cwd()
    parent = folder.parents[1]
    suddir = parent.joinpath('uploads')
    if suddir.exists():
        print(suddir)
    files = list(suddir.glob('**/*'))
    for file in files:
        print(file.relative_to(suddir))
        with open(file, 'r', encoding='utf-8') as f_in:
            print(f_in)

file_compress('abc.txt')