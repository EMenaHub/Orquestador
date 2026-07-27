from cachetools import TTLCache
import httpx

from app.config import settings

_regions_cache: TTLCache = TTLCache(maxsize=1, ttl=settings.cache_ttl_regions)
_devices_cache: TTLCache = TTLCache(maxsize=128, ttl=settings.cache_ttl_devices)

GRAPHQL_QUERY_REGIONS = """
query {
  locations(location_type: "region") {
    id
    name
  }
}
"""

GRAPHQL_QUERY_DEVICES = """
query($region: [String!]) {
  devices(role: "region", parent: $region) {
    id
    name
  }
}
"""


async def _graphql(query: str, variables: dict | None = None) -> list[dict]:
    async with httpx.AsyncClient(
        base_url=settings.nautobot_url,
        headers={"Authorization": f"Token {settings.nautobot_token}"},
        timeout=30,
    ) as client:
        resp = await client.post(
            "/api/graphql/",
            json={"query": query, "variables": variables or {}},
        )
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            raise RuntimeError(f"GraphQL error: {data['errors']}")
        return data["data"]


async def get_regions() -> list[dict]:
    if _regions_cache:
        return list(_regions_cache.values())

    data = await _graphql(GRAPHQL_QUERY_REGIONS)
    regions = data.get("locations", [])
    for r in regions:
        _regions_cache[r["id"]] = r
    return regions


async def get_devices(region_id: str) -> list[dict]:
    cache_key = f"devices:{region_id}"
    if cache_key in _devices_cache:
        return _devices_cache[cache_key]

    data = await _graphql(GRAPHQL_QUERY_DEVICES, {"region": region_id})
    devices = data.get("devices", [])
    _devices_cache[cache_key] = devices
    return devices
