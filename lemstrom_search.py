"""
pid  |   p_notes   |   t_notes   | t_nids  
-------+-------------+-------------+---------
 10919 | {1,10,1,14} | {0,55,0,59} | {0,1}
"""
import itertools
import heapq

def search(p_nids, t_nids, len_pattern, threshold):

    def should_discard_from_queue(row):
        if not queue:
            return False
        _, chain = queue[0]
        (pre_pl, pre_pr), (pre_tl, pre_tr) = chain[-1]
        (next_pl, next_pr), (next_tl, next_tr) = row
        return pre_pr < next_pl or pre_tr < next_tl or pre_pr < next_pl

    def should_extend_from_queue(row):
        if not queue:
            return False
        _, chain = queue[0]
        (pre_pl, pre_pr), (pre_tl, pre_tr) = chain[-1]
        (next_pl, next_pr), (next_tl, next_tr) = row
        return pre_tr == next_tl and pre_pr == next_pl

    assert len(p_nids) > 0
    assert len(t_nids) > 0

    queue = []
    results = set()
    
    for (pl, pr), (tl, tr) in zip(p_nids, t_nids):
        heapq.heappush(queue, ((pr, tr, tl), (((pl, pr), (tl, tr)),)))

    for table_row in zip(p_nids, t_nids):
        if not queue:
            break

        #print("considering row ", table_row)

        (pl, pr), (tl, tr) = table_row
        if pl < queue[0][0][0]:
            #print("pl less than ", queue[0][0][0], " skipping...")
            continue

        while should_discard_from_queue(table_row):
            #print("discarding ", queue[0])
            heapq.heappop(queue)

        max_length_so_far = float('-inf')
        max_chain = ()

        while should_extend_from_queue(table_row):
            _, candidate_chain = heapq.heappop(queue)
            if len(candidate_chain) >= max_length_so_far:
                max_chain = candidate_chain
                max_length_so_far = len(max_chain)
                new_chain = max_chain + (table_row,)
                if len(new_chain) >= threshold:
                    results.add(new_chain)

                (pl, pr), (tl, tr) = table_row
                #print("pushing ", new_chain)
                heapq.heappush(queue, ((pr, tr, tl), new_chain))

    return results

def test_search():
    def compute_vectors(pattern, target):
        p_vecs = [(si, ei, x2 - x1, y2 - y1) for (si, (x1, y1)), (ei, (x2, y2)) in itertools.combinations(enumerate(pattern), 2) if ei - si < 5]
        t_vecs = [(si, ei, x2 - x1, y2 - y1) for (si, (x1, y1)), (ei, (x2, y2)) in itertools.combinations(enumerate(target), 2) if ei - si < 5]

        tables = []
        for psi, pei, px, py in p_vecs:
            for tsi, tei, tx, ty in t_vecs:
                if (py == ty) and not ((px == 0 and tx != 0) or (px != 0 and tx == 0)):
                    tables.append(((psi, pei), (tsi, tei)))

        def table_sort(tpl):
            (psi, pei), (tsi, tei) = tpl
            return (psi, tsi, tei, pei)
        tables.sort(key=table_sort)
        p_nids, t_nids = zip(*tables)
        return p_nids, t_nids

    pattern = [
        (0.0, 67),
        (0.5, 70),
        (1.0, 69),
        (1.5, 62),
        (2.0, 69),
        (3.0, 67)
    ]

    target = [
        (0.0,45.0),
        (0.0,52.0),
        (0.0,57.0),
        (0.0,57.0),
        (0.5,64.0),
        (1.0,62.0),
        (1.5,60.0),
        (2.0,56.0),
        (2.0,59.0),
        (2.5,52.0),
        (3.0,45.0),
        (3.0,52.0),
        (3.0,57.0),
        (3.0,57.0),
        (3.5,60.0),
        (4.0,56.0),
        (4.0,59.0),
        (4.5,52.0),
        (5.0,59.0),
        (6.0,45.0),
        (6.0,52.0),
        (6.0,57.0),
        (6.0,69.0),
        (6.25,76.0),
        (6.5,74.0),
        (6.75,77.0),
        (7.0,76.0),
        (7.5,60.0),
        (7.5,69.0),
        (8.0,59.0),
        (8.0,71.0),
        (8.5,57.0),
        (8.5,72.0)
    ]

    p_nids, t_nids = compute_vectors(pattern, target)
    results = search(p_nids, t_nids, len(pattern))
    for v in results:
        print(v)
    import time
    for multiplier in range(1, 100):
        multiplied_target = target * multiplier
        p_nids, t_nids = compute_vectors(pattern, multiplied_target)
    
        total = 0
        num_trials = 10
        for _ in range(num_trials):
            st = time.time()
            results = search(p_nids, t_nids, len(pattern))
            et = time.time()
            total += (et - st) / num_trials

        print(multiplier, len(multiplied_target), total)
