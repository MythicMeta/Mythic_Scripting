import base64
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, List, Union

import aiohttp

from . import graphql_queries, mythic_classes, mythic_utilities

"""
Logging error levels for logging_level with Mythic based on logging package
CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0
"""


async def login(
    server_ip: str,
    server_port: int = 7443,
    username: str = None,
    password: str = None,
    apitoken: str = None,
    ssl: bool = True,
    timeout: int = -1,
    logging_level: int = logging.WARNING,
) -> mythic_classes.Mythic:
    """
    Create a new Mythic instance based on the connection information and attempt to validate the credentials.
    If a username and password is provided, this will log into Mythic and fetch/generate an API token to use for subsequent functions.
    If an api token is provided, this will validate that the api token is valid.
    """
    mythic = mythic_classes.Mythic(
        username=username,
        password=password,
        server_ip=server_ip,
        server_port=server_port,
        apitoken=apitoken,
        ssl=ssl,
        global_timeout=timeout,
        schema=None,
    )
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging_level)
    if apitoken is None:
        url = f"{mythic.http}{mythic.server_ip}:{mythic.server_port}/auth"
        data = {
            "username": mythic.username,
            "password": mythic.password,
            "scripting_version": mythic.scripting_version,
        }
        logging.debug(
            f"[*] Logging into Mythic as scripting_version {mythic.scripting_version}"
        )
        try:
            response = await mythic_utilities.http_post(mythic=mythic, url=url, data=data)
            mythic.access_token = (
                response["access_token"] if "access_token" in response else None
            )
            mythic.refresh_token = (
                response["refresh_token"] if "refresh_token" in response else None
            )
            mythic.current_operation_id = (
                response["user"]["current_operation_id"] if "user" in response else 0
            )
            current_tokens = await mythic_utilities.graphql_post(
                mythic=mythic, gql_query=graphql_queries.get_apitokens
            )
            if "apitokens" in current_tokens and len(current_tokens["apitokens"]) > 0:
                mythic.apitoken = current_tokens["apitokens"][0]["token_value"]
            else:
                # we need to generate an api token and use that so that future calls don't get timed out from an expired JWT
                new_token = await mythic_utilities.graphql_post(
                    mythic=mythic, gql_query=graphql_queries.create_apitoken
                )
                if (
                    new_token["createAPIToken"]["status"] == "success"
                    and "token_value" in new_token["createAPIToken"]
                ):
                    mythic.apitoken = new_token["createAPIToken"]["token_value"]
                else:
                    raise Exception(
                        f"Failed to get or generate an API token to use from Mythic\n{new_token['createAPIToken']['error']}"
                    )
            await mythic_utilities.load_mythic_schema(mythic)
            return mythic
        except Exception as e:
            logging.exception(f"[-] Failed to authenticate to Mythic: \n{str(e)}")
            raise e
    else:
        try:
            await get_me(mythic=mythic)
            await mythic_utilities.load_mythic_schema(mythic=mythic)
            return mythic
        except Exception as e:
            logging.exception(f"[-] Failed to authenticate to Mythic: \n{str(e)}")
            raise e


async def get_me(mythic: mythic_classes.Mythic) -> dict:
    url = f"{mythic.http}{mythic.server_ip}:{mythic.server_port}/me"
    try:
        response = await mythic_utilities.http_get_dictionary(mythic=mythic, url=url)
        mythic.current_operation_id = response["me"]["current_operation_id"]
        mythic.operator_id = response["me"]["id"]
        mythic.operator = response["me"]["username"]
        return response
    except Exception as e:
        logging.exception(
            f"[-] Failed to use APIToken to fetch user information\n: {str(e)}"
        )
        raise e


async def execute_custom_query(
    mythic: mythic_classes.Mythic, query: str, variables: dict = None
) -> dict:
    try:
        return await mythic_utilities.graphql_post(
            mythic=mythic, query=query, variables=variables
        )
    except Exception as e:
        logging.info(f"Hit an exception within execute_custom_query: {e}")
        raise e


async def subscribe_custom_query(
    mythic: mythic_classes.Mythic, query: str, variables: dict = None, timeout: int = None
) -> AsyncGenerator:
    """
    Execute a custom graphql subscription.
    This returns an async iterator, which can be used as:
        async for item in execute_custom_subscription(...data):
            print(item) <--- item will always be a dictionary based on the data you're getting back
    """
    try:
        async for result in mythic_utilities.graphql_subscription(
            mythic=mythic, query=query, variables=variables, timeout=timeout
        ):
            yield result
    except Exception as e:
        logging.info(f"Hit an exception within execute_custom_subscription: {e}")
        raise e


# ########### Callback Functions #############


async def get_all_callbacks(
    mythic: mythic_classes.Mythic, custom_return_attributes: str = None
) -> List[dict]:
    """
    Executes a graphql query to get information about all callbacks (including ones that are no longer active).
    This returns an async iterator, which can be used as:
        async for item in get_all_callbacks(...data):
            print(item) <--- item will always be a dictionary based on the data you're getting back
    The default set of attributes returned in the dictionary can be found at graphql_queries.callback_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` field, everything else is optional.
    """
    query = f"""
    query CurrentCallbacks{{
        callback(order_by: {{id: asc}}){{
            {custom_return_attributes if custom_return_attributes is not None else '...callback_fragment'}
        }}
    }}
    {graphql_queries.callback_fragment if custom_return_attributes is None else ''}
    """
    initial_tasks = await mythic_utilities.graphql_post(
        mythic=mythic, query=query, variables=None
    )
    return initial_tasks["callback"]


async def get_all_active_callbacks(
    mythic: mythic_classes.Mythic,
    custom_return_attributes: str = None,
) -> List[dict]:
    """
    Executes a graphql query to get information about all of the currently active callbacks.
    This returns an async iterator, which can be used as:
        async for item in get_all_active_callbacks(...data):
            print(item) <--- item will always be a dictionary based on the data you're getting back
    The default set of attributes returned in the dictionary can be found at graphql_queries.callback_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` field, everything else is optional.
    """
    query = f"""
    query CurrentCallbacks{{
        callback(where: {{active: {{_eq: true}}}}, order_by: {{id: asc}}){{
            {custom_return_attributes if custom_return_attributes is not None else '...callback_fragment'}
        }}
    }}
    {graphql_queries.callback_fragment if custom_return_attributes is None else ''}
    """
    initial_tasks = await mythic_utilities.graphql_post(
        mythic=mythic, query=query, variables=None
    )
    return initial_tasks["callback"]


async def subscribe_new_callbacks(
    mythic: mythic_classes.Mythic,
    fetch_limit: int = 50,
    timeout: int = None,
    custom_return_attributes: str = None,
) -> AsyncGenerator:
    """
    Execute a graphql subscription for callbacks that have an initial checkin time greater than when this function is called.
    This returns an async iterator, which can be used as:
        async for item in subscribe_new_callbacks(...data):
            print(item) <--- item will always be a dictionary based on the data you're getting back
    The default set of attributes returned in the dictionary can be found at graphql_queries.callback_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` field, everything else is optional.
    """
    seen_callbacks = set()
    try:
        subscription = f"""
        subscription NewCallbacks($now: timestamp!, $fetch_limit: Int!){{
            callback(where: {{active: {{_eq: true}}, init_callback: {{_gt: $now}}}}, limit: $fetch_limit, order_by: {{id: desc}}){{
                {custom_return_attributes if custom_return_attributes is not None else '...callback_fragment'}
            }}
        }}
        {graphql_queries.callback_fragment if custom_return_attributes is None else ''}
        """
        variables = {"now": str(datetime.utcnow()), "fetch_limit": fetch_limit}
        async for result in mythic_utilities.graphql_subscription(
            mythic=mythic, query=subscription, variables=variables, timeout=timeout
        ):
            if len(result["callback"]) > 0:
                for c in reversed(result["callback"]):
                    if c["id"] in seen_callbacks:
                        continue
                    seen_callbacks.add(c["id"])
                    yield c
    except StopAsyncIteration:
        logging.info("stopasynciteration exception in subscribe_new_callbacks")
        pass
    except Exception as e:
        logging.info("some other exception in subscribe_new_callbacks")
        raise e


