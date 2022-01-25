# import logging
from fastapi import logger as fastapi_logger
from fastapi.responses import PlainTextResponse

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from fastapi_pagination import add_pagination

from fastapi_pagination.ext.sqlalchemy import paginate as sql_paginate

# from fastapi_pagination.ext.databases import paginate as sql_paginate

from fastapi_pagination.paginator import paginate as paginate_list

from fastapi_limiter.depends import RateLimiter
from networkx.algorithms import cycles

from sqlalchemy.orm import Session

import ulid
import pandas as pd
import networkx as nx
import networkx.algorithms.centrality as nxc

import io


from grrm import schemas
from grrm.crud import Database
from service.database import session
from grrm import models

from fastapi_pagination import Page, add_pagination, paginate
from .helpers import MapPage, ItemsPage
from .utils import get_structure, get_graph

# pagination_params = using_params(CustomPaginationParams)
# items_pagination_params = using_params(ItemsPaginationParams)

# logger = logging.getLogger(__name__)
logger = fastapi_logger.logger


router = APIRouter()


# @router.get("/")
# async def index():
#     return {
#         "apis": [
#             "/maps",
#         ]
#     }


@router.get("/stats")
async def get_stats(
    db: Session = Depends(session),
):


    maps = Database.get_accessible_maps(db)
    maps_count = maps.count()

    eqs = db.query(models.Eq).filter(models.Eq.map_id.in_(m.id for m in maps.all()))
    eqs_count = eqs.count()

    edges =  db.query(models.Edge).filter(models.Edge.map_id.in_(m.id for m in maps.all()))
    edges_count = edges.count()

    return {
        "maps": maps_count,
        "eqs": eqs_count,
        "edges": edges_count,
    }


@router.get(
    "/maps",
    response_model=MapPage[schemas.GRRMMap],
    dependencies=[
        # Depends(RateLimiter(times=10, seconds=5)),
    ],
)
async def get_maps(
    atoms: Optional[str] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    sort: Optional[str] = None,
    smiles: Optional[str] = None,
    db: Session = Depends(session),
):
    """
    Maps

    :param db: DB Session
    :return: Maps
    :rtype: JSON or CSV
    :exception: HTTPException(404)
    """

    if smiles:
        maps = Database.get_maps_with_smiles(db, smiles, sort)
        if maps:
            return sql_paginate(maps)

    in_atoms = []
    if atoms:
        in_atoms = list(set(atoms.split(",")))

    maps = Database.get_accessible_maps(db, in_atoms, before, after, sort)

    if maps:
        return sql_paginate(maps)

    raise HTTPException(status_code=404, detail=f"maps not found")


@router.get(
    "/maps/{map_id}",
    response_model=schemas.GRRMMap,
    # dependencies=[Depends(RateLimiter(times=10, seconds=5))],
)
async def get_map(
    map_id: str,
    db: Session = Depends(session),
):
    """
    Map metadata
    :param map_id: grrm map id
    :param db: DB Session
    :return: Map metadata
    :rtype: JSON or CSV
    :exception: HTTPException(404)
    """

    map = Database.get_map(db, map_id)
    if map:
        return map
    raise HTTPException(status_code=404, detail=f"map not found: {map_id}")


@router.get(
    "/maps/{map_id}/init-structure",
    response_class=PlainTextResponse,
    dependencies=[
        # Depends(items_pagination_params),
        # Depends(RateLimiter(times=10, seconds=5)),
    ],
)
async def get_map_init_structure(
    map_id: str, format: Optional[str] = "xyz", db: Session = Depends(session)
):
    map = Database.get_map(db, map_id)
    map_xyz = map.initxyz

    response = get_structure(map.atom_name, map.initxyz, format)

    if response:
        return response

    raise HTTPException(
        status_code=404, detail=f"Structure is not found on map: {map_id}"
    )


@router.get(
    "/maps/{map_id}/n0-structure",
    response_class=PlainTextResponse,
    dependencies=[
        # Depends(items_pagination_params),
        # Depends(RateLimiter(times=10, seconds=5)),
    ],
)
async def get_map_n0_structure(
    map_id: str, format: Optional[str] = "xyz", db: Session = Depends(session)
):
    map = Database.get_map(db, map_id)
    n0 = Database.get_eqs(db, map_id).filter(models.Eq.nid == 0).first()

    response = get_structure(map.atom_name, n0.xyz, format)

    if response:
        return response

    raise HTTPException(
        status_code=404, detail=f"Structure is not found on map: {map_id}"
    )


