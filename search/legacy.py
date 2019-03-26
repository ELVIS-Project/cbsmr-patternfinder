from _w2 import ffi, lib


def filter_chain(chain, window, num_notes):
    ok = (
        sum((r - l <= window) for l, r in zip(chain, chain[1:])) == len(chain) - 1
        and len(chain) >= num_notes)
    if not ok:
        print("Didn't pass filter: " + str(chain))
    return ok

def recursively_extract_chain(KEntry):
    if KEntry.y == ffi.NULL:
        return [KEntry.targetVec.startIndex, KEntry.targetVec.endIndex]
    else:
        return recursively_extract_chain(KEntry.y) + [KEntry.targetVec.endIndex]

def extract_chains(KTable, KTable_length):

    chains = []

    for i in range(KTable_length):
        if KTable[i].w > 0:
            chains.append(recursively_extract_chain(KTable[i]))

    return chains