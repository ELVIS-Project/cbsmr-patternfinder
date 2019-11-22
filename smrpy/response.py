import base64
import json
import math
import os
from functools import partial
from flask import url_for, request
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

def build_response(occs, qargs):
    pagination = Pagination(len(occs), qargs)

    pagination.pages = [occs[qargs.rpp * i : qargs.rpp * (i + 1)] for i in range(pagination.numPages)]
    for o in pagination.pages[qargs.page]:
        pass
        #o.update({'excerptUrl': url_for("excerpt", pid=o['pid'], nid=",".join(str(x) for x in excerptIndices))})

    return {
            "query": qargs.query,
            "pagination": asdict(pagination),
            "numPages": pagination.numPages,
            "range": pagination.range
            }

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
            self.numPages = int(self.numOccs / self.queryArgs.rpp) + 1
        else:
            self.numPages = 0

        self.range = calculate_page_range(self.queryArgs.page, self.numPages, 3)
        self.cur = self.queryArgs.page

        pagelink = partial(url_for, endpoint="search", **{param: request.args.get(param) for param in (x.name for x in fields(QueryArgs))})
        self.links = [pagelink(page=i) for i in self.range]
        self.previousLink = pagelink(page = self.cur - 1) if self.cur > 0 else None
        self.nextLink = pagelink(page=min(self.numPages, self.cur+1)),
        self.firstLink = pagelink(page=0)
        self.lastLink = pagelink(page=(self.numPages - 1)) if self.numPages > 0 else 0

def calculate_page_range(cur, total, numrange):
    page_nums = range(min(numrange, total))
    return tuple(map(lambda x: x + min(total - len(page_nums) + 1, cur), page_nums))
