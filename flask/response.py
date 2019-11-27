import base64
import json
import math
import os
from functools import partial
from errors import *
from flask import url_for, request
from excerpt import coloured_excerpt
from dataclasses import dataclass, fields, asdict

@dataclass
class QueryArgs:
    rpp: int
    page: int
    tnps: tuple
    intervening: tuple
    inexact: int
    collection: int
    query: str

def available_search_options(db_conn):
    opts = {}
    with db_conn, db_conn.cursor() as cur:
        cur.execute(f"""
            SELECT id, name FROM Collection
        """)
        opts.update({'collections': [(cid, name) for cid, name in cur.fetchall()]})
    return opts

def build_response(db_conn, occs, qargs):
    pagination = Pagination(len(occs), qargs)
    pagination.pages = [
            [pb_occ_to_json(db_conn, o, get_excerpt = (i == qargs.page)) for o in occs[qargs.rpp * i : qargs.rpp * (i + 1)]]
            for i in range(pagination.numPages)]
    return {
            "query": qargs.query,
            "pagination": asdict(pagination),
            "numPages": pagination.numPages,
            "range": pagination.range
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
            resp["name"] = name[0]
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

@dataclass
class Pagination:
    numOccs: list
    queryArgs: QueryArgs

    range: tuple = ()
    cur: int = 0
    numPages = 0
    previousLink: str = ""
    nextLink: str = ""
    firstLink: str = ""
    lastLink: str = ""
    links: tuple = ()
    pages: tuple = ()

    def __post_init__(self):
        if self.queryArgs.rpp > 0:
            self.numPages = math.ceil(self.numOccs / self.queryArgs.rpp)
        else:
            self.numPages = 1

        self.cur = min(self.queryArgs.page, self.numPages)

        self.range = calculate_page_range(self.cur, self.numPages, 3)

        pagelink = partial(url_for, endpoint="search", **{param: request.args.get(param) for param in (x.name for x in fields(QueryArgs)) if param != 'page'})
        self.links = [pagelink(page=i) for i in self.range]
        self.previousLink = pagelink(page = self.cur - 1) if self.cur > 0 else None
        self.nextLink = pagelink(page=min(self.numPages-1, self.cur+1)),
        self.firstLink = pagelink(page=0)
        self.lastLink = pagelink(page=(self.numPages-1 if self.numPages > 0 else 0))

def calculate_page_range(cur, total, numrange):
    page_nums = range(0, min(numrange, total))
    if cur > 0:
        range_offset = min(total - len(page_nums), cur - int(len(page_nums) / 2))
    else:
        range_offset = 0
    return tuple(map(lambda x: x + range_offset, page_nums))