async def subscribe_all_active_callbacks(
    mythic: mythic_classes.Mythic,
    timeout: int = None,
    custom_return_attributes: str = None,
) -> AsyncGenerator:
    """
    Executes a graphql query to get information about all currently active callbacks so far, then opens up a subscription for new callbacks.
    This returns an async iterator, which can be used as:
        async for item in subscribe_all_active_callbacks(...data):
            print(item) <--- item will always be a dictionary based on the data you're getting back
    The default set of attributes returned in the dictionary can be found at graphql_queries.callback_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` field, everything else is optional.
    """
    for t in await get_all_active_callbacks(
        mythic=mythic, custom_return_attributes=custom_return_attributes
    ):
        yield t
    async for t in subscribe_new_callbacks(
        mythic=mythic, timeout=timeout, custom_return_attributes=custom_return_attributes
    ):
        yield t


async def update_callback(
    mythic: mythic_classes.Mythic,
    callback_id: int,
    active: bool = None,
    sleep_info: str = None,
    locked: bool = None,
    description: str = None,
) -> bool:
    current_callback_info_query = """
    query callbackInfo($callback_id: Int!){
        callback_by_pk(id: $callback_id){
            active
            sleep_info
            locked
            description
        }
    }
    """
    current_callback_info = await mythic_utilities.graphql_post(
        mythic=mythic,
        query=current_callback_info_query,
        variables={"callback_id": callback_id},
    )
    if current_callback_info["callback_by_pk"] is None:
        raise Exception("Failed to find callback")
    if active is not None:
        if active == current_callback_info["callback_by_pk"]["active"]:
            pass
        else:
            update_status = await mythic_utilities.graphql_post(
                mythic=mythic,
                gql_query=graphql_queries.update_callback_active_status,
                variables={"callback_id": callback_id, "active": active},
            )
            if update_status["updateCallback"]["status"] != "success":
                raise Exception(update_status["updateCallback"]["error"])
    if locked is not None:
        update_status = await mythic_utilities.graphql_post(
            mythic=mythic,
            gql_query=graphql_queries.update_callback_lock_status,
            variables={"callback_id": callback_id, "locked": locked},
        )
        if update_status["updateCallback"]["status"] != "success":
            raise Exception(update_status["updateCallback"]["error"])
    if description is not None:
        update_status = await mythic_utilities.graphql_post(
            mythic=mythic,
            gql_query=graphql_queries.update_callback_description,
            variables={"callback_id": callback_id, "description": description},
        )
        if update_status["updateCallback"]["status"] != "success":
            raise Exception(update_status["updateCallback"]["error"])
    if sleep_info is not None:
        update_status = await mythic_utilities.graphql_post(
            mythic=mythic,
            gql_query=graphql_queries.update_callback_sleep_info,
            variables={"callback_id": callback_id, "sleep_info": sleep_info},
        )
    return True


# ########## Task Functions #################


async def get_all_tasks(
    mythic: mythic_classes.Mythic,
    custom_return_attributes: str = None,
    callback_id: int = None,
) -> List[dict]:
    """
    Executes a graphql query to get all tasks submitted so far (potentially limited to a single callback).
    This returns an async iterator, which can be used as:
        async for item in get_all_tasks(...data):
            print(item) <--- item will always be a dictionary based on the data you're getting back
    The default set of attributes returned in the dictionary can be found at graphql_queries.task_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` field, everything else is optional.
    """
    if callback_id is not None:
        query = f"""
        query CurrentTasks($callback_id: Int){{
            task(where: {{callback: {{id: {{_eq: $callback_id}}}}}}, order_by: {{id: desc}}){{
                {custom_return_attributes if custom_return_attributes is not None else '...task_fragment'}
            }}
        }}
        {graphql_queries.task_fragment if custom_return_attributes is None else ''}
        """
        variables = {"callback_id": callback_id}
    else:
        query = f"""
        query CurrentTasks{{
            task(order_by: {{id: desc}}){{
                {custom_return_attributes if custom_return_attributes is not None else '...task_fragment'}
            }}
        }}
        {graphql_queries.task_fragment if custom_return_attributes is None else ''}
        """
        variables = None
    initial_tasks = await mythic_utilities.graphql_post(
        mythic=mythic, query=query, variables=variables
    )
    return initial_tasks["task"]


async def subscribe_new_tasks(
    mythic: mythic_classes.Mythic,
    fetch_limit: int = 50,
    timeout: int = None,
    callback_id: int = None,
    custom_return_attributes: str = None,
) -> AsyncGenerator:
    """
    Execute a graphql subscription for tasks that have a timestamp greater than when this function is called.
    This will only fire once per task, this will not reflect updates to tasks as they go through the tasking process, get processed by agents, and become completed.
    For that, use the subscribe_new_tasks_and_updates function.
    This returns an async iterator, which can be used as:
        async for item in subscribe_new_tasks(...data):
            print(item) <--- item will always be a dictionary based on the data you're getting back
    The default set of attributes returned in the dictionary can be found at graphql_queries.task_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` field, everything else is optional.
    """
    seen_tasks = set()
    try:
        if callback_id is not None:
            subscription = f"""
            subscription NewTasks($now: timestamp!, $fetch_limit: Int!, $callback_id: Int){{
                task(where: {{timestamp: {{_gt: $now}}, callback: {{id: {{_eq: $callback_id}}}}}}, limit: $fetch_limit, order_by: {{id: desc}}){{
                    {custom_return_attributes if custom_return_attributes is not None else '...task_fragment'}
                }}
            }}
            {graphql_queries.task_fragment if custom_return_attributes is None else ''}
            """
            variables = {
                "now": str(datetime.utcnow()),
                "fetch_limit": fetch_limit,
                "callback_id": callback_id,
            }
        else:
            subscription = f"""
            subscription NewTasks($now: timestamp!, $fetch_limit: Int!){{
                task(where: {{timestamp: {{_gt: $now}}}}, limit: $fetch_limit, order_by: {{id: desc}}){{
                    {custom_return_attributes if custom_return_attributes is not None else '...task_fragment'}
                }}
            }}
            {graphql_queries.task_fragment if custom_return_attributes is None else ''}
            """
            variables = {
                "now": str(datetime.utcnow()),
                "fetch_limit": fetch_limit,
            }
        async for result in mythic_utilities.graphql_subscription(
            mythic=mythic, query=subscription, variables=variables, timeout=timeout
        ):
            if len(result["task"]) > 0:
                for t in reversed(result["task"]):
                    if t["id"] in seen_tasks:
                        continue
                    seen_tasks.add(t["id"])
                    yield t
    except Exception as e:
        raise e


async def subscribe_new_tasks_and_updates(
    mythic: mythic_classes.Mythic,
    fetch_limit: int = 50,
    timeout: int = None,
    callback_id: int = None,
    custom_return_attributes: str = None,
) -> AsyncGenerator:
    """
    Execute a graphql subscription for tasks that have a timestamp greater than when this function is called.
    This will include when the timestamp on a task updates (every time it gets a response, the status updates, marked as completed, etc).
    If you only want to be notified once about a task, use `subscribe_new_tasks` instead.
    This returns an async iterator, which can be used as:
        async for item in subscribe_new_tasks_and_updates(...data):
            print(item) <--- item will always be a dictionary based on the data you're getting back
    The default set of attributes returned in the dictionary can be found at graphql_queries.task_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` and 'timestamp' field, everything else is optional.
    """
    seen_tasks = set()
    try:
        if callback_id is not None:
            subscription = f"""
            subscription NewTasks($now: timestamp!, $fetch_limit: Int!, $callback_id: Int){{
                task(where: {{timestamp: {{_gt: $now}}, callback: {{id: {{_eq: $callback_id}}}}}}, limit: $fetch_limit, order_by: {{timestamp: desc}}){{
                    {custom_return_attributes if custom_return_attributes is not None else '...task_fragment'}
                }}
            }}
            {graphql_queries.task_fragment if custom_return_attributes is None else ''}
            """
            variables = {
                "now": str(datetime.utcnow()),
                "fetch_limit": fetch_limit,
                "callback_id": callback_id,
            }
        else:
            subscription = f"""
            subscription NewTasks($now: timestamp!, $fetch_limit: Int!){{
                task(where: {{timestamp: {{_gt: $now}}}}, limit: $fetch_limit, order_by: {{timestamp: desc}}){{
                    {custom_return_attributes if custom_return_attributes is not None else '...task_fragment'}
                }}
            }}
            {graphql_queries.task_fragment if custom_return_attributes is None else ''}
            """
            variables = {
                "now": str(datetime.utcnow()),
                "fetch_limit": fetch_limit,
            }
        async for result in mythic_utilities.graphql_subscription(
            mythic=mythic, query=subscription, variables=variables, timeout=timeout
        ):
            # match on timestamps rather than ID values so that we can get new updates for tasks that have already been issued
            # but also not repeatedly send the same task data back to the caller
            if len(result["task"]) > 0:
                for t in reversed(result["task"]):
                    if t["timestamp"] in seen_tasks:
                        continue
                    seen_tasks.add(t["timestamp"])
                    yield t
    except Exception as e:
        raise e