@router.get(
    "/maps/{map_id}/graph",
    response_class=PlainTextResponse,
    dependencies=[
        # Depends(items_pagination_params),
        # Depends(RateLimiter(times=10, seconds=5)),
    ],
)
async def get_map_graph(
    map_id: str, format: Optional[str] = "csv", db: Session = Depends(session)
):
    response = Database.get_graph(db, map_id)

    if response:
        return response

    raise HTTPException(
        status_code=404, detail=f"Structure is not found on map: {map_id}"
    )


@router.get(
    "/maps/{map_id}/eqs",
    response_model=ItemsPage[schemas.EqAbr],
    dependencies=[
        # Depends(items_pagination_params),
        # Depends(RateLimiter(times=10, seconds=5)),
    ],
)
async def get_eqs_in_map(
    map_id: str, sort: Optional[str] = None, db: Session = Depends(session)
):
    """
    Find Eqs in the specified map
    :param db: DB Session
    :return: Maps
    :rtype: JSON or CSV
    :exception: HTTPException(404)
    """
    eqs = Database.get_eqs(db, map_id, sort)
    if eqs:
        return sql_paginate(eqs)
    raise HTTPException(status_code=404, detail=f"Eqs are not found on map: {map_id}")


@router.get(
    "/maps/{map_id}/eqs/stats",
    response_model=List[schemas.EqStats],
    dependencies=[
        # Depends(items_pagination_params),
        # Depends(RateLimiter(times=10, seconds=5)),
    ],
)
async def get_eq_stats_in_map(
    map_id: str,
    measure: Optional[str] = None,
    sort: Optional[str] = None,
    db: Session = Depends(session),
):
    eqs = Database.get_eqs(db, map_id, sort)
    print(eqs.count())

    csv = Database.get_graph(db, map_id)
    df = pd.read_csv(io.StringIO(csv), index_col=0)

    #

    if eqs:
        eq_list = eqs.all()
        m = 0

        if measure:

            if measure == "frequency":
                fs = df["n0"].value_counts()

                for eq in eq_list:
                    eq.frequency = (
                        0
                        if len(fs[fs.index == ulid.from_bytes(eq.id).str].values) == 0
                        else fs[fs.index == ulid.from_bytes(eq.id).str].values[0]
                    )

            elif measure == "betweenness":
                G = nx.from_pandas_edgelist(df, source="n0", target="n1")
                bc = nxc.betweenness_centrality(G)

                for eq in eq_list:
                    eq.measure = bc.get(ulid.from_bytes(eq.id).str, None)

            elif measure == "closeness":
                G = nx.from_pandas_edgelist(df, source="n0", target="n1")
                cc = nxc.closeness_centrality(G)

                for eq in eq_list:
                    eq.measure = cc.get(ulid.from_bytes(eq.id).str, None)

            elif measure == "pagerank":
                G = nx.from_pandas_edgelist(df, source="n0", target="n1")
                pr = nx.pagerank(G)

                for eq in eq_list:
                    eq.measure = pr.get(ulid.from_bytes(eq.id).str, None)

        return eq_list

    raise HTTPException(status_code=404, detail=f"Eqs are not found on map: {map_id}")


@router.get(
    "/eq_measures/{eq_id}",
    response_model=schemas.EqMeasure,
    # dependencies=[Depends(RateLimiter(times=10, seconds=5))],
)
async def get_eq_measure(eq_id: str, db: Session = Depends(session)):
    """
    Eq measure
    :param eq_id: grrm eq id
    :param db: DB Session
    :return: Eq metadata
    :rtype: JSON or CSV
    :exception: HTTPException(404)
    """
    eq = Database.get_eq_measure(db, eq_id)
    if eq:
        return eq
    raise HTTPException(status_code=404, detail=f"eq measure not found: {eq_id}")



@router.get(
    "/maps/{map_id}/eqs/measures",
    response_model=List[schemas.EqMeasure],
    dependencies=[
        # Depends(items_pagination_params),
        # Depends(RateLimiter(times=10, seconds=5)),
    ],
)
async def get_eq_measures_in_map(
    map_id: str,
    sort: Optional[str] = None,
    db: Session = Depends(session),
):

    print("----")
    eq_measures = Database.get_eq_measures(db, map_id)

    print(eq_measures.count())
    print(eq_measures.first())


    return eq_measures.all()


    raise HTTPException(status_code=404, detail=f"Eqs are not found on map: {map_id}")


@router.get(
    "/eqs/{eq_id}",
    response_model=schemas.Eq,
    # dependencies=[Depends(RateLimiter(times=10, seconds=5))],
)
async def get_eq(eq_id: str, db: Session = Depends(session)):
    """
    Eq metadata
    :param eq_id: grrm eq id
    :param db: DB Session
    :return: Eq metadata
    :rtype: JSON or CSV
    :exception: HTTPException(404)
    """
    eq = Database.get_eq(db, eq_id)
    if eq:
        return eq
    raise HTTPException(status_code=404, detail=f"eq not found: {eq_id}")


