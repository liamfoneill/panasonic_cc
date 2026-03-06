#!/usr/bin/env python3
"""Probe Panasonic Comfort Cloud auth/bootstrap calls with a refresh token."""

from __future__ import annotations

import argparse
import asyncio
import json
import ssl
import sys
from pathlib import Path

import aiohttp
import certifi


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "custom_components" / "panasonic_cc"
INSPECT_ROOT = Path("/tmp/panasonic_cc_inspect")

if INSPECT_ROOT.exists():
    sys.path.insert(0, str(INSPECT_ROOT))

from aio_panasonic_comfort_cloud import ApiClient  # type: ignore  # noqa: E402
from aio_panasonic_comfort_cloud.constants import BASE_PATH_ACC  # type: ignore  # noqa: E402
from aio_panasonic_comfort_cloud.panasonicrequestheader import PanasonicRequestHeader  # type: ignore  # noqa: E402


PANASONIC_OAUTH_SCOPE = "openid offline_access comfortcloud.control a2w.control"
AGREEMENT_TYPES = (1, 2, 3)


async def read_json(response: aiohttp.ClientResponse) -> str:
    text = await response.text()
    try:
        parsed = json.loads(text)
        return json.dumps(parsed, indent=2, sort_keys=True)
    except json.JSONDecodeError:
        return text


async def post_json(
    session: aiohttp.ClientSession,
    url: str,
    *,
    headers: dict[str, str],
    payload: dict,
) -> tuple[int, str, dict[str, str]]:
    response = await session.post(url, headers=headers, json=payload)
    body = await read_json(response)
    return response.status, body, dict(response.headers)


async def get_json(
    session: aiohttp.ClientSession,
    url: str,
    *,
    headers: dict[str, str],
) -> tuple[int, str, dict[str, str]]:
    response = await session.get(url, headers=headers)
    body = await read_json(response)
    return response.status, body, dict(response.headers)


async def request_json(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    payload: dict | None = None,
) -> tuple[int, str, dict[str, str]]:
    response = await session.request(method, url, headers=headers, json=payload)
    body = await read_json(response)
    return response.status, body, dict(response.headers)


async def print_request(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    payload: dict | None = None,
) -> tuple[int, dict | None]:
    status, body, _ = await request_json(
        session,
        method,
        url,
        headers=headers,
        payload=payload,
    )
    print(f"{method} {url}")
    print(f"Status: {status}")
    print(body)
    print()
    try:
        return status, json.loads(body)
    except json.JSONDecodeError:
        return status, None


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe Panasonic Comfort Cloud auth/bootstrap endpoints.",
    )
    parser.add_argument("--username", required=True, help="Panasonic ID")
    parser.add_argument("--password", default="", help="Panasonic password")
    parser.add_argument("--refresh-token", required=True, help="Refresh token")
    args = parser.parse_args()

    timeout = aiohttp.ClientTimeout(total=60)
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        api = ApiClient(args.username, args.password, session)
        await api._settings.is_ready()
        api._settings.set_token(
            refresh_token=args.refresh_token,
            scope=PANASONIC_OAUTH_SCOPE,
        )

        print("== Refresh token ==")
        await api._authentication.refresh_token()
        print("Access token refreshed successfully.")
        print(f"Rotated refresh token: {api._settings.refresh_token}")
        print(f"Client ID before bootstrap: {api._settings.clientId!r}")
        print()

        print("== auth/v2/login ==")
        auth_headers = await PanasonicRequestHeader.get(
            api._settings,
            api._app_version,
            include_client_id=False,
        )
        auth_status, auth_body, auth_response_headers = await post_json(
            session,
            f"{BASE_PATH_ACC}/auth/v2/login",
            headers=auth_headers,
            payload={"language": 0},
        )
        print(f"Status: {auth_status}")
        print(auth_body)
        if auth_status == 200:
            try:
                client_id = json.loads(auth_body)["clientId"]
                api._settings.clientId = client_id
                print(f"Stored clientId: {client_id}")
            except Exception:
                print("Could not extract clientId from auth/v2/login response.")
        print()

        print("== initial device/group ==")
        group_headers = await PanasonicRequestHeader.get(
            api._settings,
            api._app_version,
        )
        group_status, group_payload = await print_request(
            session,
            "GET",
            f"{BASE_PATH_ACC}/device/group",
            headers=group_headers,
        )

        try:
            login_payload = json.loads(auth_body)
        except json.JSONDecodeError:
            login_payload = {}

        language = int(login_payload.get("language", 0) or 0)

        print("== agreement flow ==")
        for agreement_type in AGREEMENT_TYPES:
            status_status, status_payload = await print_request(
                session,
                "GET",
                f"{BASE_PATH_ACC}/auth/agreement/status/{agreement_type}",
                headers=group_headers,
            )
            await print_request(
                session,
                "GET",
                f"{BASE_PATH_ACC}/auth/agreement/documents/{language}/{agreement_type}",
                headers=group_headers,
            )
            if status_status == 200 and isinstance(status_payload, dict):
                if int(status_payload.get("agreementStatus", 0) or 0) != 1:
                    await print_request(
                        session,
                        "PUT",
                        f"{BASE_PATH_ACC}/auth/agreement/status/",
                        headers=group_headers,
                        payload={"agreementStatus": 1, "type": agreement_type},
                    )

        print("== final device/group ==")
        final_group_status, final_group_payload = await print_request(
            session,
            "GET",
            f"{BASE_PATH_ACC}/device/group",
            headers=group_headers,
        )

        if auth_status != 200 or final_group_status != 200:
            print("== Summary ==")
            print("Panasonic is still rejecting part of the bootstrap flow.")
            return 1

        print("== Summary ==")
        print("auth/v2/login and device/group both succeeded.")
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
