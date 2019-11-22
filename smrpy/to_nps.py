"""
python3 to_nps <piece>

Output:
(0,42)
(0,46)
(1,42)
...
(842,58)
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))

import music21
from indexers import NotePointSet
from piece import Note

def main():
    with open(sys.argv[1], "rb") as f:
        sd = f.read()

    nps = NotePointSet(music21.converter.parse(sd))
    for i, n in enumerate(nps):
        note = Note.from_m21(n, i)
        print(note)

if __name__ == '__main__':
    main()