async def subscribe_all_tasks(
    mythic: mythic_classes.Mythic,
    timeout: int = None,
    callback_id: int = None,
    custom_return_attributes: str = None,
) -> AsyncGenerator:
    """
    Executes a graphql query to get information about every task submitted so far, then opens up a subscription for new tasks.
    This returns an async iterator, which can be used as:
        async for item in subscribe_all_tasks(...data):
            print(item) <--- item will always be a dictionary based on the data you're getting back
    The default set of attributes returned in the dictionary can be found at graphql_queries.task_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` and `timestamp` fields, everything else is optional.
    """
    for t in await get_all_tasks(
        mythic=mythic,
        custom_return_attributes=custom_return_attributes,
        callback_id=callback_id,
    ):
        yield t
    async for t in subscribe_new_tasks(
        mythic=mythic,
        timeout=timeout,
        custom_return_attributes=custom_return_attributes,
        callback_id=callback_id,
    ):
        yield t


async def subscribe_all_tasks_and_updates(
    mythic: mythic_classes.Mythic,
    timeout: int = None,
    callback_id: int = None,
    custom_return_attributes: str = None,
) -> AsyncGenerator:
    """
    Executes a graphql query to get information about every task submitted so far, then opens up a subscription for new tasks and updates to all tasks.
    This returns an async iterator, which can be used as:
        async for item in subscribe_all_tasks_and_updates(...data):
            print(item) <--- item will always be a dictionary based on the data you're getting back
    The default set of attributes returned in the dictionary can be found at graphql_queries.task_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` and `timestamp` fields, everything else is optional.
    """
    for t in await get_all_tasks(
        mythic=mythic,
        custom_return_attributes=custom_return_attributes,
        callback_id=callback_id,
    ):
        yield t
    async for t in subscribe_new_tasks_and_updates(
        mythic=mythic,
        timeout=timeout,
        custom_return_attributes=custom_return_attributes,
        callback_id=callback_id,
    ):
        yield t


async def add_mitre_attack_to_task(
    mythic: mythic_classes.Mythic, task_id: int, mitre_attack_numbers: List[str]
) -> bool:
    """
    Adds the supplied MITRE ATT&CK techniques to the specified task.
    :return: success or failure in adding the techniques
    """
    try:
        attack_items_query = """
        query attackInformation($t_nums: [String!]!) {
            attack(where: {t_num: {_in: $t_nums}}){
                id
            }
        }
        """
        query = """
        mutation MyMutation($task_id: Int!,$ attack_id: Int!) {
            insert_attacktask_one(object: {task_id: $task_id, attack_id: $attack_id}) {
                id
            }
        }
        """
        attack_items = await mythic_utilities.graphql_post(
            mythic=mythic,
            query=attack_items_query,
            variables={"t_nums": mitre_attack_numbers},
        )
        for t in attack_items["attack"]:
            try:
                await mythic_utilities.graphql_post(
                    mythic=mythic,
                    query=query,
                    variables={"task_id": task_id, "attack_id": t["id"]},
                )
            except Exception as e:
                logging.warning(str(e))
                return False
        return True

    except Exception as e:
        raise e


async def issue_task(
    mythic: mythic_classes.Mythic,
    command_name: str,
    parameters: Union[str, dict],
    callback_id: int,
    token_id: int = None,
    return_on_status: mythic_classes.MythicStatus = mythic_classes.MythicStatus.Preprocessing,
    custom_return_attributes: str = None,
    timeout: int = None,
) -> dict:
    """
    Create a new task within Mythic for a specific callback.
    `return_on_status` indicates if this command should return immediately, mythic_classes.MythicStatus.Preprocessing, or wait for a certain status before returning.
        This can be helpful if you want ot make sure a task is completed before continuing
    If you have files that you need to upload and leverage as part of your tasking, use the `register_file` function to get back a file_id.
    If you return immediately from this task, you'll get a dictionary with a status, error, and id field for your new task.
    If you return on another status, you can use your own custom attributes or use the defaults outlined in graphql_queries.task_fragment.
    """
    parameter_string = parameters
    if isinstance(parameters, dict):
        parameter_string = json.dumps(parameters)
    submission_status = await mythic_utilities.graphql_post(
        mythic=mythic,
        gql_query=graphql_queries.create_task,
        variables={
            "callback_id": callback_id,
            "command": command_name,
            "params": parameter_string,
            "token_id": token_id,
            "tasking_location": "command_line"
            if isinstance(parameters, str)
            else "scripting",
        },
    )
    if submission_status["createTask"]["status"] == "success":
        if return_on_status != mythic_classes.MythicStatus.Preprocessing:
            return await waitfor_task_status(
                mythic=mythic,
                task_id=submission_status["createTask"]["id"],
                return_on_status=return_on_status,
                custom_return_attributes=custom_return_attributes,
                timeout=timeout,
            )
        return submission_status["createTask"]
    else:
        raise Exception(
            f"Failed to create task: {submission_status['createTask']['error']}"
        )


async def waitfor_task_status(
    mythic: mythic_classes.Mythic,
    task_id: int,
    return_on_status: mythic_classes.MythicStatus = mythic_classes.MythicStatus.Submitted,
    custom_return_attributes: str = None,
    timeout: int = None,
) -> dict:
    """
    Execute a subscription to wait for a task to reach a certain status or timeout.
    This will return the graphql_queries.task_fragment attributes by default, but this can be overridden with the custom_return_attributes
    """
    subscription = f"""
    subscription TaskWaitForStatus($task_id: Int!){{
        task_by_pk(id: $task_id){{
            {custom_return_attributes if custom_return_attributes is not None else '...task_fragment'}
        }}
    }}
    {graphql_queries.task_fragment if custom_return_attributes is None else ''}
    """
    variables = {"task_id": task_id}
    async for result in mythic_utilities.graphql_subscription(
        mythic=mythic, query=subscription, variables=variables, timeout=timeout
    ):
        if (
            mythic_classes.MythicStatus(result["task_by_pk"]["status"])
            >= return_on_status
        ):
            return result["task_by_pk"]


async def issue_task_all_active_callbacks(
    mythic: mythic_classes.Mythic,
    command_name: str,
    parameters: Union[str, dict],
) -> List[dict]:
    """
    Create a new task within Mythic for all currently active callbacks.
    If you have files that you need to upload and leverage as part of your tasking, use the `register_file` function to get back a file_id.
    For each task created, you'll get a dictionary with:
    {
        "status": either "success" or "error",
        "error": empty if this was successful, otherwise it'll have an error message,
        "id": null if the task wasn't created, otherwise the new ID for your task,
        "callback_id": the id of the callback this was issued to
    }
    The callback_id piece is added in manually by this function so that you can track which callbacks actually created tasks or not
    """
    created_tasks = []
    all_active_callbacks_query = """
    query allActiveCallbacks{
        callback(where: {active: {_eq: true}}){
            id
        }
    }
    """
    all_callbacks = await mythic_utilities.graphql_post(
        mythic=mythic, query=all_active_callbacks_query
    )
    parameter_string = parameters
    if isinstance(parameters, dict):
        parameter_string = json.dumps(parameters)
    for callback in all_callbacks["callback"]:
        submission_status = await mythic_utilities.graphql_post(
            mythic=mythic,
            gql_query=graphql_queries.create_task,
            variables={
                "callback_id": callback["id"],
                "command": command_name,
                "params": parameter_string,
                "tasking_location": "command_line"
                if isinstance(parameters, str)
                else "scripting",
            },
        )
        submission_status["createTask"]["callback_id"] = callback["id"]
        created_tasks.append(submission_status["createTask"])
    return created_tasks


async def issue_task_and_waitfor_task_output(
    mythic: mythic_classes.Mythic,
    command_name: str,
    parameters: Union[str, dict],
    callback_id: int,
    token_id: int = None,
    return_on_status: mythic_classes.MythicStatus = mythic_classes.MythicStatus.Preprocessing,
    timeout: int = None,
) -> bytes:
    task = await issue_task(
        mythic=mythic,
        command_name=command_name,
        parameters=parameters,
        callback_id=callback_id,
        token_id=token_id,
        return_on_status=return_on_status,
        timeout=timeout,
    )
    if "id" not in task or task["id"] is None:
        raise Exception("Failed to create task")
    return await waitfor_for_task_output(
        mythic=mythic, timeout=timeout, task_id=task["id"]
    )


