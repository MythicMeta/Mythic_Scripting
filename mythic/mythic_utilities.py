import asyncio
import logging
import ssl
from os import path
from time import time
from typing import AsyncGenerator, TypeVar

import aiohttp
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.websockets import WebsocketsTransport
from graphql import print_schema

from . import mythic_classes

T = TypeVar("T")


async def timeout_generator(
        mythic: mythic_classes.Mythic, it: AsyncGenerator[T, None], timeout: float = None
) -> AsyncGenerator[T, None]:
    start = time()
    should_timeout = timeout is not None and timeout > 0
    task = None
    while True:
        # we don't want to wait for timeout each time, that's an overall timeout
        if should_timeout:
            # the new timeout should be the total amount of time remaining
            new_timeout = timeout - (time() - start)
            if new_timeout <= 0:
                # we already hit our timeout and should return
                break
        else:
            new_timeout = None
        try:
            task = asyncio.create_task(it.__anext__())
            yield await asyncio.wait_for(task, new_timeout)
        except asyncio.TimeoutError:
            if task is not None:
                task.cancel()
            raise asyncio.TimeoutError
        except StopAsyncIteration:
            if task is not None:
                task.cancel()
            raise asyncio.TimeoutError
        except Exception as e:
            if task is not None:
                task.cancel()
            raise e


def get_headers(mythic: mythic_classes.Mythic) -> dict:
    headers = {}
    if mythic.apitoken is not None:
        headers["apitoken"] = mythic.apitoken
    elif mythic.access_token is not None:
        headers["Authorization"] = f"Bearer {mythic.access_token}"
    return headers


async def get_http_transport(mythic: mythic_classes.Mythic) -> AIOHTTPTransport:
    transport = AIOHTTPTransport(
        url=f"{mythic.http}{mythic.server_ip}:{mythic.server_port}/graphql/",
        headers=get_headers(mythic),
    )
    return transport


async def get_ws_transport(mythic: mythic_classes.Mythic) -> WebsocketsTransport:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    websocket_transport = WebsocketsTransport(
        url=f"{mythic.ws}{mythic.server_ip}:{mythic.server_port}/graphql/",
        headers=get_headers(mythic),
        ssl=ssl_context if mythic.ssl else False,
    )
    return websocket_transport


async def http_post(mythic: mythic_classes.Mythic, data: dict, url: str) -> dict:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json=data, headers=get_headers(mythic), ssl=False
            ) as resp:
                return await resp.json()
    except Exception as e:
        raise e


async def http_post_form(
    mythic: mythic_classes.Mythic, data: aiohttp.FormData, url: str
) -> dict:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, data=data, headers=get_headers(mythic), ssl=False
            ) as resp:
                return await resp.json()
    except Exception as e:
        raise e


async def http_get_dictionary(mythic: mythic_classes.Mythic, url: str) -> dict:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=get_headers(mythic), ssl=False) as resp:
                return await resp.json()
    except Exception as e:
        raise e


async def http_get(mythic: mythic_classes.Mythic, url: str) -> bytes:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=get_headers(mythic), ssl=False) as resp:
                return await resp.content.read()
    except Exception as e:
        raise e


async def http_get_chunked(
    mythic: mythic_classes.Mythic, url: str, chunk_size: int = 512000
) -> AsyncGenerator:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=get_headers(mythic), ssl=False) as resp:
                async for data in resp.content.iter_chunked(abs(chunk_size)):
                    yield data
    except Exception as e:
        raise e


async def graphql_post(
    mythic: mythic_classes.Mythic,
    gql_query: gql = None,
    query: str = None,
    variables: dict = None,
):
    try:
        query_data = gql(query) if query is not None else gql_query
        if query_data is None:
            raise Exception("No data or gql_data passed into graphql_post function")
        async with Client(
            transport=await get_http_transport(mythic=mythic),
            fetch_schema_from_transport=False,
            execute_timeout=None if mythic.global_timeout < 0 else mythic.global_timeout,
            schema=mythic.schema,
        ) as session:
            result = await session.execute(query_data, variable_values=variables)
            return result
    except Exception as e:
        raise e


async def graphql_subscription(
    mythic: mythic_classes.Mythic,
    gql_query: gql = None,
    query: str = None,
    variables: dict = None,
    timeout: int = None,
) -> AsyncGenerator:
    try:
        query_data = gql(query) if query is not None else gql_query
        local_timeout = timeout
        if local_timeout is None:
            local_timeout = mythic.global_timeout

        if query_data is None:
            raise Exception(
                "No data or gql_data passed into graphql_subscription function"
            )
        async with Client(
            transport=await get_ws_transport(mythic=mythic),
            fetch_schema_from_transport=False,
            execute_timeout=None,
        ) as session:
            async for result in timeout_generator(
                mythic=mythic,
                it=session.subscribe(query_data, variable_values=variables),
                timeout=local_timeout,
            ):
                yield result
    except Exception as e:
        raise e


async def fetch_graphql_schema(mythic: mythic_classes.Mythic):
    try:
        async with Client(
            transport=await get_http_transport(mythic=mythic),
            fetch_schema_from_transport=True,
            schema=mythic.schema,
        ) as session:
            schema = print_schema(session.client.schema)
            return schema
    except Exception as e:
        raise e


async def load_mythic_schema(mythic: mythic_classes.Mythic) -> bool:
    if path.exists("mythic_schema.graphql"):
        try:
            with open("mythic_schema.graphql", "r") as f:
                schema = f.read()
                mythic.schema = schema
            return True
        except Exception as e:
            mythic.logger.error(
                f"[-] Found mythic_schema.graphql locally, but failed to read it:\n{str(e)}"
            )
            mythic.logger.error(
                "[-] Unable to verify GraphQL queries syntactically before executing"
            )
            return False
    else:
        try:
            schema = await fetch_graphql_schema(mythic)
        except Exception as e:
            mythic.logger.error(f"[-] Failed to contact Mythic and fetch schema:\n{str(e)}")
            return False
        try:
            mythic.schema = schema
            with open("mythic_schema.graphql", "w") as f:
                f.write(schema)
            return True
        except Exception as e:
            mythic.logger.error(f"[-] Failed to save Mythic schema to disk:\n{str(e)}")
            mythic.logger.error(
                "[-] Unable to verify GraphQL queries syntactically before executing"
            )
            return False
