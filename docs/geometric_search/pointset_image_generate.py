import music21
import click
import matplotlib.pyplot as plt
import numpy as np
from itertools import cycle
from smrpy import indexers

@click.group()
def cli():
    pass

@cli.command()
@click.argument("filename")
@click.argument("outname")
def pointset(filename, outname):
    """
    Converts a musicxml file to its point set image representation
    """
    st = music21.converter.parse(filename)
    nps = indexers.NotePointSet(st)

    offsets = np.array([n.offset for n in nps])
    pitches = np.array([n.pitch.ps for n in nps])
    pointset_plot = plt.scatter(offsets, pitches)

    plt.xlabel("Quarter-length offset")
    plt.ylabel("Chromatic pitch")
    plt.savefig(outname)

@cli.command()
@click.argument("filenames", nargs=-1)
@click.argument("outname")
def pointsets(filenames, outname):
    fig, ax = plt.subplots()
    colours = cycle(('#a50000', '#00a500', '#0000a5'))
    for label, filename, colour in zip(filenames[::2], filenames[1::2], colours):
        st = music21.converter.parse(filename) 
        nps = indexers.NotePointSet(st)
        offsets = np.array([n.offset for n in nps])
        pitches = np.array([n.pitch.ps for n in nps])
        ax.scatter(offsets, pitches, c=colour, label=label)
    ax.legend()
    ax.grid(True)
    plt.xlabel("Quarter-length offset")
    plt.ylabel("Chromatic pitch")
    fig.savefig(outname)

if __name__ == "__main__":
    cli()