# ######### File Browser Functions ###########


async def get_all_filebrowser_data(
    mythic: mythic_classes.Mythic, custom_return_attributes: str = None
) -> List[dict]:
    """
    Executes a graphql query to get information about all current filebrowser data.
    The default set of attributes returned in the dictionary can be found at graphql_queries.filebrowser_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` and `timestamp` fields, everything else is optional.
    """
    query = f"""
    query CurrentFilebrowserObjects{{
        filebrowserobj(order_by: {{timestamp: asc}}){{
            {custom_return_attributes if custom_return_attributes is not None else '...filebrowser_fragment'}
        }}
    }}
    {graphql_queries.filebrowser_fragment if custom_return_attributes is None else ''}
    """
    initial_filebrowserobjs = await mythic_utilities.graphql_post(
        mythic=mythic, query=query, variables=None
    )
    return initial_filebrowserobjs["filebrowserobj"]


async def subscribe_new_filebrowser(
    mythic: mythic_classes.Mythic,
    fetch_limit: int = 50,
    timeout: int = None,
    custom_return_attributes: str = None,
):
    """
    Executes a graphql query to get information about new filebrowser data since the function was called.
    This returns an async iterator, which can be used as:
        async for item in subscribe_new_filebrowser(...data):
            print(item) <--- item will always be a dictionary based on the data you're getting back
    The default set of attributes returned in the dictionary can be found at graphql_queries.filebrowser_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` and `timestamp` fields, everything else is optional.
    """
    seen_files = set()
    try:
        subscription = f"""
        subscription NewFileBrowser($now: timestamp!, $fetch_limit: Int!){{
            filebrowserobj(where: {{timestamp: {{_gt: $now}}}}, limit: $fetch_limit, order_by: {{timestamp: asc}}){{
                 {custom_return_attributes if custom_return_attributes is not None else '...filebrowser_fragment'}
            }}
        }}
        {graphql_queries.filebrowser_fragment if custom_return_attributes is None else ''}
        """
        latest_time = str(datetime.utcnow())
        while True:
            variables = {"now": latest_time, "fetch_limit": fetch_limit}
            async for result in mythic_utilities.graphql_subscription(
                mythic=mythic, query=subscription, variables=variables, timeout=timeout
            ):
                if len(result["filebrowserobj"]) > 0:
                    for t in result["filebrowserobj"]:
                        if t["id"] in seen_files:
                            continue
                        seen_files.add(t["id"])
                        latest_time = t["timestamp"]
                        yield t
                    if latest_time != variables["now"]:
                        # this means we updated our latest time, update the subscription
                        break

    except Exception as e:
        raise e


async def subscribe_all_filebrowser(
    mythic: mythic_classes.Mythic,
    timeout: int = None,
    custom_return_attributes: str = None,
):
    """
    Executes a graphql query to get information about all filebrowser data so far, then opens up a subscription for new filebrowser data.
    This returns an async iterator, which can be used as:
        async for item in subscribe_all_filebrowser(...data):
            print(item) <--- item will always be a dictionary based on the data you're getting back
    The default set of attributes returned in the dictionary can be found at graphql_queries.filebrowser_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` and `timestamp` fields, everything else is optional.
    """
    for t in await get_all_filebrowser_data(
        mythic=mythic, custom_return_attributes=custom_return_attributes
    ):
        yield t
    async for t in subscribe_new_filebrowser(
        mythic=mythic, timeout=timeout, custom_return_attributes=custom_return_attributes
    ):
        yield t


# ######### Command Functions ##############


async def get_all_commands_for_payloadtype(
    mythic: mythic_classes.Mythic,
    payload_type_name: str,
    custom_return_attributes: str = None,
) -> List:
    """
    Executes a graphql query to get information about all current commands for a payload type.
    The default set of attributes returned in the dictionary can be found at graphql_queries.commands_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `attributes` and `cmd` fields, everything else is optional.
    """
    query = f"""
    query CurrentCommands($payload_type_name: String!){{
        command(where: {{payloadtype: {{ptype: {{_eq: $payload_type_name}}}}, deleted: {{_eq: false}}}}){{
            {custom_return_attributes if custom_return_attributes is not None else '...command_fragment'}
        }}
    }}
    {graphql_queries.command_fragment if custom_return_attributes is None else ''}
    """
    initial_commands = await mythic_utilities.graphql_post(
        mythic=mythic, query=query, variables={"payload_type_name": payload_type_name}
    )
    return initial_commands["command"]


# ######### Payload Functions ##############


async def create_payload(
    mythic: mythic_classes.Mythic,
    payload_type_name: str,
    filename: str,
    operating_system: str,
    c2_profiles: List[dict],
    commands: List[str] = None,
    build_parameters: List[dict] = None,
    description: str = "",
    return_on_complete: bool = True,
    timeout: int = None,
    custom_return_attributes: str = None,
    include_all_commands: bool = False,
) -> dict:
    """
    This tasks Mythic to create a new payload based on the supplied parameters. If `return_on_complete` is false, then this will return immediately after issuing the task to Mythic.
    If `return_on_complete` is true, then this will do a subsequent subscription to wait for the payload container to finish building.
    c2_profiles is a list of dictionaries where each dictionary holds the following information:
        {
            "c2_profile": "name of the profile, like http",
            "c2_profile_parameters": {
                "parameter name": "parameter value",
                "parameter name 2": "parameter value 2"
            }
        }
    The names of these parameters can be found on the C2 Profile page in Mythic and clicking "build info".
    build_parameters is a list of dictionaries where each dictionary holds the following information:
    {
        "name": "build parameter name", "value": "build parameter value"
    }
    The names of the build parameters page can be found on the Payloads page and clicking for "build information".
    commands is a list of the command names you want included in your payload. If you omit this, set it as None, or as an empty array ( [] ), then Mythic will automatically
        include all builtin and recommended commands for the OS you selected.
    custom_return_attributes only applies when you're using `return_on_complete`. Otherwise, you get a dictionary with status, error, and uuid.
    """
    create_payload_dict = {}
    create_payload_dict["selected_os"] = operating_system
    create_payload_dict["filename"] = filename
    create_payload_dict["tag"] = description
    create_payload_dict["payload_type"] = payload_type_name
    create_payload_dict["commands"] = commands if commands is not None else []
    for c in c2_profiles:
        if "c2_profile" not in c:
            raise Exception(
                "C2 Profile instance must have 'c2_profile` key with name of c2 profile"
            )
        if "c2_profile_parameters" not in c or not isinstance(
            c["c2_profile_parameters"], dict
        ):
            raise Exception(
                "C2 Profile instance must have a 'c2_profile_parameters' dictionary where the keys are the c2 profile parameter names and the values are what you want to specify"
            )
    create_payload_dict["c2_profiles"] = c2_profiles
    if build_parameters is not None:
        for p in build_parameters:
            if "name" not in p or "value" not in p:
                raise Exception(
                    "Build Parameters instance must be an array of dictionaries where each dictionary simply has a 'name' and 'value' key"
                )
        create_payload_dict["build_parameters"] = build_parameters
    else:
        create_payload_dict["build_parameters"] = []

    if include_all_commands:
        create_payload_dict["commands"] = []
        initial_commands = await get_all_commands_for_payloadtype(
            mythic=mythic, payload_type_name=payload_type_name
        )
        for c in initial_commands:
            try:
                attributes = json.loads(c["attributes"])
                passes_all_restrictions = True
                if "filter_by_build_parameter" in attributes:
                    # check if the command is allowed by build parameter restrictions
                    for build_param in create_payload_dict["build_parameters"]:
                        if (
                            build_param["name"] in attributes["filter_by_build_parameter"]
                            and attributes["filter_by_build_parameter"]
                            != build_param["value"]
                        ):
                            passes_all_restrictions = False
                if "load_only" in attributes and attributes["load_only"]:
                    passes_all_restrictions = False
                # check if the command is allowed by supported_os
                if (
                    len(attributes["supported_os"]) != 0
                    and operating_system not in attributes["supported_os"]
                ):
                    passes_all_restrictions = False
                if passes_all_restrictions or (
                    "builtin" in attributes and attributes["builtin"]
                ):
                    create_payload_dict["commands"].append(c["cmd"])
            except Exception as e:
                print(f"[-] Error trying to parse command information: {e}")
                pass
    payload = await mythic_utilities.graphql_post(
        mythic=mythic,
        gql_query=graphql_queries.create_payload,
        variables={"payload": json.dumps(create_payload_dict)},
    )
    if return_on_complete:
        # return from this function once the payload successfuly built or errored out
        return await waitfor_payload_complete(
            mythic=mythic,
            payload_uuid=payload["createPayload"]["uuid"],
            timeout=timeout,
            custom_return_attributes=custom_return_attributes,
        )
    else:
        return payload["createPayload"]


