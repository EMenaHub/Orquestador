from cachetools import TTLCache
import httpx

from app.config import settings

TENANTS_MAP: dict[str, dict] = {
    "Zapping Chile": {"id": "fe1e9621-9706-4769-a06f-a12c7a5cd36b", "name": "Zapping Chile"},
    "Zapping Brasil": {"id": "68891f49-0f30-427c-9dc2-bfefea8c4701", "name": "Zapping Brasil"},
    "Zapping Ecuador": {"id": "638a9dc7-ef48-49e6-be26-f06fc8b415eb", "name": "Zapping Ecuador"},
    "Zapping Peru": {"id": "b0d2a831-2133-44b8-bb72-7ad8c662a330", "name": "Zapping Peru"},
}

MANUAL_DEVICES: list[dict] = [
    {"name": "BR-CB-VPN-1", "tenant": "Zapping Brasil", "role": "VPN"},
    {"name": "BR-DC2-VPN-2", "tenant": "Zapping Brasil", "role": "VPN"},
    {"name": "BR-ION-EDGE-1", "tenant": "Zapping Brasil", "role": "SWITCH"},
    {"name": "CL-DC1-AGG-3", "tenant": "Zapping Chile", "role": "AGG"},
    {"name": "CL-DC2-AGG-2", "tenant": "Zapping Chile", "role": "AGG"},
    {"name": "CL-OFF-RT-1", "tenant": "Zapping Chile", "role": "ROUTER"},
    {"name": "EC-EV-EDGE", "tenant": "Zapping Ecuador", "role": "SWITCH"},
]

_tenants_cache: TTLCache = TTLCache(maxsize=1, ttl=settings.cache_ttl_regions)
_devices_cache: TTLCache = TTLCache(maxsize=1, ttl=settings.cache_ttl_devices)

GRAPHQL_QUERY_TENANTS = """
query {
  tenants {
    id
    name
  }
}
"""

GRAPHQL_QUERY_DEVICES = """
query {
  devices(limit: 500) {
    id
    name
    role { name }
    tenant { id name }
  }
}
"""


async def _graphql(query: str, variables: dict | None = None) -> dict:
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


async def get_tenants() -> list[dict]:
    if _tenants_cache:
        return list(_tenants_cache.values())

    data = await _graphql(GRAPHQL_QUERY_TENANTS)
    tenants = data.get("tenants", [])
    for t in tenants:
        _tenants_cache[t["id"]] = t
    return tenants


async def get_devices_by_tenant() -> list[dict]:
    if _devices_cache:
        return list(_devices_cache.values())

    data = await _graphql(GRAPHQL_QUERY_DEVICES)
    devices = data.get("devices", [])
    allowed_roles = {r.strip().upper() for r in settings.nautobot_device_roles.split(",")}

    grouped: dict[str, dict] = {}
    for d in devices:
        role_name = (d.get("role") or {}).get("name", "").upper()
        if role_name not in allowed_roles:
            continue
        tenant = d.get("tenant") or {}
        tenant_id = tenant.get("id", "unknown")
        if tenant_id not in grouped:
            tenant_name = tenant.get("name", "Unknown")
            grouped[tenant_id] = {"id": tenant_id, "name": tenant_name, "devices": []}
        grouped[tenant_id]["devices"].append({"id": d["id"], "name": d["name"]})

    existing_names = {d["name"] for tenant in grouped.values() for d in tenant["devices"]}

    for md in MANUAL_DEVICES:
        if md["name"].upper() in existing_names:
            continue
        tenant_info = TENANTS_MAP.get(md["tenant"])
        if not tenant_info:
            continue
        tenant_id = tenant_info["id"]
        if tenant_id not in grouped:
            grouped[tenant_id] = {"id": tenant_id, "name": tenant_info["name"], "devices": []}
        grouped[tenant_id]["devices"].append({"id": f"manual-{md['name']}", "name": md["name"]})
        existing_names.add(md["name"].upper())

    result = list(grouped.values())
    _devices_cache[1] = result
    return result
