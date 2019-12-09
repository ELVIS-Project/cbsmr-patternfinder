import os
import click
import json
import music21
from dataclasses import dataclass, asdict

FILENAME_PARSERS = ['elvis', 'chorale', 'palestrina']
NUM_PIECES_PER_COLLECTION = 100000

def unique_index(i, collection_id):
    base = NUM_PIECES_PER_COLLECTION * collection_id
    return base + i

@dataclass
class Metadata:
    pid: int
    fmt: str = ''
    name: str = '' 
    composer: str = ''
    collection_id: int = ''
    filename: str = ''

    @classmethod
    def from_path(cls, tp, path):
        try:
            return globals()['parse_' + tp + '_piece_path'](path)
        except KeyError:
            raise NotImplementedError

    @classmethod
    def from_path_and_env(cls, path):
        for k in FILENAME_PARSERS:
            if os.getenv("PARSE_" + k.upper()):
                return cls.from_path(k.lower(), path)
        raise NotImplementedError

def parse_chorale_piece_path(piece_path):
    collection_id = 2
    fmt = 'krn'
    basename, _ = os.path.splitext(os.path.basename(piece_path))
    index = int(basename[-3:])
    name = music21.converter.parse(piece_path).metadata.title
    return Metadata(unique_index(index, collection_id), fmt, name, 'Bach', collection_id, piece_path)
def parse_elvis_piece_path(piece_path):
    collection_id = 1
    basename, fmt = os.path.splitext(os.path.basename(piece_path))
    fmt = fmt[1:] # skip '.'
    base = [x.replace('-', ' ') for x in os.path.basename(basename).split("_") if not "file" in x]
    piece_id = int(base[0])
    name = ' - '.join(base[1:-1])
    composer = base[-1]
    return Metadata(piece_id, fmt, name, composer, collection_id, piece_path)
def parse_palestrina_piece_path(piece_path):
    collection_id=3
    fmt = 'mid'
    basename, _ = os.path.splitext(os.path.basename(piece_path))
    xs = basename.split('_')
    name = " ".join(xs[:-2])
    num_voices = xs[-1]
    movement = xs[-2]
    return Metadata(pid=None, fmt=fmt, name=f"{name} {movement[0].upper()}{movement[1:]} à {num_voices}", composer='Palestrina', collection_id=collection_id, filename=piece_path)

@click.command()
@click.option("-t", default="elvis", help=" || ".join(FILENAME_PARSERS))
@click.argument("filename")
def parse(t, filename):
    md = Metadata.from_path(t, filename)
    print(json.dumps(asdict(md)))

def main():
    parse()

if __name__ == '__main__':
    main()