async def create_wrapper_payload(
    mythic: mythic_classes.Mythic,
    payload_type_name: str,
    filename: str,
    operating_system: str,
    wrapped_payload_uuid: str,
    build_parameters: List[dict] = None,
    description: str = "",
    return_on_complete: bool = True,
    timeout: int = None,
    custom_return_attributes: str = None,
):
    """
    This tasks Mythic to create a new payload based on the supplied parameters. If `return_on_complete` is false, then this will return immediately after issuing the task to Mythic.
    If `return_on_complete` is true, then this will do a subsequent subscription to wait for the payload container to finish building.
    build_parameters is a list of dictionaries where each dictionary holds the following information:
    {
        "name": "build parameter name", "value": "build parameter value"
    }
    The names of the build parameters page can be found on the Payloads page and clicking for "build information".
    custom_return_attributes only applies when you're using `return_on_complete`. Otherwise, you get a dictionary with status, error, and uuid.
    """
    create_payload_dict = {}
    create_payload_dict["selected_os"] = operating_system
    create_payload_dict["filename"] = filename
    create_payload_dict["tag"] = description
    create_payload_dict["payload_type"] = payload_type_name
    create_payload_dict["c2_profiles"] = []
    create_payload_dict["wrapper"] = True
    if build_parameters is not None:
        for p in build_parameters:
            if "name" not in p or "value" not in p:
                raise Exception(
                    "Build Parameters instance must be an array of dictionaries where each dictionary simply has a 'name' and 'value' key"
                )
    create_payload_dict["build_parameters"] = build_parameters
    create_payload_dict["wrapped_payload"] = wrapped_payload_uuid
    payload = await mythic_utilities.graphql_post(
        mythic=mythic,
        gql_query=graphql_queries.create_payload,
        variables={"payload": json.dumps(create_payload_dict)},
    )
    if return_on_complete:
        # return from this function once the payload successfuly built or errored out
        return await waitfor_payload_complete(
            mythic=mythic,
            payload_uuid=payload["createPayload"]["uuid"],
            timeout=timeout,
            custom_return_attributes=custom_return_attributes,
        )
    else:
        return payload["createPayload"]


async def waitfor_payload_complete(
    mythic: mythic_classes.Mythic,
    payload_uuid: str,
    timeout: int = None,
    custom_return_attributes: str = None,
) -> dict:
    """
    Execute a subscription to wait for the `build_phase` of the specified payload to be something other than 'building'.
    This will return when the payload is finished, either successfully or with an error, or when the timeout is reached.
    The default set of attributes returned in the dictionary can be found at graphql_queries.payload_build_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` and `build_phase` fields, everything else is optional.
    """
    subscription = f"""
        subscription PayloadUpdatedStatus($uuid: String!){{
            payload(where: {{uuid: {{_eq: $uuid}}}}){{
                {custom_return_attributes if custom_return_attributes is not None else '...payload_build_fragment'}
            }}
        }}
        {graphql_queries.payload_build_fragment if custom_return_attributes is None else ''}
        """
    variables = {"uuid": payload_uuid}
    async for result in mythic_utilities.graphql_subscription(
        mythic=mythic, query=subscription, variables=variables, timeout=timeout
    ):
        if len(result["payload"]) > 0:
            if result["payload"][0]["build_phase"] != "building":
                return result["payload"][0]
    return None


async def get_all_payloads(
    mythic: mythic_classes.Mythic, custom_return_attributes: str = None
) -> List[dict]:
    """
    Get information about all payloads currently registered with Mythic (this includes deleted payloads and autogenerated ones for tasking).
    The default attributes returned for each payload can be found at graphql_queries.payload_data_fragment, but can be modified with thte custom_return_attributes variable.
    """
    payload_query = f"""
    query PayloadInfoQuery{{
        payload{{
            {custom_return_attributes if custom_return_attributes is not None else '...payload_data_fragment'}
        }}
    }}
    {graphql_queries.payload_data_fragment if custom_return_attributes is None else ''}
    """
    payloads = await mythic_utilities.graphql_post(mythic=mythic, query=payload_query)
    return payloads["payload"]


async def get_payload_by_uuid(
    mythic: mythic_classes.Mythic,
    payload_uuid: str,
    custom_return_attributes: str = None,
) -> dict:
    """
    Get information about the specified payload.
    The default parameters returned can be found at graphql_queries.payload_data_fragment, but can be modified with the custom_return_attributes
    """
    payload_query = f"""
    query PayloadInfoQuery($payload_uuid: String!){{
        payload(where: {{uuid: {{_eq: $payload_uuid}}}}){{
            {custom_return_attributes if custom_return_attributes is not None else '...payload_data_fragment'}
        }}
    }}
    {graphql_queries.payload_data_fragment if custom_return_attributes is None else ''}
    """
    payloads = await mythic_utilities.graphql_post(
        mythic=mythic, query=payload_query, variables={"payload_uuid": payload_uuid}
    )
    if len(payloads["payload"]) != 1:
        raise Exception("Failed to find payload")
    return payloads["payload"][0]


async def download_payload(
    mythic: mythic_classes.Mythic,
    payload_uuid: str,
) -> bytes:
    """
    Download the raw bytes for the payload specified by payload_uuid
    """
    payload_query = f"""
    query PayloadInfoQuery($uuid: String!){{
        payload(where: {{uuid: {{_eq: $uuid}}}}){{
            ...payload_data_fragment
        }}
    }}
    {graphql_queries.payload_data_fragment}
    """
    payload = await mythic_utilities.graphql_post(
        mythic=mythic, query=payload_query, variables={"uuid": payload_uuid}
    )
    if len(payload["payload"]) != 1:
        raise Exception("Failed to find payload")
    url = f"{mythic.http}{mythic.server_ip}:{mythic.server_port}/direct/download/{payload['payload'][0]['filemetum']['agent_file_id']}"
    try:
        response = await mythic_utilities.http_get(mythic=mythic, url=url)
        return response
    except Exception as e:
        raise e


# ######### Task Output Functions ###########


async def waitfor_for_task_output(
    mythic: mythic_classes.Mythic,
    task_id: int,
    timeout: int = None,
) -> bytes:
    """
    Execute a subscription for the specified task and aggregate all of the output for it.
    This subscription returns when the task is done (completed or errored) or when the timeout is hit.
    The function returns an aggregated binary blob of all of the responses.
    """
    subscription = f"""
        subscription TaskResponses($task_id: Int!){{
            task_by_pk(id: $task_id){{
                status
                responses(order_by: {{id: asc}}){{
                    ...user_output_fragment
                }}
            }}
        }}
        {graphql_queries.user_output_fragment}
    """
    variables = {"task_id": task_id}
    aggregated_output = []
    async for result in mythic_utilities.graphql_subscription(
        mythic=mythic, query=subscription, variables=variables, timeout=timeout
    ):
        aggregated_output = result["task_by_pk"]["responses"]
        if (
            mythic_classes.MythicStatus(result["task_by_pk"]["status"])
            >= mythic_classes.MythicStatus.Completed
        ):
            break
    final_output = b""
    for output in aggregated_output:
        final_output += base64.b64decode(output["response_text"])
    return final_output


async def get_all_task_output(
    mythic: mythic_classes.Mythic, custom_return_attributes: str = None
) -> List[dict]:
    """
    Execute a query to get all current responses.
    The default set of attributes returned in the dictionary can be found at graphql_queries.task_output_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` and `timestamp` fields, everything else is optional.
    """
    query = f"""
    query AllTaskResponses{{
        response(order_by: {{id: asc}}) {{
            {custom_return_attributes if custom_return_attributes is not None else '...task_output_fragment'}
        }}
    }}
    {graphql_queries.task_output_fragment if custom_return_attributes is None else ''}
    """
    initial = await mythic_utilities.graphql_post(
        mythic=mythic, query=query, variables=None
    )
    return initial["response"]


