from typing import Optional, Any, Tuple

import httpx

SucCode = 200
transport = httpx.AsyncHTTPTransport(
    retries=3,
    limits=httpx.Limits(max_connections=20, max_keepalive_connections=8)
)
client = httpx.AsyncClient(timeout=20, transport=transport)


class ServerResp:
    status_code: int
    status_msg: str
    data: Any

async def get_to_server(
        url: str,
        params: dict,
        headers: Optional[dict[str, str]]=None,
) -> Tuple[Any, Optional[Exception]]:
    try:
        resp = client.get(url, params=params, headers=headers)
        if resp.status_code != SucCode:
            return None, Exception(f"failed with status_code {resp.status_code}")
        resp = ServerResp(**resp.json())
    except Exception as e:
        return None, e
    if resp.status_code != SucCode:
        return None, Exception(resp.status_msg)
    return resp.data, None

async def post_to_server(
        url: str,
        data: dict,
        headers: Optional[dict[str, str]]=None,
) -> Tuple[Any, Optional[Exception]]:
    try:
        resp = await client.post(url, json=data, headers=headers)
        if resp.status_code != SucCode:
            return None, Exception(f"failed with status_code {resp.status_code}")
        resp = ServerResp(**resp.json())
    except Exception as e:
        return None, e
    if resp.status_code != SucCode:
        return None, Exception(resp.status_msg)
    return resp.data, None
