import base64
import json
import math
from flask import url_for
from excerpt import coloured_excerpt

def build_response(db_conn, occs, rpp, page, query):
    if rpp > 0:
        num_pages = int(len(occs) / rpp) + 1
    else:
        num_pages = 0
    paginator_range = calculate_page_range(5, page, num_pages)

    return {
        'paginatorLinks': [url_for("search", query=query, page=i, rpp=rpp) for i in paginator_range],
        'paginatorRange': paginator_range,
        'totalCount': len(occs),
        'pagesCount': num_pages,
        'query': query,
        'rpp': rpp,
        'curPage': page,
        'pages': [
            [pb_occ_to_json(db_conn, o, get_excerpt = (i == page)) for o in occs[rpp * i : rpp * (i + 1)]]
            for i in paginator_range]
    }

def pb_occ_to_json(db_conn, pb_occ, get_excerpt):

    resp = {
        "excerptFailed": False,
        "excerptSkipped": True,
        "pid": pb_occ.pid
    }

    if get_excerpt:
        try:
            xml = coloured_excerpt(db_conn, pb_occ.notes, pb_occ.pid)
        except Exception as e:
            b64_xml = "excerpt failed: " + str(e)
            resp["excerptFailed"] = True
        else:
            b64_xml = base64.b64encode(bytes(xml, encoding='utf-8')).decode('utf-8')
            resp["excerptSkipped"] = False
    else:
        b64_xml = ""

    resp["url"] = url_for("excerpt", pid=pb_occ.pid, nid=",".join(str(x) for x in pb_occ.notes))
    resp["xmlBase64"] = b64_xml

    return json.dumps(resp)

def calculate_page_range(num, cur, total):
    page_nums = range(num)
    if total - cur < 3:
        page_nums = map(lambda x: x + total - num, page_nums)
    elif cur > 2:
        page_nums = map(lambda x: x + math.floor(cur / 2))
    return list(page_nums)