async def get_all_task_output_by_id(
    mythic: mythic_classes.Mythic, task_id: int, custom_return_attributes: str = None
) -> List[dict]:
    """
    Execute a query to get all responses for a given task.
    The default set of attributes returned in the dictionary can be found at graphql_queries.task_output_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` and `timestamp` fields, everything else is optional.
    """
    query = f"""
    query AllTaskResponses($task_id: Int!){{
        response(order_by: {{id: asc}}, where: {{task_id: {{_eq: $task_id}}}}) {{
            {custom_return_attributes if custom_return_attributes is not None else '...task_output_fragment'}
        }}
    }}
    {graphql_queries.task_output_fragment if custom_return_attributes is None else ''}
    """
    initial = await mythic_utilities.graphql_post(
        mythic=mythic, query=query, variables={"task_id": task_id}
    )
    return initial["response"]


async def subscribe_new_task_output(
    mythic: mythic_classes.Mythic,
    timeout: int = None,
    custom_return_attributes: str = None,
    fetch_limit: int = 50,
):
    """
    Execute a subscription to get all new responses.
    This returns an async iterator, which can be used as:
        async for item in subscribe_new_task_output(...data):
            print(item) <--- item will always be a dictionary based on the data you're getting back
    The default set of attributes returned in the dictionary can be found at graphql_queries.task_output_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` and `timestamp` fields, everything else is optional.
    """
    subscription = f"""
    subscription AllNewResponses($now: timestamp!, $fetch_limit: Int!){{
        response(where: {{timestamp: {{_gt: $now}}}}, order_by: {{id: asc}}, limit: $fetch_limit) {{
            {custom_return_attributes if custom_return_attributes is not None else '...task_output_fragment'}
        }}
    }}
    {graphql_queries.task_output_fragment if custom_return_attributes is None else ''}
    """
    seen_files = set()
    try:
        latest_time = str(datetime.utcnow())
        while True:
            variables = {"now": latest_time, "fetch_limit": fetch_limit}
            async for result in mythic_utilities.graphql_subscription(
                mythic=mythic, query=subscription, variables=variables, timeout=timeout
            ):
                if len(result["response"]) > 0:
                    for t in result["response"]:
                        if t["id"] in seen_files:
                            continue
                        seen_files.add(t["id"])
                        latest_time = t["timestamp"]
                        yield t
                    if latest_time != variables["now"]:
                        # this means we updated our latest time, update the subscription
                        break

    except Exception as e:
        raise e


async def subscribe_all_task_output(
    mythic: mythic_classes.Mythic,
    timeout: int = None,
    custom_return_attributes: str = None,
) -> AsyncGenerator:
    """
    Execute a query to get all current responses, then execute a subscription to get all new responses.
    This returns an async iterator, which can be used as:
        async for item in subscribe_all_task_output(...data):
            print(item) <--- item will always be a dictionary based on the data you're getting back
    The default set of attributes returned in the dictionary can be found at graphql_queries.task_output_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` and `timestamp` fields, everything else is optional.
    """
    for t in await get_all_task_output(
        mythic=mythic, custom_return_attributes=custom_return_attributes
    ):
        yield t
    async for t in subscribe_new_task_output(
        mythic=mythic, custom_return_attributes=custom_return_attributes, timeout=timeout
    ):
        yield t


# ########## Operator Functions ##############


async def create_operator(
    mythic: mythic_classes.Mythic,
    username: str,
    password: str,
) -> dict:
    """
    Create a new operator within Mythic with the specified username and password.
    If you want to then add that operator to an operation, use the add_operator_to_operation function.
    This returns a dictionary with the information from the graphql_queries.create_operator_fragment.
    """
    return await mythic_utilities.graphql_post(
        mythic=mythic,
        gql_query=graphql_queries.create_operator,
        variables={"username": username, "password": password},
    )


async def create_apitoken(mythic: mythic_classes.Mythic) -> str:
    """
    Create a new API token for the currently logged in user. If there was an issue in creation, this will raise an exception.
    """
    create_apitoken_mutation = """
    mutation createAPITokenMutation{
        createAPIToken(token_type: "User"){
            id
            token_value
            status
            error
        }
    }
    """
    token = await mythic_utilities.graphql_post(
        mythic=mythic,
        query=create_apitoken_mutation,
        variables=None,
    )
    if token["createAPIToken"]["status"] == "error":
        raise Exception(
            f"Failed to create new token: {token['createAPIToken']['error']} "
        )
    return token["createAPIToken"]["token_value"]


# ########## File Functions ##############


async def register_file(
    mythic: mythic_classes.Mythic, filename: str, contents: bytes
) -> str:
    """
    Upload a file to Mythic via a form and get back a file_id that can be used in tasking.
    Returns the new file_id that can be used in subsequent tasking.
    """
    form = aiohttp.FormData()
    form.add_field("file", value=contents, filename=filename)
    url = f"{mythic.http}{mythic.server_ip}:{mythic.server_port}/api/v1.4/task_upload_file_webhook"
    response = await mythic_utilities.http_post_form(mythic=mythic, data=form, url=url)
    if response["status"] == "success":
        return response["agent_file_id"]
    else:
        logging.error(f"Failed to register_file with Mythic:\n{response['error']}")
        return None


async def download_file(mythic: mythic_classes.Mythic, file_uuid: str) -> bytes:
    url = f"{mythic.http}{mythic.server_ip}:{mythic.server_port}/direct/download/{file_uuid}"
    try:
        response = await mythic_utilities.http_get(mythic=mythic, url=url)
        return response
    except Exception as e:
        raise e


async def get_all_downloaded_files(
    mythic: mythic_classes.Mythic, custom_return_attributes: str = None
) -> List[dict]:
    """
    Execute a query to get metadata about all of the files Mythic knows about that are downloaded from agents.
    To download the contents of a file, use the `download_file` function with the agent_file_id.
    The default set of attributes returned in the dictionary can be found at graphql_queries.file_data_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` field, everything else is optional.
    """
    file_query = f"""
    query downloadedFiles{{
        filemeta(where: {{is_download_from_agent: {{_eq: true}}}}, order_by: {{id: asc}}){{
            {custom_return_attributes if custom_return_attributes is not None else '...file_data_fragment'}
        }}
    }}
    {graphql_queries.file_data_fragment if custom_return_attributes is None else ''}
    """
    downloaded_files = await mythic_utilities.graphql_post(
        mythic=mythic, query=file_query
    )
    return downloaded_files["filemeta"]


async def get_all_screenshots(
    mythic: mythic_classes.Mythic, custom_return_attributes: str = None
) -> List[dict]:
    """
    Execute a query to get metadata about all of the screenshots Mythic knows about that are downloaded from agents.
    To download the contents of a file, use the `download_file` function with the agent_file_id.
    The default set of attributes returned in the dictionary can be found at graphql_queries.file_data_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` field, everything else is optional.
    """
    file_query = f"""
    query downloadedScreenshots{{
        filemeta(where: {{is_screenshot: {{_eq: true}}}}, order_by: {{id: asc}}){{
            {custom_return_attributes if custom_return_attributes is not None else '...file_data_fragment'}
        }}
    }}
    {graphql_queries.file_data_fragment if custom_return_attributes is None else ''}
    """
    downloaded_files = await mythic_utilities.graphql_post(
        mythic=mythic, query=file_query
    )
    return downloaded_files["filemeta"]


async def get_all_uploaded_files(
    mythic: mythic_classes.Mythic, custom_return_attributes: str = None
) -> List[dict]:
    """
    Execute a query to get metadata about all of the uploaded files Mythic knows about.
    To download the contents of a file, use the `download_file` function with the agent_file_id.
    The default set of attributes returned in the dictionary can be found at graphql_queries.file_data_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` field, everything else is optional.
    """
    file_query = f"""
    query uploadedFiles{{
        filemeta(where: {{is_screenshot: {{_eq: false}}, is_download_from_agent: {{_eq: false}}, is_payload: {{_eq: false}}}}, order_by: {{id: asc}}){{
            {custom_return_attributes if custom_return_attributes is not None else '...file_data_fragment'}
        }}
    }}
    {graphql_queries.file_data_fragment if custom_return_attributes is None else ''}
    """
    downloaded_files = await mythic_utilities.graphql_post(
        mythic=mythic, query=file_query
    )
    return downloaded_files["filemeta"]


