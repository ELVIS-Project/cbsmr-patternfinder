import base64
import json
import math
import os
from functools import partial
from errors import *
from flask import url_for
from excerpt import coloured_excerpt

def build_response(db_conn, occs, rpp, page, tnps, intervening, query, inexact):
    if rpp > 0:
        num_pages = int(len(occs) / rpp) + 1
    else:
        num_pages = 0
    paginator_range = calculate_page_range(page, num_pages)

    pagelink = partial(url_for, endpoint="search", inexact=inexact, query=query, rpp=rpp, tnps=tnps, intervening=intervening)
    return {
        'paginatorLinks': [pagelink(page=i) for i in paginator_range],
        'previousPageLink': pagelink(page=max(0, page-1)),
        'nextPageLink': pagelink(page=min(num_pages, page+1)),
        'firstPage': pagelink(page=0),
        'lastPage': pagelink(page=(num_pages-1)),
        'paginatorRange': paginator_range,
        'totalCount': len(occs),
        'pagesCount': num_pages,
        'query': query,
        'rpp': rpp,
        'curPage': page,
        'pages': [
            [pb_occ_to_json(db_conn, o, get_excerpt = (i == page)) for o in occs[rpp * i : rpp * (i + 1)]]
            for i in range(num_pages)]
    }

def pb_occ_to_json(db_conn, pb_occ, get_excerpt):

    excerptIndices = [n.piece_idx for n in pb_occ.notes]
    pid = str(pb_occ.pid)

    resp = {
        "excerptFailed": False,
        "excerptSkipped": True,
        "pid": pid,
        "excerptUrl": url_for("excerpt", pid=pid, nid=",".join(str(x) for x in excerptIndices))
    }

    with db_conn, db_conn.cursor() as cur:
        cur.execute(f"SELECT name FROM Piece WHERE pid={pb_occ.pid}")
        if cur.rowcount == 0:
            raise DatabasesOutOfSyncError(f"pid {pb_occ.pid} does not exist in the flask database")
        name = cur.fetchone()
        if name and name[0]:
            resp["name"] = " ".join(os.path.basename(name[0]).split("_")[1:])
        else:
            resp["name"] = "no name info"

    if get_excerpt:
        try:
            raise Exception("skipping server-side rendering")
            xml = coloured_excerpt(db_conn, excerptIndices, pb_occ.pid)
        except Exception as e:
            b64_xml = "excerpt failed: " + str(e)
            resp["excerptFailed"] = True
        else:
            b64_xml = base64.b64encode(bytes(xml, encoding='utf-8')).decode('utf-8')
            resp["excerptSkipped"] = False
    else:
        b64_xml = ""

    resp["xmlBase64"] = b64_xml

    return resp

def calculate_page_range(cur, total):
    """
    page_nums = range(num)
    if total - cur < num / 2:
        page_nums = map(lambda x: x + total - num, page_nums)
    elif cur > num / 2:
        page_nums = map(lambda x: x + cur, page_nums)
    """
    if cur == 0 or cur == 1:
        return list(range(3))
    elif total - cur < 3:
        return list(range(cur, total))
    else:
        return [cur-1, cur, cur+1]
