"""FastAPI dependency injection."""

from fastapi import Depends
from app.core.auth import VDCAuthClient, get_auth_client
from app.core.http_client import get_http_client
import httpx


async def get_vdc_auth() -> VDCAuthClient:
    """Dependency for VDC authentication client."""
    return get_auth_client()


async def get_http() -> httpx.AsyncClient:
    """Dependency for HTTP client."""
    return get_http_client()


# Service dependencies

async def get_air_shopping_service():
    """Dependency for AirShoppingService."""
    from app.services.air_shopping import AirShoppingService
    auth = await get_vdc_auth()
    http = await get_http()
    return AirShoppingService(auth_client=auth, http_client=http)


async def get_flight_price_service():
    """Dependency for FlightPriceService."""
    from app.services.flight_price import FlightPriceService
    auth = await get_vdc_auth()
    http = await get_http()
    return FlightPriceService(auth_client=auth, http_client=http)


async def get_ancillary_service():
    """Dependency for AncillaryService."""
    from app.services.ancillary import AncillaryService
    auth = await get_vdc_auth()
    http = await get_http()
    return AncillaryService(auth_client=auth, http_client=http)


async def get_order_create_service():
    """Dependency for OrderCreateService."""
    from app.services.order_create import OrderCreateService
    return OrderCreateService()