@router.get(
    "/eqs/{eq_id}/structure",
    response_class=PlainTextResponse,
    dependencies=[
        # Depends(items_pagination_params),
        # Depends(RateLimiter(times=10, seconds=5)),
    ],
)
async def get_eq_structure(
    eq_id: str, format: Optional[str] = "xyz", db: Session = Depends(session)
):
    eq = Database.get_eq(db, eq_id)

    response = ""
    response = get_structure(eq.map.atom_name, eq.xyz, format)

    if response:
        return response

    raise HTTPException(status_code=404, detail=f"Structure is not found: {eq_id}")


@router.get(
    "/maps/{map_id}/edges",
    response_model=ItemsPage[schemas.EdgeAbr],
    dependencies=[
        # Depends(items_pagination_params),
        # Depends(RateLimiter(times=10, seconds=5)),
    ],
)
async def get_edges_in_map(
    map_id: str, sort: Optional[str] = None, db: Session = Depends(session)
):
    """
    Find Eqs in the specified map
    :param db: DB Session
    :return: Maps
    :rtype: JSON or CSV
    :exception: HTTPException(404)
    """
    eqs = Database.get_edges(db, map_id, sort)
    if eqs:
        return sql_paginate(eqs)
    raise HTTPException(status_code=404, detail=f"Edges are not found on map: {map_id}")


@router.get(
    "/edges/{edge_id}",
    response_model=schemas.Edge,
    # dependencies=[Depends(RateLimiter(times=10, seconds=5))],
)
async def get_edge(edge_id: str, db: Session = Depends(session)):
    """
    Edge metadata
    :param edge_id: grrm edge id
    :param db: DB Session
    :return: Edge metadata
    :rtype: JSON or CSV
    :exception: HTTPException(404)
    """
    edge = Database.get_edge(db, edge_id)
    if edge:
        return edge
    raise HTTPException(status_code=404, detail=f"edge not found: {edge_id}")


@router.get(
    "/edges/{edge_id}/structure",
    response_class=PlainTextResponse,
    dependencies=[
        # Depends(items_pagination_params),
        # Depends(RateLimiter(times=10, seconds=5)),
    ],
)
async def get_edge_structure(
    edge_id: str, format: Optional[str] = "xyz", db: Session = Depends(session)
):
    edge = Database.get_edge(db, edge_id)

    response = ""
    response = get_structure(edge.map.atom_name, edge.xyz, format)

    if response:
        return response

    raise HTTPException(status_code=404, detail=f"Structure is not found: {edge_id}")


@router.get(
    "/edges/{edge_id}/pathnodes",
    response_model=ItemsPage[schemas.PathNodeAbr],
    dependencies=[
        # Depends(items_pagination_params),
        # Depends(RateLimiter(times=10, seconds=5)),
    ],
)
async def get_pathnodes(edge_id: str, db: Session = Depends(session)):
    """
    Pathnode list
    :param edge_id: grrm edge id
    :param db: DB Session
    :return: Pathnode list
    :rtype: JSON or CSV
    :exception: HTTPException(404)
    """
    pathnodes = Database.get_pathnodes(db, edge_id)
    if pathnodes:
        return paginate_list(pathnodes)
    raise HTTPException(status_code=404, detail=f"pathnodes not found on: {edge_id}")


@router.get(
    "/pathnodes/{pnode_id}",
    response_model=schemas.PathNode,
    # dependencies=[Depends(RateLimiter(times=10, seconds=5))],
)
async def get_pathnode(pnode_id: str, db: Session = Depends(session)):
    """
    Pathnode metadata
    :param pnode_id: grrm pathnode id
    :param db: DB Session
    :return: Pathnode metadata
    :rtype: JSON or CSV
    :exception: HTTPException(404)
    """
    pathnode = Database.get_pathnode(db, pnode_id)
    if pathnode:
        return pathnode
    raise HTTPException(status_code=404, detail=f"pathnode not found: {pnode_id}")


@router.get(
    "/pathnodes/{pnode_id}/structure",
    response_class=PlainTextResponse,
    dependencies=[
        # Depends(items_pagination_params),
        # Depends(RateLimiter(times=10, seconds=5)),
    ],
)
async def get_pathnode_structure(
    pnode_id: str, format: Optional[str] = "xyz", db: Session = Depends(session)
):
    pathnode = Database.get_pathnode(db, pnode_id)

    response = ""
    response = get_structure(pathnode.map.atom_name, pathnode.xyz, format)

    if response:
        return response

    raise HTTPException(status_code=404, detail=f"Structure is not found: {pnode_id}")


add_pagination(router)