async def update_file_comment(
    mythic: mythic_classes.Mythic, file_uuid: str, comment: str
) -> dict:
    """
    Update a file's comment within Mythic
    """
    update_comment_mutation = """
    mutation updateCommentMutation($file_uuid: String!, $comment: String!){
        update_filemeta(where: {agent_file_id: {_eq: $file_uuid}}, _set: {comment: $comment}) {
            returning {
                id
                comment
            }
        }
    }
    """
    updated = await mythic_utilities.graphql_post(
        mythic=mythic,
        query=update_comment_mutation,
        variables={"file_uuid": file_uuid, "comment": comment},
    )
    return updated["update_filemeta"]


async def search_files(
    mythic: mythic_classes.Mythic,
    comment: str = "",
    filename: str = "",
    host: str = "",
    custom_return_attributes: str = None,
) -> List[dict]:
    """
    Search across all files in the current operation
    """
    search_files_query = f"""
    query searchFiles($comment: String!, $filename: String!, $host: String!){{
        filemeta(order_by: {{id: asc}}, where: {{host: {{_ilike: $host}}, comment: {{_ilike: $comment}}, _or: [{{filename_text: {{_ilike: $filename}}}}, {{full_remote_path_text: {{_ilike: $filename}}}}]}}) {{
             {custom_return_attributes if custom_return_attributes is not None else '...file_data_fragment'}
        }}
    }}
    {graphql_queries.file_data_fragment if custom_return_attributes is None else ''}
    """
    search_comment = f"%{comment}%" if comment != "" else "%%"
    search_filename = f"%{filename}%" if filename != "" else "%%"
    search_host = f"%{host}%" if host != "" else "%%"
    variables = {
        "comment": search_comment,
        "host": search_host,
        "filename": search_filename,
    }
    searched_files = await mythic_utilities.graphql_post(
        mythic=mythic, query=search_files_query, variables=variables
    )
    return searched_files["filemeta"]


# ########## Operations Functions #############


async def get_operations(
    mythic: mythic_classes.Mythic, custom_return_attributes: str = None
) -> List[dict]:
    """
    Get information about the current operations known to the authenticated user.
    Default return attributes for each operation can be found at graphql_queries.get_operations_fragment, but can be overridden with custom_return_attributes
    """
    get_operations_query = f"""
    query getOperations{{
        operation(order_by: {{name: asc}}) {{
             {custom_return_attributes if custom_return_attributes is not None else '...get_operations_fragment'}
        }}
    }}
    {graphql_queries.get_operations_fragment if custom_return_attributes is None else ''}
    """
    operations = await mythic_utilities.graphql_post(
        mythic=mythic,
        query=get_operations_query,
    )
    return operations["operation"]


async def create_operation(
    mythic: mythic_classes.Mythic,
    operation_name: str,
    custom_return_attributes: str = None,
):
    """
    Create a new operation within Mythic (the account creating the operation will automatically be the operation lead).
    The default attributes returned are outlined in graphql_queries.create_operation_fragment. These can be overridden with the custom_retun_attributes.
    """
    create_operation_query = f"""
    mutation newOperationMutation($name: String){{
        createOperation(name: $name){{
            {custom_return_attributes if custom_return_attributes is not None else '...create_operation_fragment'}
        }}
    }}
    {graphql_queries.create_operation_fragment if custom_return_attributes is None else ''}
    """
    created_operation = await mythic_utilities.graphql_post(
        mythic=mythic,
        query=create_operation_query,
        variables={"name": operation_name},
    )
    return created_operation["createOperation"]


async def add_operator_to_operation(
    mythic: mythic_classes.Mythic,
    operation_name: str,
    operator_username: str,
    view_mode: str = "operator",
    custom_return_attributes: str = None,
) -> dict:
    """
    Add the specified operator to the specified operation. This will raise Exceptions if the operator/operation cannot be found or if the user is already added.
    If you want to adjust the lead of an operation, use the `update_operation` function.
    view_mode can either be "operator", "spectator", "lead" depending on the level of access you want to provide to the new operator in the operation.
    You must be authenticating as the lead of the operation or as a global admin to perform this sort of update.
    The default return values can be found at graphql_queries.add_operator_to_operation_fragment, but can be overridden with the custom_return_attributes.
    """
    # need to get operation id from operation name and operator id from operator name, then create the new object
    operator_and_operation = await mythic_utilities.graphql_post(
        mythic=mythic,
        gql_query=graphql_queries.get_operation_and_operator_by_name,
        variables={
            "operation_name": operation_name,
            "operator_username": operator_username,
        },
    )
    if (
        len(operator_and_operation["operation"]) != 1
        or len(operator_and_operation["operator"]) != 1
    ):
        raise Exception("Didn't find an exact match for the operation name and username")
    if len(operator_and_operation["operation"][0]["operatoroperations"]) != 0:
        raise Exception("Operator already added to operation")
    add_operator_to_operation = f"""
    mutation addNewOperators($operators: [operatoroperation_insert_input!]!) {{
        insert_operatoroperation(objects: $operators) {{
            returning {{
                {custom_return_attributes if custom_return_attributes is not None else '...add_operator_to_operation_fragment'}
            }}
        }}
    }}
    {graphql_queries.add_operator_to_operation_fragment if custom_return_attributes is None else ''}
    """
    variables = {
        "operators": {
            "operation_id": operator_and_operation["operation"][0]["id"],
            "operator_id": operator_and_operation["operator"][0]["id"],
            "view_mode": view_mode,
        }
    }
    add_operator = await mythic_utilities.graphql_post(
        mythic=mythic, query=add_operator_to_operation, variables=variables
    )
    return add_operator["insert_operatoroperation"]


async def remove_operator_from_operation(
    mythic: mythic_classes.Mythic,
    operation_name: str,
    operator_username: str,
    custom_return_attributes: str = None,
) -> dict:
    """
    Removes the specified operator from the specified operation. This will raise Exceptions if the operator/operation cannot be found or if the user isn't part of the operation already.
    If you want to adjust the lead of an operation, use the `update_operation` function.
    You must be authenticating as the lead of the operation or as a global admin to perform this sort of update.
    The default return values can be found at graphql_queries.remove_operator_from_operation_fragment, but can be overridden with the custom_return_attributes.
    """
    operator_and_operation = await mythic_utilities.graphql_post(
        mythic=mythic,
        gql_query=graphql_queries.get_operation_and_operator_by_name,
        variables={
            "operation_name": operation_name,
            "operator_username": operator_username,
        },
    )
    if (
        len(operator_and_operation["operation"]) != 1
        or len(operator_and_operation["operator"]) != 1
    ):
        raise Exception("Didn't find an exact match for the operation name and username")
    if len(operator_and_operation["operation"][0]["operatoroperations"]) != 1:
        raise Exception("Operator not part of operation")
    remove_operator_mutation = f"""
    mutation removeOperatorsFromOperation($operatoroperation_ids: [Int!]!) {{
        delete_operatoroperation(where: {{id: {{_in: $operatoroperation_ids}}}}) {{
            returning {{
                {custom_return_attributes if custom_return_attributes is not None else '...remove_operator_from_operation_fragment'}
            }}
        }}
    }}
    {graphql_queries.remove_operator_from_operation_fragment if custom_return_attributes is None else ''}
    """
    variables = {
        "operatoroperation_ids": [
            operator_and_operation["operation"][0]["operatoroperations"][0]["id"]
        ]
    }
    remove_operator = await mythic_utilities.graphql_post(
        mythic=mythic, query=remove_operator_mutation, variables=variables
    )
    return remove_operator["delete_operatoroperation"]


async def update_operator_in_operation(
    mythic: mythic_classes.Mythic,
    view_mode: str,
    operation_name: str,
    operator_username: str,
    custom_return_attributes: str = None,
) -> dict:
    """
    Updates the specified operator in the specified operation. This will raise Exceptions if the operator/operation cannot be found or if the user isn't part of the operation already.
    If you want to adjust the lead of an operation, use the `update_operation` function.
    You must be authenticating as the lead of the operation or as a global admin to perform this sort of update.
    The default return values can be found at graphql_queries.update_operator_in_operation_fragment, but can be overridden with the custom_return_attributes.
    """
    operator_and_operation = await mythic_utilities.graphql_post(
        mythic=mythic,
        gql_query=graphql_queries.get_operation_and_operator_by_name,
        variables={
            "operation_name": operation_name,
            "operator_username": operator_username,
        },
    )
    if (
        len(operator_and_operation["operation"]) != 1
        or len(operator_and_operation["operator"]) != 1
    ):
        raise Exception("Didn't find an exact match for the operation name and username")
    if len(operator_and_operation["operation"][0]["operatoroperations"]) != 1:
        raise Exception("Operator not part of operation")
    query = f"""
    mutation updateOperatorViewMode($operatoroperation_id: Int!, $view_mode: String!) {{
        update_operatoroperation_by_pk(pk_columns: {{id: $operatoroperation_id}}, _set: {{view_mode: $view_mode}}) {{
            {custom_return_attributes if custom_return_attributes is not None else '...update_operator_in_operation_fragment'}
        }}
    }}
    {graphql_queries.update_operator_in_operation_fragment if custom_return_attributes is None else ''}
    """
    variables = {
        "operatoroperation_id": operator_and_operation["operation"][0][
            "operatoroperations"
        ][0]["id"],
        "view_mode": view_mode,
    }
    update_operator = await mythic_utilities.graphql_post(
        mythic=mythic, query=query, variables=variables
    )
    return update_operator["update_operatoroperation_by_pk"]


