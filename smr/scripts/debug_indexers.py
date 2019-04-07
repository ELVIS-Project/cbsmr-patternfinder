import os
import sys
import itertools
import pickle
from tqdm import tqdm
from indexers import intra_vectors, notes

ELVISDUMP = "/Users/davidgarfinkle/elvis-project/elvisdump"

def main():
    failed_notes = {}
    failed_vectors = {}
    for subdir in ("MEI", "XML", "MID"):
        directory = os.path.join(ELVISDUMP, subdir)
        print(f"Processing {directory}")
        for fl in tqdm(os.listdir(directory)):
            filepath = os.path.abspath(os.path.join(directory, fl))
            try:
                notes(filepath)
            except Exception as e:
                failed_notes[e.__class__] = failed_notes.get(e.__class__, [])
                failed_notes[e.__class__].append((filepath, str(e)))
            try:
                intra_vectors(filepath)
            except Exception as e:
                failed_vectors[e.__class__] = failed_vectors.get(e.__class__, [])
                failed_vectors[e.__class__].append((filepath, str(e)))
    
        with open('./failed_notes.pkl', 'wb') as f:
            pickle.dump(failed_notes, f)
        with open('./failed_intervals.pkl', 'wb') as f:
            pickle.dump(failed_vectors, f)



if __name__ == "__main__":
    main()