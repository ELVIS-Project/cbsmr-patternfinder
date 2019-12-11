import music21
import click
import matplotlib.pyplot as plt
import numpy as np
from smrpy import indexers

@click.command()
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

if __name__ == "__main__":
    pointset()
