from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.aws import (
    CatalogMeta,
    QuoteRequest,
    QuoteResponse,
    RegionOut,
    ServiceOut,
)
from app.services import catalog

router = APIRouter(prefix="/aws", tags=["aws"])


@router.get("/catalog", response_model=CatalogMeta)
def get_catalog(db: Session = Depends(get_db)) -> CatalogMeta:
    return catalog.catalog_meta(db)


@router.get("/regions", response_model=list[RegionOut])
def get_regions(db: Session = Depends(get_db)) -> list[RegionOut]:
    return catalog.list_regions(db)


@router.get("/services", response_model=list[ServiceOut])
def get_services(db: Session = Depends(get_db)) -> list[ServiceOut]:
    return catalog.list_services(db)


@router.post("/quote", response_model=QuoteResponse)
def post_quote(
    payload: QuoteRequest, db: Session = Depends(get_db)
) -> QuoteResponse:
    if payload.plan_code:
        quote = catalog.quote_plan(db, payload.plan_code, payload.region_code)
        if quote is None:
            raise HTTPException(status_code=404, detail="El combo no existe")
        return quote

    if payload.services:
        components = [
            {"service_code": spec.service_code, "params": spec.params}
            for spec in payload.services
        ]
        return catalog.quote_components(db, components, payload.region_code)

    raise HTTPException(
        status_code=400, detail="Indica un plan_code o una lista de services"
    )