async def update_operation(
    mythic: mythic_classes.Mythic,
    operation_name: str,
    lead_operator_username: str = None,
    new_operation_name: str = None,
    channel: str = None,
    display_name: str = None,
    icon_emoji: str = None,
    icon_url: str = None,
    webhook: str = None,
    webhook_message: str = None,
    complete: bool = False,
) -> None:
    """
    This function updates various aspects about the named operation. You must be either the lead of the operation or a global admin to edit this information.
    """
    get_operation_by_name = """
    query getOperationByName($operation_name: String!){
        operation(where: {name: {_eq: $operation_name}}){
            id
            channel
            complete
            display_name
            icon_emoji
            icon_url
            webhook
            webhook_message
            admin {
                id
                username
            }
        }
    }
    """
    operation_info = await mythic_utilities.graphql_post(
        mythic=mythic,
        query=get_operation_by_name,
        variables={"operation_name": operation_name},
    )
    if len(operation_info["operation"]) != 1:
        raise Exception("Failed to find operation by name")
    update_operation_mutation = """
    mutation MyMutation($operation_id: Int!, $channel: String!, $complete: Boolean!, $display_name: String!, $icon_emoji: String!, $icon_url: String!, $name: String!, $webhook: String!, $webhook_message: String!) {
        update_operation_by_pk(pk_columns: {id: $operation_id}, _set: {channel: $channel, complete: $complete, display_name: $display_name, icon_emoji: $icon_emoji, icon_url: $icon_url, name: $name, webhook: $webhook, webhook_message: $webhook_message}) {
            id
            name
            complete
        }
    }
    """
    variables = {
        "operation_id": operation_info["operation"][0]["id"],
        "channel": channel
        if channel is not None
        else operation_info["operation"][0]["channel"],
        "complete": complete,
        "display_name": display_name
        if display_name is not None
        else operation_info["operation"][0]["display_name"],
        "icon_emoji": icon_emoji
        if icon_emoji is not None
        else operation_info["operation"][0]["icon_emoji"],
        "icon_url": icon_url
        if icon_url is not None
        else operation_info["operation"][0]["icon_url"],
        "webhook": webhook
        if webhook is not None
        else operation_info["operation"][0]["webhook"],
        "webhook_message": webhook_message
        if webhook_message is not None
        else operation_info["operation"][0]["webhook_message"],
        "name": new_operation_name if new_operation_name is not None else operation_name,
    }
    await mythic_utilities.graphql_post(
        mythic=mythic,
        query=update_operation_mutation,
        variables=variables,
    )
    if lead_operator_username is not None:
        get_operator_query = """
        query getOperatorByname($username: String!){
            operator(where: {username: {_eq: $username}}){
                id
            }
        }
        """
        operator = await mythic_utilities.graphql_post(
            mythic=mythic,
            query=get_operator_query,
            variables={"username": lead_operator_username},
        )
        if len(operator["operator"]) != 1:
            raise Exception("Failed to find operator")
        update_lead_of_operation = """
        mutation updateLeadMutation($operation_id: Int!, $admin_id: Int!) {
            update_operation_by_pk(pk_columns: {id: $operation_id}, _set: {admin_id: $admin_id}) {
                admin {
                    id
                    username
                }
                id
            }
        }
        """
        await mythic_utilities.graphql_post(
            mythic=mythic,
            query=update_lead_of_operation,
            variables={
                "operation_id": operation_info["operation"][0]["id"],
                "admin_id": operator["operator"][0]["id"],
            },
        )


async def update_current_operation_for_user(
    mythic: mythic_classes.Mythic, operator_id: int, operation_id: int
):
    """
    Sets the specified operation as current for the specified user.
    """
    query = """
    mutation updateCurrentOpertionMutation($operator_id: Int!, $operation_id: Int!) {
        updateCurrentOperation(user_id: $operator_id, operation_id: $operation_id) {
            status
            error
            operation_id
        }
    }
    """
    results = await mythic_utilities.graphql_post(
        mythic=mythic,
        query=query,
        variables={"operator_id": operator_id, "operation_id": operation_id},
    )
    return results["updateCurrentOperation"]


# ############ Process Functions ##############


async def get_latest_processes_on_host(
    mythic: mythic_classes.Mythic, host: str, custom_return_attributes: str = None
) -> AsyncGenerator:
    """
    Execute a query against Mythic to get all of the processes returned by the latest task on this host that hooks into Mythic's process browser.
    This returns an async iterator, which can be used as:
        async for item in get_latest_processes_on_host(...data):
            print(item) <--- item will always be a dictionary based on the data you're getting back
    The default set of attributes returned in the dictionary can be found at graphql_queries.file_data_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` field, everything else is optional.
    """
    process_query = f"""
    query getAllProcessesOnHost($host: String!){{
        process(where: {{host: {{_eq: $host}}}}, order_by: {{task_id: desc}}, limit: 1){{
            task {{
                processes(order_by: {{name: asc}}){{
                    {custom_return_attributes if custom_return_attributes is not None else '...process_data_fragment'}
                }}
            }}
            
        }}
    }}
    {graphql_queries.process_data_fragment if custom_return_attributes is None else ''}
    """
    process_data = await mythic_utilities.graphql_post(
        mythic=mythic, query=process_query, variables={"host": host.upper()}
    )
    if len(process_data["process"]) > 0:
        for t in process_data["process"][0]["task"]["processes"]:
            yield t
    else:
        raise Exception("No process data on host")


# ####### Analytic-based Functions ############


async def get_unique_compromised_hosts(
    mythic: mythic_classes.Mythic,
) -> List[str]:
    """
    Query all callbacks, filebrowser data, and process data in the current operation and get a unique list of hostnames.
    """
    query = """
    query uniqueHosts{
        callback(distinct_on: host) {
            host
        }
        filemeta(distinct_on: host) {
            host
        }
        process(distinct_on: host) {
            host
        }
        payloadonhost(distinct_on: host) {
            host
        }
    }
    """
    results = await mythic_utilities.graphql_post(mythic=mythic, query=query)
    unique_results = set()
    for r in results["callback"]:
        unique_results.add(r["host"])
    for r in results["filemeta"]:
        unique_results.add(r["host"])
    for r in results["process"]:
        unique_results.add(r["host"])
    for r in results["payloadonhost"]:
        unique_results.add(r["host"])
    unique_results.discard("")
    return list(unique_results)


async def get_unique_compromised_accounts(
    mythic: mythic_classes.Mythic,
) -> List[str]:
    """
    Get all of the user accounts from callbacks and credentials, then return a unique list of those.
    """
    query = """
    query uniqueAccounts{
        callback {
            user
            host
            domain
        }
        credential {
            realm
            account
        }
    }
    """
    results = await mythic_utilities.graphql_post(mythic=mythic, query=query)
    unique_results = set()
    for c in results["callback"]:
        if c["domain"] != "":
            unique_results.add(c["domain"] + "/" + c["user"])
        else:
            unique_results.add(c["host"] + "/" + c["user"])
    for c in results["credential"]:
        unique_results.add(c["realm"] + "/" + c["account"])
    return list(unique_results)


async def get_unique_compromised_ips(
    mythic: mythic_classes.Mythic,
) -> List[str]:
    """
    Query all callbacks to get a unique list of ip addresses.
    """
    query = """
    query uniqueIPs{
        callback {
            ip
            external_ip
        }
    }
    """
    results = await mythic_utilities.graphql_post(mythic=mythic, query=query)
    unique_results = set()
    for r in results["callback"]:
        unique_results.add(r["ip"])
        unique_results.add(r["external_ip"])
    unique_results.discard("")
    return list(unique_results)
