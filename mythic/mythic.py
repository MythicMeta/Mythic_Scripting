import base64
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, List, Union
import asyncio

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
"""

LOG_FORMAT = (
    "%(levelname) -4s %(asctime)s %(funcName) "
    "-3s %(lineno) -5d: %(message)s"
)


async def login(
        server_ip: str,
        server_port: int = 7443,
        username: str = None,
        password: str = None,
        apitoken: str = None,
        ssl: bool = True,
        timeout: int = -1,
        logging_level: int = logging.WARNING,
        log_format: str = LOG_FORMAT,
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
        log_level=logging_level,
        log_format=log_format,
        schema=None,
    )
    # logging.basicConfig(format="%(levelname)s:%(message)s", level=logging_level)
    if apitoken is None:
        url = f"{mythic.http}{mythic.server_ip}:{mythic.server_port}/auth"
        data = {
            "username": mythic.username,
            "password": mythic.password,
            "scripting_version": mythic.scripting_version,
        }
        mythic.logger.debug(
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
                mythic=mythic, gql_query=graphql_queries.get_apitokens, variables={"username": mythic.username}
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
            return mythic
        except Exception as e:
            mythic.logger.error(f"[-] Failed to authenticate to Mythic: {str(e)}")
            raise e
    else:
        try:
            return mythic
        except Exception as e:
            mythic.logger.error(f"[-] Failed to authenticate to Mythic: {str(e)}")
            raise e


async def execute_custom_query(
        mythic: mythic_classes.Mythic, query: str, variables: dict = None
) -> dict:
    try:
        return await mythic_utilities.graphql_post(
            mythic=mythic, query=query, variables=variables
        )
    except Exception as e:
        mythic.logger.error(f"Hit an exception within execute_custom_query: {e}")
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
    except asyncio.TimeoutError:
        mythic.logger.warning("Timeout reached in timeout_generator")
        return
    except StopAsyncIteration:
        return
    except Exception as e:
        mythic.logger.error(f"Hit an exception within execute_custom_subscription: {e}")
        raise e


# ########### Callback Functions #############


async def get_all_callbacks(
        mythic: mythic_classes.Mythic, custom_return_attributes: str = None
) -> List[dict]:
    """
    Executes a graphql query to get information about all callbacks (including ones that are no longer active).
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
    Executes a graphql query to get information about all currently active callbacks.
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
        batch_size: int = 50,
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
    try:
        subscription = f"""
        subscription NewCallbacks($now: timestamp!, $batch_size: Int!){{
            callback_stream(where: {{active: {{_eq: true}}}}, cursor: {{initial_value: {{ init_callback: $now}}}}, batch_size: $batch_size){{
                {custom_return_attributes if custom_return_attributes is not None else '...callback_fragment'}
            }}
        }}
        {graphql_queries.callback_fragment if custom_return_attributes is None else ''}
        """
        variables = {"now": str(datetime.utcnow()), "batch_size": batch_size}
        async for result in mythic_utilities.graphql_subscription(
                mythic=mythic, query=subscription, variables=variables, timeout=timeout
        ):
            yield result["callback_stream"]
    except asyncio.TimeoutError:
        mythic.logger.warning("Timeout reached in timeout_generator")
        return
    except StopAsyncIteration:
        return
    except Exception as e:
        mythic.logger.error(f"some other exception in subscribe_new_callbacks: {e}")
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
    try:
        async for t in subscribe_new_callbacks(
                mythic=mythic, timeout=timeout, custom_return_attributes=custom_return_attributes, batch_size=1
        ):
            yield t
    except asyncio.TimeoutError:
        mythic.logger.warning("Timeout reached in timeout_generator")
        return
    except StopAsyncIteration:
        return
    except Exception as e:
        raise e


async def update_callback(
        mythic: mythic_classes.Mythic,
        callback_display_id: int,
        active: bool = None,
        sleep_info: str = None,
        locked: bool = None,
        description: str = None,
        ips: List[str] = None,
        user: str = None,
        host: str = None,
        os: str = None,
        architecture: str = None,
        extra_info: str = None,
        pid: int = None,
        process_name: str = None,
        integrity_level: int = None,
        domain: str = None
):
    update_status = await mythic_utilities.graphql_post(
        mythic=mythic,
        gql_query=graphql_queries.update_callback,
        variables={
            "callback_display_id": callback_display_id,
            "active": active,
            "sleep_info": sleep_info,
            "locked": locked,
            "description": description,
            "ips": ips,
            "user": user,
            "host": host,
            "os": os,
            "architecture": architecture,
            "extra_info": extra_info,
            "pid": pid,
            "process_name": process_name,
            "integrity_level": integrity_level,
            "domain": domain
        },
    )
    return update_status["updateCallback"]


# ########## Task Functions #################


async def get_all_tasks(
        mythic: mythic_classes.Mythic,
        custom_return_attributes: str = None,
        callback_display_id: int = None,
) -> List[dict]:
    """
    Executes a graphql query to get all tasks submitted so far (potentially limited to a single callback).
    The default set of attributes returned in the dictionary can be found at graphql_queries.task_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` field, everything else is optional.
    """
    if callback_display_id is not None:
        query = f"""
        query CurrentTasks($callback_display_id: Int){{
            task(where: {{callback: {{display_id: {{_eq: $callback_display_id}}}}}}, order_by: {{id: asc}}){{
                {custom_return_attributes if custom_return_attributes is not None else '...task_fragment'}
            }}
        }}
        {graphql_queries.task_fragment if custom_return_attributes is None else ''}
        """
        variables = {"callback_display_id": callback_display_id}
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
        batch_size: int = 50,
        timeout: int = None,
        callback_display_id: int = None,
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
    try:
        if callback_display_id is not None:
            subscription = f"""
            subscription NewTasks($now: timestamp!, $batch_size: Int!, $callback_display_id: Int){{
                task_stream(cursor: {{initial_value: {{status_timestamp_submitted: $now}}}}, where: {{callback: {{display_id: {{_eq: $callback_display_id}}}}}}, batch_size: $batch_size){{
                    {custom_return_attributes if custom_return_attributes is not None else '...task_fragment'}
                }}
            }}
            {graphql_queries.task_fragment if custom_return_attributes is None else ''}
            """
            variables = {
                "now": str(datetime.utcnow()),
                "batch_size": batch_size,
                "callback_display_id": callback_display_id,
            }
        else:
            subscription = f"""
            subscription NewTasks($now: timestamp!, $batch_size: Int!){{
                task_stream(batch_size: $batch_size, cursor: {{initial_value: {{status_timestamp_submitted: $now}}}}){{
                    {custom_return_attributes if custom_return_attributes is not None else '...task_fragment'}
                }}
            }}
            {graphql_queries.task_fragment if custom_return_attributes is None else ''}
            """
            variables = {
                "now": str(datetime.utcnow()),
                "batch_size": batch_size,
            }
        try:
            async for result in mythic_utilities.graphql_subscription(
                    mythic=mythic, query=subscription, variables=variables, timeout=timeout
            ):
                yield result["task_stream"]
        except asyncio.TimeoutError:
            mythic.logger.warning("Timeout reached in timeout_generator")
            return
        except StopAsyncIteration:
            return
    except Exception as e:
        raise e


async def subscribe_new_tasks_and_updates(
        mythic: mythic_classes.Mythic,
        batch_size: int = 50,
        timeout: int = None,
        callback_display_id: int = None,
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
    try:
        if callback_display_id is not None:
            subscription = f"""
            subscription NewTasks($now: timestamp!, $batch_size: Int!, $callback_display_id: Int){{
                task_stream(cursor: {{initial_value: {{timestamp: $now}}}}, where: {{callback: {{display_id: {{_eq: $callback_display_id}}}}}}, batch_size: $batch_size){{
                    {custom_return_attributes if custom_return_attributes is not None else '...task_fragment'}
                }}
            }}
            {graphql_queries.task_fragment if custom_return_attributes is None else ''}
            """
            variables = {
                "now": str(datetime.utcnow()),
                "batch_size": batch_size,
                "callback_display_id": callback_display_id,
            }
        else:
            subscription = f"""
            subscription NewTasks($now: timestamp!, $batch_size: Int!){{
                task_stream(batch_size: $batch_size, cursor: {{initial_value: {{timestamp: $now}}}}){{
                    {custom_return_attributes if custom_return_attributes is not None else '...task_fragment'}
                }}
            }}
            {graphql_queries.task_fragment if custom_return_attributes is None else ''}
            """
            variables = {
                "now": str(datetime.utcnow()),
                "batch_size": batch_size,
            }
        try:
            async for result in mythic_utilities.graphql_subscription(
                    mythic=mythic, query=subscription, variables=variables, timeout=timeout
            ):
                yield result["task_stream"]
        except asyncio.TimeoutError:
            mythic.logger.warning("Timeout reached in timeout_generator")
            return
        except StopAsyncIteration:
            return
    except Exception as e:
        raise e


async def subscribe_all_tasks(
        mythic: mythic_classes.Mythic,
        timeout: int = None,
        callback_display_id: int = None,
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
            callback_display_id=callback_display_id,
    ):
        yield t
    try:
        async for t in subscribe_new_tasks(
                mythic=mythic,
                timeout=timeout,
                custom_return_attributes=custom_return_attributes,
                callback_display_id=callback_display_id,
        ):
            yield t
    except asyncio.TimeoutError:
        mythic.logger.warning("Timeout reached in timeout_generator")
        return
    except StopAsyncIteration:
        return
    except Exception as e:
        raise e


async def subscribe_all_tasks_and_updates(
        mythic: mythic_classes.Mythic,
        timeout: int = None,
        callback_display_id: int = None,
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
            callback_display_id=callback_display_id,
    ):
        yield t
    try:
        async for t in subscribe_new_tasks_and_updates(
                mythic=mythic,
                timeout=timeout,
                custom_return_attributes=custom_return_attributes,
                callback_display_id=callback_display_id,
                batch_size=1
        ):
            yield t[0]
    except asyncio.TimeoutError:
        mythic.logger.warning("Timeout reached in timeout_generator")
        return
    except StopAsyncIteration:
        return
    except Exception as e:
        raise e


async def add_mitre_attack_to_task(
        mythic: mythic_classes.Mythic, task_display_id: int, mitre_attack_numbers: List[str]
) -> bool:
    """
    Adds the supplied MITRE ATT&CK techniques to the specified task.
    :return: success or failure in adding the techniques
    """
    try:
        query = """
        mutation MyMutation($task_display_id: Int!,$t_num: String!) {
            addAttackToTask(task_display_id: $task_display_id, t_num: $t_num) {
                status
                error
            }
        }
        """
        for t in mitre_attack_numbers:
            try:
                resp = await mythic_utilities.graphql_post(
                    mythic=mythic,
                    query=query,
                    variables={"task_display_id": task_display_id, "t_num": t},
                )
                if resp["addAttackToTask"]["status"] == "error":
                    mythic.logger.warning(f"Failed to add {t} to {task_display_id}: {resp['addAttackToTask']['error']}")
            except Exception as e:
                mythic.logger.error(str(e))
                return False
        return True

    except Exception as e:
        raise e


async def issue_task(
        mythic: mythic_classes.Mythic,
        command_name: str,
        parameters: Union[str, dict],
        callback_display_id: int,
        token_id: int = None,
        wait_for_complete: bool = False,
        custom_return_attributes: str = None,
        file_ids: [str] = None,
        timeout: int = None,
        is_interactive_task: bool = False,
        interactive_task_type: int = None,
        parent_task_id: int = None,
) -> dict:
    """
    Create a new task within Mythic for a specific callback.
    `return_on_status` indicates if this command should return immediately, mythic_classes.MythicStatus.Preprocessing, or wait for a certain status before returning.
        This can be helpful if you want ot make sure a task is completed before continuing
    If you have files that you need to upload and leverage as part of your tasking, use the `register_file` function to get back a file_id.
        Then supply those file ids in the `file_ids` array AND as their appropriate
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
            "callback_id": callback_display_id,
            "command": command_name,
            "params": parameter_string,
            "token_id": token_id,
            "is_interactive_task": is_interactive_task,
            "interactive_task_type": interactive_task_type,
            "parent_task_id": parent_task_id,
            "tasking_location": "command_line" if isinstance(parameters, str) else "scripting",
            "files": file_ids,
        },
    )
    if submission_status["createTask"]["status"] == "success":
        if wait_for_complete:
            result = await waitfor_task_complete(
                mythic=mythic,
                task_display_id=submission_status["createTask"]["display_id"],
                custom_return_attributes=custom_return_attributes,
                timeout=timeout,
            )
            if result is not None:
                return result
            else:
                raise Exception(f"Failed to get result back from waitfor_task_complete")
        return submission_status["createTask"]
    else:
        raise Exception(
            f"Failed to create task: {submission_status['createTask']['error']}"
        )


async def waitfor_task_complete(
        mythic: mythic_classes.Mythic,
        task_display_id: int,
        custom_return_attributes: str = None,
        timeout: int = None,
) -> dict:
    """
    Execute a subscription to wait for a task to reach a certain status or timeout.
    This will return the graphql_queries.task_fragment attributes by default, but this can be overridden with the custom_return_attributes
    """
    subscription = f"""
    subscription TaskWaitForStatus($task_display_id: Int!){{
        task_stream(cursor: {{initial_value: {{timestamp: "1970-01-01"}}}}, batch_size: 1, where: {{display_id: {{_eq: $task_display_id}}}}){{
            {custom_return_attributes if custom_return_attributes is not None else '...task_fragment'}
        }}
    }}
    {graphql_queries.task_fragment if custom_return_attributes is None else ''}
    """
    variables = {"task_display_id": task_display_id}
    try:
        async for result in mythic_utilities.graphql_subscription(
                mythic=mythic, query=subscription, variables=variables, timeout=timeout
        ):
            if len(result["task_stream"]) != 1:
                raise Exception("task not found")
            if "error" in result["task_stream"][0]["status"] or result["task_stream"][0]["completed"]:
                return result["task_stream"][0]
    except asyncio.TimeoutError:
        mythic.logger.warning("Timeout reached in timeout_generator")
        return {}
    except StopAsyncIteration:
        return {}
    except Exception as e:
        raise e


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
            display_id
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
                "callback_id": callback["display_id"],
                "command": command_name,
                "params": parameter_string,
                "tasking_location": "command_line"
                if isinstance(parameters, str)
                else "scripting",
            },
        )
        submission_status["createTask"]["callback_display_id"] = callback["display_id"]
        created_tasks.append(submission_status["createTask"])
    return created_tasks


async def issue_task_and_waitfor_task_output(
        mythic: mythic_classes.Mythic,
        command_name: str,
        parameters: Union[str, dict],
        callback_display_id: int,
        token_id: int = None,
        timeout: int = None,
) -> bytes:
    task = await issue_task(
        mythic=mythic,
        command_name=command_name,
        parameters=parameters,
        callback_display_id=callback_display_id,
        token_id=token_id,
        wait_for_complete=True,
        timeout=timeout,
    )
    if "display_id" not in task or task["display_id"] is None:
        raise Exception("Failed to create task")
    return await waitfor_for_task_output(
        mythic=mythic, timeout=timeout, task_display_id=task["display_id"]
    )


# ######### File Browser Functions ###########


async def get_all_filebrowser(
        mythic: mythic_classes.Mythic, custom_return_attributes: str = None,
        host: str = None,
        batch_size: int = 100,
) -> AsyncGenerator:
    """
    Executes a graphql query to get information about all current filebrowser data.
    This returns an async iterator, which can be used as:
        async for item in get_all_filebrowser(...data):
            print(item) <--- item will always be a dictionary based on the data you're getting back
    The default set of attributes returned in the dictionary can be found at graphql_queries.filebrowser_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` and `timestamp` fields, everything else is optional.
    """
    query = f"""
    query getAllFileBrowserObjects($host: String!, $batch_size: Int!, $offset: Int!){{
        mythictree(limit: $batch_size, offset: $offset, where: {{host: {{_ilike: $host}}, tree_type: {{_eq: "file"}}}}){{
            {custom_return_attributes if custom_return_attributes is not None else '...mythictree_fragment'}
        }}
    }}
    {graphql_queries.mythictree_fragment if custom_return_attributes is None else ''}
    """
    host_search = host
    if host_search is None:
        host_search = "%_%"
    else:
        host_search = f"%{host_search}%"
    offset = 0
    while True:
        output = await mythic_utilities.graphql_post(
            mythic=mythic, query=query, variables={"host": host_search, "batch_size": batch_size, "offset": offset}
        )
        if len(output["mythictree"]) > 0:
            yield output["mythictree"]
            offset += len(output["mythictree"])
        else:
            break


async def subscribe_new_filebrowser(
        mythic: mythic_classes.Mythic,
        host: str = None,
        batch_size: int = 50,
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
    host_search = host
    if host_search is None:
        host_search = "%_%"
    else:
        host_search = f"%{host_search}%"
    process_query = f"""
    subscription getAllProcessesOnHost($host: String!, $batch_size: Int!, $now: timestamp!){{
        mythictree_stream(batch_size: $batch_size, where: {{host: {{_ilike: $host}}, tree_type: {{_eq: "file"}}}}, cursor: {{initial_value: {{timestamp: $now}}}}){{
            {custom_return_attributes if custom_return_attributes is not None else '...mythictree_fragment'}
        }}
    }}
    {graphql_queries.mythictree_fragment if custom_return_attributes is None else ''}
    """
    try:
        async for output in mythic_utilities.graphql_subscription(
                mythic=mythic, query=process_query,
                variables={"host": host_search, "batch_size": batch_size, "now": str(datetime.utcnow())},
                timeout=timeout
        ):
            yield output["mythictree_stream"]
    except asyncio.TimeoutError:
        mythic.logger.warning("Timeout reached in timeout_generator")
        return
    except StopAsyncIteration:
        return
    except Exception as e:
        raise e


async def subscribe_all_filebrowser(
        mythic: mythic_classes.Mythic,
        host: str = None,
        timeout: int = None,
        batch_size: int = 100,
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
    async for t in get_all_filebrowser(
            mythic=mythic, custom_return_attributes=custom_return_attributes,
            host=host, batch_size=batch_size
    ):
        yield t
    try:
        async for t in subscribe_new_filebrowser(
                mythic=mythic, timeout=timeout, custom_return_attributes=custom_return_attributes,
                host=host, batch_size=batch_size
        ):
            yield t
    except asyncio.TimeoutError:
        mythic.logger.warning("Timeout reached in timeout_generator")
        return
    except StopAsyncIteration:
        return
    except Exception as e:
        raise e


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
        command(where: {{payloadtype: {{name: {{_eq: $payload_type_name}}}}, deleted: {{_eq: false}}}}){{
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
    custom_return_attributes only applies when you're using `return_on_complete`.
    Otherwise, you get a dictionary with status, error, and uuid.
    """
    create_payload_dict = {}
    create_payload_dict["selected_os"] = operating_system
    create_payload_dict["filename"] = filename
    create_payload_dict["description"] = description
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
                attributes = c["attributes"]
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
    create_payload_dict["description"] = description
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
    try:
        async for result in mythic_utilities.graphql_subscription(
                mythic=mythic, query=subscription, variables=variables, timeout=timeout
        ):
            if len(result["payload"]) > 0:
                if result["payload"][0]["build_phase"] != "building":
                    return result["payload"][0]
    except asyncio.TimeoutError:
        mythic.logger.warning("Timeout reached in timeout_generator")
        return
    except StopAsyncIteration:
        return
    except Exception as e:
        raise e
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
    try:
        return await download_file(mythic=mythic, file_uuid=payload['payload'][0]['filemetum']['agent_file_id'])
    except Exception as e:
        raise e


async def payload_check_config(mythic: mythic_classes.Mythic,
                               payload_uuid: str,
                               ) -> dict:
    """
    Check the payload's configuration against C2 profile configurations
    :param mythic:
    :param payload_uuid:
    :return: dict with status, error, and output keys
    """
    config_query = f"""
    query checkPayloadConfig($uuid: String!){{
        config_check(uuid: $uuid){{
            status
            error
            output
        }}
    }}
    """
    configStatus = await mythic_utilities.graphql_post(
        mythic=mythic, query=config_query, variables={"uuid": payload_uuid}
    )
    return configStatus["config_check"]


async def payload_redirect_rules(mythic: mythic_classes.Mythic,
                                 payload_uuid: str,
                                 ) -> dict:
    """
    Get redirect rules for a payload
    :param mythic:
    :param payload_uuid:
    :return: dict with status, error, and output keys
    """
    config_query = f"""
    query checkPayloadRedirectRules($uuid: String!){{
        redirect_rules(uuid: $uuid){{
            status
            error
            output
        }}
    }}
    """
    redirectRules = await mythic_utilities.graphql_post(
        mythic=mythic, query=config_query, variables={"uuid": payload_uuid}
    )
    return redirectRules["redirect_rules"]


# ######### Task Output Functions ###########


async def waitfor_for_task_output(
        mythic: mythic_classes.Mythic,
        task_display_id: int,
        timeout: int = None,
) -> bytes:
    """
    Execute a subscription for the specified task and aggregate all of the output for it.
    This subscription returns when the task is done (completed or errored) or when the timeout is hit.
    The function returns an aggregated binary blob of all of the responses.
    """
    subscription = f"""
        subscription TaskResponses($task_display_id: Int!){{
            task_stream(cursor: {{initial_value: {{timestamp: "1970-01-01"}}}}, batch_size: 1, where: {{display_id: {{_eq: $task_display_id}}}}){{
                status
                completed
                responses(order_by: {{id: asc}}){{
                    ...user_output_fragment
                }}
            }}
        }}
        {graphql_queries.user_output_fragment}
    """
    variables = {"task_display_id": task_display_id}
    aggregated_output = []
    try:
        async for result in mythic_utilities.graphql_subscription(
                mythic=mythic, query=subscription, variables=variables, timeout=timeout
        ):
            aggregated_output = result["task_stream"][0]["responses"]
            if "error" in result["task_stream"][0]["status"] or result["task_stream"][0]["completed"]:
                break
    except asyncio.TimeoutError:
        mythic.logger.warning("Timeout reached in timeout_generator")
    except StopAsyncIteration:
        pass
    except Exception as e:
        raise e
    final_output = b""
    for output in aggregated_output:
        final_output += base64.b64decode(output["response_text"])
    subtaskIds = await get_all_subtask_ids(mythic=mythic, task_display_id=task_display_id,
                                           fetch_display_id_instead=True)
    for subtask in subtaskIds:
        subtaskOutput = await get_all_task_output_by_id(mythic=mythic, task_display_id=subtask)
        for r in subtaskOutput:
            final_output += base64.b64decode(r["response_text"])
    return final_output


async def get_all_subtask_ids(mythic: mythic_classes.Mythic, task_display_id: int,
                              fetch_display_id_instead: bool) -> List[int]:
    subtaskIds = []
    idQuery = f"""
    query taskIdFromDisplayID($task_display_id: Int!){{
        task(where: {{display_id: {{_eq: $task_display_id}}}}){{
            id
        }}
    }}
    """
    subtaskQuery = """
    query subtaskList($task_id: Int!){
        task(where: {parent_task_id: {_eq: $task_id}}){
            id
            display_id
        }
    }
    """
    initial = await mythic_utilities.graphql_post(
        mythic=mythic, query=idQuery, variables={"task_display_id": task_display_id}
    )
    if initial["task"]:
        taskIdsToCheck = [initial["task"][0]["id"]]
        while len(taskIdsToCheck) > 0:
            currentTaskId = taskIdsToCheck.pop()
            subtasks = await mythic_utilities.graphql_post(
                mythic=mythic, query=subtaskQuery, variables={"task_id": currentTaskId}
            )
            for t in subtasks["task"]:
                taskIdsToCheck.append(t["id"])
                if fetch_display_id_instead:
                    subtaskIds.append(t["display_id"])
                else:
                    subtaskIds.append(t["id"])
    return subtaskIds


async def get_all_task_output(
        mythic: mythic_classes.Mythic, custom_return_attributes: str = None, batch_size: int = 10
) -> AsyncGenerator:
    """
    Execute a query to get all current responses.
    The default set of attributes returned in the dictionary can be found at graphql_queries.task_output_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` and `timestamp` fields, everything else is optional.
    """
    query = f"""
    query AllTaskResponses($batch_size: Int!, $offset: Int!){{
        response(order_by: {{id: asc}}, limit: $batch_size, offset: $offset) {{
            {custom_return_attributes if custom_return_attributes is not None else '...task_output_fragment'}
        }}
    }}
    {graphql_queries.task_output_fragment if custom_return_attributes is None else ''}
    """
    offset = 0
    while True:
        initial = await mythic_utilities.graphql_post(
            mythic=mythic, query=query, variables={"batch_size": batch_size, "offset": offset}
        )
        if len(initial["response"]) > 0:
            yield initial["response"]
            offset += len(initial["response"])
        else:
            break


async def get_all_task_output_by_id(
        mythic: mythic_classes.Mythic, task_display_id: int, custom_return_attributes: str = None
) -> List[dict]:
    """
    Execute a query to get all responses for a given task.
    The default set of attributes returned in the dictionary can be found at graphql_queries.task_output_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` and `timestamp` fields, everything else is optional.
    """
    query = f"""
    query AllTaskResponses($task_display_id: Int!){{
        response(order_by: {{id: asc}}, where: {{task:{{display_id: {{_eq: $task_display_id}}}}}}) {{
            {custom_return_attributes if custom_return_attributes is not None else '...task_output_fragment'}
        }}
    }}
    {graphql_queries.task_output_fragment if custom_return_attributes is None else ''}
    """
    initial = await mythic_utilities.graphql_post(
        mythic=mythic, query=query, variables={"task_display_id": task_display_id}
    )
    return initial["response"]


async def get_all_task_and_subtask_output_by_id(
        mythic: mythic_classes.Mythic, task_display_id: int, custom_return_attributes: str = None
) -> List[dict]:
    """
    Execute a query to get all responses for a given task.
    The default set of attributes returned in the dictionary can be found at graphql_queries.task_output_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` and `timestamp` fields, everything else is optional.
    """
    query = f"""
    query AllTaskResponses($task_display_id: Int!){{
        response(order_by: {{id: asc}}, where: {{task:{{display_id: {{_eq: $task_display_id}}}}}}) {{
            {custom_return_attributes if custom_return_attributes is not None else '...task_output_fragment'}
        }}
    }}
    {graphql_queries.task_output_fragment if custom_return_attributes is None else ''}
    """
    initial = await mythic_utilities.graphql_post(
        mythic=mythic, query=query, variables={"task_display_id": task_display_id}
    )
    subtaskIds = await get_all_subtask_ids(mythic=mythic, task_display_id=task_display_id,
                                           fetch_display_id_instead=True)
    for subtask in subtaskIds:
        subtaskOutput = await get_all_task_output_by_id(mythic=mythic, task_display_id=subtask)
        for r in subtaskOutput:
            initial["response"].append(r)
    return initial["response"]


async def subscribe_new_task_output(
        mythic: mythic_classes.Mythic,
        timeout: int = None,
        custom_return_attributes: str = None,
        batch_size: int = 50,
) -> AsyncGenerator:
    """
    Execute a subscription to get all new responses.
    This returns an async iterator, which can be used as:
        async for item in subscribe_new_task_output(...data):
            print(item) <--- item will always be a dictionary based on the data you're getting back
    The default set of attributes returned in the dictionary can be found at graphql_queries.task_output_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` and `timestamp` fields, everything else is optional.
    """
    subscription = f"""
    subscription AllNewResponses($now: timestamp!, $batch_size: Int!){{
        response_stream(cursor: {{initial_value: {{timestamp: $now}}}}, batch_size: $batch_size) {{
            {custom_return_attributes if custom_return_attributes is not None else '...task_output_fragment'}
        }}
    }}
    {graphql_queries.task_output_fragment if custom_return_attributes is None else ''}
    """

    latest_time = str(datetime.utcnow())
    while True:
        variables = {"now": latest_time, "batch_size": batch_size}
        try:
            async for result in mythic_utilities.graphql_subscription(
                    mythic=mythic, query=subscription, variables=variables, timeout=timeout
            ):
                yield result["response_stream"]
        except asyncio.TimeoutError:
            mythic.logger.warning("Timeout reached in timeout_generator")
            return
        except StopAsyncIteration:
            return
        except Exception as e:
            mythic.logger.error(e)
            return


async def subscribe_all_task_output(
        mythic: mythic_classes.Mythic,
        timeout: int = None,
        custom_return_attributes: str = None,
        batch_size: int = 10
) -> AsyncGenerator:
    """
    Execute a query to get all current responses, then execute a subscription to get all new responses.
    This returns an async iterator, which can be used as:
        async for item in subscribe_all_task_output(...data):
            print(item) <--- item will always be a dictionary based on the data you're getting back
    The default set of attributes returned in the dictionary can be found at graphql_queries.task_output_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` and `timestamp` fields, everything else is optional.
    """
    async for t in get_all_task_output(
            mythic=mythic, custom_return_attributes=custom_return_attributes, batch_size=batch_size
    ):
        yield t
    try:
        async for t in subscribe_new_task_output(
                mythic=mythic, custom_return_attributes=custom_return_attributes, timeout=timeout, batch_size=batch_size
        ):
            yield t
    except asyncio.TimeoutError:
        mythic.logger.warning("Timeout reached in timeout_generator")
        return
    except StopAsyncIteration:
        return
    except Exception as e:
        raise e


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


async def set_admin_status(mythic: mythic_classes.Mythic, username: str, admin: bool) -> dict:
    resp = await execute_custom_query(
        mythic=mythic,
        query="""
        mutation updateOperatorAdminStatus($username: String!, $admin: Boolean){
            update_operator(_set: {admin: $admin}, where: {username: {_eq: $username}}){
                returning {
                    id
                    admin
                }
            }
        }
        """,
        variables={"username": username, "admin": admin},
    )
    return resp


async def set_active_status(mythic: mythic_classes.Mythic, username: str, active: bool) -> dict:
    resp = await execute_custom_query(
        mythic=mythic,
        query="""
        mutation updateOperatorActiveStatus($username: String!, $active: Boolean){
            update_operator(_set: {active: $active}, where: {username: {_eq: $username}}){
                returning {
                    id
                    active
                }
            }
        }
        """,
        variables={"username": username, "admin": active},
    )
    return resp


async def set_password(mythic: mythic_classes.Mythic, username: str, new_password: str,
                       old_password: str = None) -> dict:
    resp = await execute_custom_query(
        mythic=mythic,
        query="""
        query getUserID($username: String!) {
            operator(where: {username: {_eq: $username}}){
                id
            }
        }
        """,
        variables={"username": username}
    )
    if len(resp["operator"]) != 1:
        raise Exception("Failed to find operator")

    response = await execute_custom_query(
        mythic=mythic,
        query="""
        mutation updateOperatorPassword($user_id: Int!, $new_password: String!, $old_password: String){
            updatePassword(user_id: $user_id, new_password: $new_password, old_password: $old_password){
                status
                error
            }
        }
        """,
        variables={"user_id": resp["operator"][0]["id"], "new_password": new_password, "old_password": old_password},
    )
    return response["updatePassword"]


async def get_operator(mythic: mythic_classes.Mythic, username: str, custom_return_attributes: str = None) -> dict:
    resp = await execute_custom_query(
        mythic=mythic,
        query=f"""
        query getUserID($username: String!) {{
            operator(where: {{username: {{_eq: $username}}}}){{
                {custom_return_attributes if custom_return_attributes is not None else '...operator_fragment'}
            }}
        }}
        {graphql_queries.operator_fragment if custom_return_attributes is None else ''}
        """,
        variables={"username": username}
    )
    return resp


async def get_me(mythic: mythic_classes.Mythic) -> dict:
    resp = await execute_custom_query(
        mythic=mythic,
        query=f"""
        query getMe {{
            meHook{{
                status
                error
                current_operation_id
                current_operation
            }}
        }}
        """,
    )
    return resp


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
        mythic.logger.error(f"Failed to register_file with Mythic:\n{response['error']}")
        return None


async def download_file(mythic: mythic_classes.Mythic, file_uuid: str) -> bytes:
    url = f"{mythic.http}{mythic.server_ip}:{mythic.server_port}/direct/download/{file_uuid}"
    try:
        response = await mythic_utilities.http_get(mythic=mythic, url=url)
        return response
    except Exception as e:
        raise e


async def download_file_chunked(
        mythic: mythic_classes.Mythic, file_uuid: str, chunk_size: int = 512000
) -> AsyncGenerator:
    url = f"{mythic.http}{mythic.server_ip}:{mythic.server_port}/direct/download/{file_uuid}"
    try:
        async for t in mythic_utilities.http_get_chunked(
                mythic=mythic, url=url, chunk_size=chunk_size
        ):
            yield t
    except Exception as e:
        raise e


async def get_all_downloaded_files(
        mythic: mythic_classes.Mythic, custom_return_attributes: str = None, batch_size: int = 100
) -> AsyncGenerator:
    """
    Execute a query to get metadata about all files Mythic knows about that are downloaded from agents.
    To download the contents of a file, use the `download_file` function with the agent_file_id.
    This returns an async iterator, which can be used as:
        async for item in get_all_downloaded_files(...data):
            print(item) <--- item will always be a dictionary based on the data you're getting back
    The default set of attributes returned in the dictionary can be found at graphql_queries.file_data_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` field, everything else is optional.
    """
    file_query = f"""
    query downloadedFiles($batch_size: Int!, $offset: Int!){{
        filemeta(where: {{is_download_from_agent: {{_eq: true}}, complete: {{_eq: true}}}}, order_by: {{id: asc}}, limit: $batch_size, offset: $offset){{
            {custom_return_attributes if custom_return_attributes is not None else '...file_data_fragment'}
        }}
    }}
    {graphql_queries.file_data_fragment if custom_return_attributes is None else ''}
    """
    offset = 0
    while True:
        output = await mythic_utilities.graphql_post(
            mythic=mythic, query=file_query, variables={"batch_size": batch_size, "offset": offset}
        )
        if len(output["filemeta"]) > 0:
            yield output["filemeta"]
            offset += len(output["filemeta"])
        else:
            break


async def subscribe_new_downloaded_files(mythic: mythic_classes.Mythic,
                                         custom_return_attributes: str = None,
                                         timeout: int = None,
                                         batch_size: int = 10) -> AsyncGenerator:
    """
        Execute a query to get metadata about all files Mythic knows about that are downloaded from agents.
        To download the contents of a file, use the `download_file` function with the agent_file_id.
        The default set of attributes returned in the dictionary can be found at graphql_queries.file_data_fragment.
        If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` field, everything else is optional.
        """
    file_query = f"""
        subscription downloadedFiles($batch_size: Int!, $now: timestamp!){{
            filemeta_stream(where: {{is_download_from_agent: {{_eq: true}}, complete: {{_eq: true}}}}, cursor: {{initial_value: {{timestamp: $now}}}}, batch_size: $batch_size){{
                {custom_return_attributes if custom_return_attributes is not None else '...file_data_fragment'}
            }}
        }}
        {graphql_queries.file_data_fragment if custom_return_attributes is None else ''}
        """
    try:
        async for result in mythic_utilities.graphql_subscription(
                mythic=mythic, query=file_query, timeout=timeout,
                variables={"batch_size": batch_size, "now": str(datetime.utcnow())}
        ):
            yield result["filemeta_stream"]
    except asyncio.TimeoutError:
        mythic.logger.warning("Timeout reached in timeout_generator")
        return
    except StopAsyncIteration:
        return
    except Exception as e:
        raise e


async def subscribe_all_downloaded_files(mythic: mythic_classes.Mythic,
                                         custom_return_attributes: str = None,
                                         timeout: int = None,
                                         batch_size: int = 10) -> AsyncGenerator:
    """
        Execute a query to get metadata about all files Mythic knows about that are downloaded from agents.
        To download the contents of a file, use the `download_file` function with the agent_file_id.
        The default set of attributes returned in the dictionary can be found at graphql_queries.file_data_fragment.
        If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` field, everything else is optional.
        """
    async for result in get_all_downloaded_files(
            mythic=mythic, batch_size=batch_size, custom_return_attributes=custom_return_attributes
    ):
        yield result
    try:
        async for result in subscribe_new_downloaded_files(
                mythic=mythic, batch_size=batch_size, timeout=timeout, custom_return_attributes=custom_return_attributes
        ):
            yield result
    except asyncio.TimeoutError:
        mythic.logger.warning("Timeout reached in timeout_generator")
        return
    except StopAsyncIteration:
        return
    except Exception as e:
        raise e


async def get_all_screenshots(
        mythic: mythic_classes.Mythic, custom_return_attributes: str = None, batch_size: int = 10
) -> AsyncGenerator:
    """
    Execute a query to get metadata about all of the screenshots Mythic knows about that are downloaded from agents.
    To download the contents of a file, use the `download_file` function with the agent_file_id.
    This returns an async iterator, which can be used as:
        async for item in get_all_screenshots(...data):
            print(item) <--- item will always be a dictionary based on the data you're getting back
    The default set of attributes returned in the dictionary can be found at graphql_queries.file_data_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` field, everything else is optional.
    """
    file_query = f"""
    query downloadedScreenshots($batch_size: Int!, $offset: Int!){{
        filemeta(where: {{is_screenshot: {{_eq: true}}, complete: {{_eq: true}}}}, order_by: {{id: asc}}, limit: $batch_size, offset: $offset){{
            {custom_return_attributes if custom_return_attributes is not None else '...file_data_fragment'}
        }}
    }}
    {graphql_queries.file_data_fragment if custom_return_attributes is None else ''}
    """
    offset = 0
    while True:
        output = await mythic_utilities.graphql_post(
            mythic=mythic, query=file_query, variables={"batch_size": batch_size, "offset": offset}
        )
        if len(output["filemeta"]) > 0:
            yield output["filemeta"]
            offset += len(output["filemeta"])
        else:
            break


async def get_all_uploaded_files(
        mythic: mythic_classes.Mythic, custom_return_attributes: str = None, batch_size: int = 10,
) -> AsyncGenerator:
    """
    Execute a query to get metadata about all of the uploaded files Mythic knows about.
    To download the contents of a file, use the `download_file` function with the agent_file_id.
    This returns an async iterator, which can be used as:
        async for item in get_all_uploaded_files(...data):
            print(item) <--- item will always be a dictionary based on the data you're getting back
    The default set of attributes returned in the dictionary can be found at graphql_queries.file_data_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` field, everything else is optional.
    """
    file_query = f"""
    query uploadedFiles($batch_size: Int!, $offset: Int!){{
        filemeta(where: {{is_screenshot: {{_eq: false}}, is_download_from_agent: {{_eq: false}}, is_payload: {{_eq: false}}}}, order_by: {{id: asc}}, limit: $batch_size, offset: $offset){{
            {custom_return_attributes if custom_return_attributes is not None else '...file_data_fragment'}
        }}
    }}
    {graphql_queries.file_data_fragment if custom_return_attributes is None else ''}
    """
    offset = 0
    while True:
        output = await mythic_utilities.graphql_post(
            mythic=mythic, query=file_query, variables={"batch_size": batch_size, "offset": offset}
        )
        if len(output["filemeta"]) > 0:
            yield output["filemeta"]
            offset += len(output["filemeta"])
        else:
            break


async def get_latest_uploaded_file_by_name(
        mythic: mythic_classes.Mythic, custom_return_attributes: str = None, filename: str = None,
) -> dict:
    """
    Execute a query to get metadata about the uploaded file by name.
    To download the contents of a file, use the `download_file` function with the agent_file_id.
    The default set of attributes returned in the dictionary can be found at graphql_queries.file_data_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` field, everything else is optional.
    """
    file_query = f"""
    query uploaded_file_by_name($filename: String!){{
        filemeta(where: {{is_screenshot: {{_eq: false}}, is_download_from_agent: {{_eq: false}}, is_payload: {{_eq: false}}, deleted: {{_eq: false}}, filename_utf8: {{_eq: $filename}}}}, order_by: {{id: desc}}, limit: 1){{
            {custom_return_attributes if custom_return_attributes is not None else '...file_data_fragment'}
        }}
    }}
    {graphql_queries.file_data_fragment if custom_return_attributes is None else ''}
    """
    output = await mythic_utilities.graphql_post(
        mythic=mythic, query=file_query,
    )
    return output["filemeta"][0] if output["filemeta"] else {}


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
    add_operator_to_operation_query = f"""
    mutation addNewOperators($operation_id: Int!, $add_users: [Int]) {{
        updateOperatorOperation(operation_id: $operation_id, add_users: $add_users) {{
            {custom_return_attributes if custom_return_attributes is not None else '...add_operator_to_operation_fragment'}
        }}
    }}
    {graphql_queries.add_operator_to_operation_fragment if custom_return_attributes is None else ''}
    """
    variables = {
        "operation_id": operator_and_operation["operation"][0]["id"],
        "add_users": [operator_and_operation["operator"][0]["id"]],
    }
    add_operator = await mythic_utilities.graphql_post(
        mythic=mythic, query=add_operator_to_operation_query, variables=variables
    )
    return add_operator["updateOperatorOperation"]


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
    mutation removeOperators($operation_id: Int!, $remove_users: [Int]) {{
        updateOperatorOperation(operation_id: $operation_id, remove_users: $remove_users) {{
            {custom_return_attributes if custom_return_attributes is not None else '...remove_operator_from_operation_fragment'}
        }}
    }}
    {graphql_queries.remove_operator_from_operation_fragment if custom_return_attributes is None else ''}
    """
    variables = {
        "operation_id": operator_and_operation["operation"][0]["id"],
        "remove_users": [operator_and_operation["operator"][0]["id"]],
    }
    remove_operator = await mythic_utilities.graphql_post(
        mythic=mythic, query=remove_operator_mutation, variables=variables
    )
    return remove_operator["updateOperatorOperation"]


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
    mutation updateOperatorViewMode($operation_id: Int!, $view_mode_operators: [Int], $view_mode_spectators: [Int]) {{
        updateOperatorOperation(operation_id: $operation_id, view_mode_operators: $view_mode_operators, view_mode_spectators: $view_mode_spectators) {{
            {custom_return_attributes if custom_return_attributes is not None else '...update_operator_in_operation_fragment'}
        }}
    }}
    {graphql_queries.update_operator_in_operation_fragment if custom_return_attributes is None else ''}
    """
    variables = {
        "operation_id": operator_and_operation["operation"][0]["id"],
        "view_mode_operators": [operator_and_operation["operator"][0]["id"]] if view_mode == "operator" else [],
        "view_mode_spectators": [operator_and_operation["operator"][0]["id"]] if view_mode == "spectator" else [],
    }
    update_operator = await mythic_utilities.graphql_post(
        mythic=mythic, query=query, variables=variables
    )
    return update_operator["updateOperatorOperation"]


async def update_operation(
        mythic: mythic_classes.Mythic,
        operation_name: str,
        lead_operator_username: str = None,
        new_operation_name: str = None,
        channel: str = None,
        webhook: str = None,
        complete: bool = None,
        deleted: bool = None,
) -> None:
    """
    This function updates various aspects about the named operation. You must be either the lead of the operation or a global admin to edit this information.
    """
    get_operation_by_name = """
    query getOperationByName($operation_name: String!){
        operation(where: {name: {_eq: $operation_name}}){
            id
            channel
            name
            complete
            deleted
            webhook
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
    admin_id = None
    if lead_operator_username is not None:
        get_operator_query = """
        query getOperatorByName($username: String!){
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
        admin_id = operator["operator"][0]["id"]
    update_operation_mutation = """
    mutation MyMutation($operation_id: Int!, $channel: String, $complete: Boolean, $name: String, $webhook: String, $deleted: Boolean, $admin_id: Int) {
        updateOperation(operation_id: $operation_id, channel: $channel, complete: $complete, name: $name, webhook: $webhook, deleted: $deleted, admin_id: $admin_id) {
            id
            name
            complete
            channel
            webhook
            admin_id
            deleted
        }
    }
    """
    variables = {
        "operation_id": operation_info["operation"][0]["id"],
        "channel": channel,
        "complete": complete,
        "webhook": webhook,
        "name": new_operation_name,
        "deleted": deleted,
        "admin_id": admin_id,
    }
    result = await mythic_utilities.graphql_post(
        mythic=mythic,
        query=update_operation_mutation,
        variables=variables,
    )
    return result["updateOperation"]


async def update_current_operation_for_user(
        mythic: mythic_classes.Mythic, operator_id: int, operation_id: int
):
    """
    Sets the specified operation as current for the specified user.
    """
    query = """
    mutation updateCurrentOperationMutation($operator_id: Int!, $operation_id: Int!) {
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


async def subscribe_new_processes(
        mythic: mythic_classes.Mythic,
        host: str = None,
        custom_return_attributes: str = None,
        batch_size: int = 100,
        timeout: int = None
) -> AsyncGenerator:
    """
    Execute a query against Mythic to get all processes on this host that hooks into Mythic's process browser.
    This returns an async iterator, which can be used as:
        async for item in stream_processes(...data):
            print(item) <--- item will always be a dictionary based on the data you're getting back
    The default set of attributes returned in the dictionary can be found at graphql_queries.mythictree_fragment.
    """
    host_search = host
    if host_search is None:
        host_search = "%_%"
    else:
        host_search = f"%{host_search}%"
    process_query = f"""
    subscription getAllProcessesOnHost($host: String!, $batch_size: Int!, $now: timestamp!){{
        mythictree_stream(batch_size: $batch_size, where: {{host: {{_ilike: $host}}, tree_type: {{_eq: "process"}}}}, cursor: {{initial_value: {{timestamp: $now}}}}){{
            {custom_return_attributes if custom_return_attributes is not None else '...mythictree_fragment'}
        }}
    }}
    {graphql_queries.mythictree_fragment if custom_return_attributes is None else ''}
    """
    try:
        async for output in mythic_utilities.graphql_subscription(
                mythic=mythic, query=process_query,
                variables={"host": host_search, "batch_size": batch_size, "now": str(datetime.utcnow())},
                timeout=timeout
        ):
            yield output["mythictree_stream"]
    except asyncio.TimeoutError:
        mythic.logger.warning("Timeout reached in timeout_generator")
        return
    except StopAsyncIteration:
        return
    except Exception as e:
        raise e


async def get_all_processes(
        mythic: mythic_classes.Mythic,
        host: str = None,
        custom_return_attributes: str = None,
        batch_size: int = 100
) -> AsyncGenerator:
    """
    Execute a query against Mythic to get all processes on this host that hooks into Mythic's process browser.
    This returns an async iterator, which can be used as:
        async for item in get_processes(...data):
            print(item) <--- item will always be a dictionary based on the data you're getting back
    The default set of attributes returned in the dictionary can be found at graphql_queries.mythictree_fragment.
    If you want to use your own `custom_return_attributes` string to identify what information you want back, you have to include the `id` field, everything else is optional.
    """
    host_search = host
    if host_search is None:
        host_search = "%_%"
    else:
        host_search = f"%{host_search}%"
    process_query = f"""
    query getAllProcessesOnHost($host: String!, $batch_size: Int!, $offset: Int!){{
        mythictree(limit: $batch_size, offset: $offset, where: {{host: {{_ilike: $host}}, tree_type: {{_eq: "process"}}}}){{
            {custom_return_attributes if custom_return_attributes is not None else '...mythictree_fragment'}
        }}
    }}
    {graphql_queries.mythictree_fragment if custom_return_attributes is None else ''}
    """
    offset = 0
    while True:
        output = await mythic_utilities.graphql_post(
            mythic=mythic, query=process_query,
            variables={"host": host_search, "batch_size": batch_size, "offset": offset}
        )
        if len(output["mythictree"]) > 0:
            yield output["mythictree"]
            offset += len(output["mythictree"])
        else:
            break


async def subscribe_all_processes(
        mythic: mythic_classes.Mythic,
        host: str = None,
        custom_return_attributes: str = None,
        batch_size: int = 100,
        timeout: int = None
) -> AsyncGenerator:
    async for t in get_all_processes(mythic=mythic, host=host,
                                     custom_return_attributes=custom_return_attributes,
                                     batch_size=batch_size):
        yield t
    try:
        async for t in subscribe_new_processes(mythic=mythic, host=host,
                                               custom_return_attributes=custom_return_attributes,
                                               batch_size=batch_size,
                                               timeout=timeout):
            yield t
    except asyncio.TimeoutError:
        mythic.logger.warning("Timeout reached in timeout_generator")
        return
    except StopAsyncIteration:
        return
    except Exception as e:
        raise e


# ####### Credential Functions #############
async def create_credential(mythic: mythic_classes.Mythic,
                            credential: str,
                            account: str = "",
                            realm: str = "",
                            comment: str = "",
                            credential_type: str = "") -> dict:
    createCredentialMutation = """
    mutation createCredential($comment: String!, $account: String!, $realm: String!, $credential_type: String!, $credential: String!) {
        createCredential(account: $account, credential: $credential, comment: $comment, realm: $realm, credential_type: $credential_type) {
            status
            error
            id
        }
    }
    """
    output = await mythic_utilities.graphql_post(
        mythic=mythic, query=createCredentialMutation, variables={
            "credential": credential,
            "account": account,
            "realm": realm,
            "comment": comment,
            "credential_type": credential_type
        }
    )
    return output["createCredential"]


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
        mythictree(distinct_on: host) {
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
    for r in results["mythictree"]:
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


# ####### Event Feed functions ############
async def send_event_log_message(
        mythic: mythic_classes.Mythic,
        message: str,
        level: str = "info",
        source: str = "",
) -> dict:
    query = """
    mutation SendEventLog($message: String!, $level: String!, $source: String){
        createOperationEventLog(level: $level, message: $message, source: $source) {
            status
            error
        }
    }
    """
    return await mythic_utilities.graphql_post(mythic=mythic, query=query, variables={"level": level,
                                                                                      "message": message,
                                                                                      "source": source})


# ####### webhook ############
async def send_custom_webhook_message(
        mythic: mythic_classes.Mythic,
        webhook_data: dict,
        webhook_type: str = "new_custom",
) -> dict:
    query = """
    mutation sendMyExternalWebhook($webhook_type: String!, $webhook_data: jsonb!){
        sendExternalWebhook(webhook_type: $webhook_type, webhook_data: $webhook_data) {
            status
            error
        }
    }
    """

    return await mythic_utilities.graphql_post(mythic=mythic, query=query, variables={"webhook_data": webhook_data,
                                                                                      "webhook_type": webhook_type})


# ####### C2 Functions #############

async def start_stop_c2_profile(
        mythic: mythic_classes.Mythic,
        c2_profile_name: str,
        action: str = "start"
):
    query = """
    query getC2IdFromName($c2_name: String!) {
      c2profile(where: {name: {_eq: $c2_name}}){
        id
      }
    }
    """
    resp = await mythic_utilities.graphql_post(mythic=mythic, query=query, variables={
        "c2_name": c2_profile_name,
    })
    if len(resp["c2profile"]) == 0:
        raise Exception(f"Failed to find c2 profile {c2_profile_name}")
    start_stop = """
    mutation startStopC2Profile($id: Int!, $action: String!){
        startStopProfile(id: $id, action: $action){
            status
            error
            output
        }
    }
    """
    resp = await mythic_utilities.graphql_post(mythic=mythic, query=start_stop, variables={
        "id": resp["c2profile"][0]["id"], "action": action,
    })
    return resp["startStopProfile"]


async def create_saved_c2_instance(
        mythic: mythic_classes.Mythic,
        instance_name: str,
        c2_profile_name: str,
        c2_parameters: dict
):
    query = """
    query getC2IdFromName($c2_name: String!) {
      c2profile(where: {name: {_eq: $c2_name}}){
        id
      }
    }
    """
    resp = await mythic_utilities.graphql_post(mythic=mythic, query=query, variables={
        "c2_name": c2_profile_name,
    })
    if len(resp["c2profile"]) == 0:
        raise Exception(f"Failed to find c2 profile {c2_profile_name}")
    mutation = """
    mutation createNewC2Instance($instance_name: String!, $c2_instance: String!, $c2profile_id: Int!){
      create_c2_instance(c2_instance: $c2_instance, instance_name: $instance_name, c2profile_id: $c2profile_id){
        status
        error
      }
    }
    """
    resp = await mythic_utilities.graphql_post(mythic=mythic, query=mutation, variables={
        "instance_name": instance_name, "c2profile_id": resp["c2profile"][0]["id"],
        "c2_instance": json.dumps(c2_parameters)
    })
    return resp["create_c2_instance"]


# ####### Tag Functions ############


async def create_tag_type(
        mythic: mythic_classes.Mythic,
        color: str = "#71a0d0",
        description: str = "",
        name: str = "test",
) -> dict:
    query = """
    mutation createNewTagType($color: String!, $description: String!, $name: String!) {
      insert_tagtype_one(object: {color: $color, description: $description, name: $name}, on_conflict: {constraint: tagtype_name_operation_id_key, update_columns: color}) {
        id
      }
    }
    """
    resp = await mythic_utilities.graphql_post(mythic=mythic, query=query, variables={
        "color": color, "description": description, "name": name
    })
    return resp["insert_tagtype_one"]


async def update_tag_type(
        mythic: mythic_classes.Mythic,
        tag_type_id: int,
        color: str = "#71a0d0",
        description: str = "",
        name: str = "test",
) -> dict:
    query = """
    mutation createNewTagType($id: Int!, $color: String!, $description: String!, $name: String!) {
      update_tagtype_by_pk(pk_columns: {id: $id}, _set: {color: $color, description: $description, name: $name}) {
        id
      }
    }
    """
    resp = await mythic_utilities.graphql_post(mythic=mythic, query=query, variables={
        "color": color, "description": description, "name": name, "id": tag_type_id
    })
    return resp["update_tagtype_by_pk"]


async def delete_tag_type(mythic: mythic_classes.Mythic, tag_type_id: int) -> dict:
    query = """
    mutation createNewTagType($id: Int!) {
      deleteTagtype(id: $id) {
        error
        status
        tagtype_id
      }
    }
    """
    resp = await mythic_utilities.graphql_post(mythic=mythic, query=query, variables={
        "id": tag_type_id
    })
    return resp["deleteTagtype"]


async def get_tag_type(mythic: mythic_classes.Mythic, name: str) -> dict:
    query = """
    query getTagType($name: String!) {
      tagtype(where: {name: {_eq: $name}}) {
        id
        name
        color
        description
      }
    }
    """
    resp = await mythic_utilities.graphql_post(mythic=mythic, query=query, variables={
        "name": name
    })
    return resp["tagtype"]


async def get_all_tag_types(mythic: mythic_classes.Mythic) -> dict:
    query = """
    query getTagType {
      tagtype {
        id
        name
        color
        description
      }
    }
    """
    return await mythic_utilities.graphql_post(mythic=mythic, query=query)


async def create_tag(mythic: mythic_classes.Mythic,
                     tag_type_id: int,
                     source: str = "",
                     url: str = "",
                     data: str = "",
                     credential_ids: List[int] = None,
                     filemeta_ids: List[int] = None,
                     keylog_ids: List[int] = None,
                     mythictree_ids: List[int] = None,
                     response_ids: List[int] = None,
                     task_ids: List[int] = None,
                     taskartifact_ids: List[int] = None) -> List[dict]:
    # this will create a new instance of a tag for every id listed in every group
    def get_mutation(target_object: str) -> str:
        return f"""
            mutation createTag($tagtype_id: Int!, $source: String!, $url: String!, $data: jsonb!, ${target_object}: Int!) {{
              insert_tag_one(object: {{data: $data, source: $source, tagtype_id: $tagtype_id, url: $url, {target_object}:${target_object}}}) {{
                id
                {target_object}
              }}
            }}
            """

    output = []
    if credential_ids is not None:
        for target_id in credential_ids:
            resp = await mythic_utilities.graphql_post(mythic=mythic, query=get_mutation("credential_id"), variables={
                "tagtype_id": tag_type_id, "source": source, "url": url, "data": data, "credential_id": target_id
            })
            output.append(resp)
    if filemeta_ids is not None:
        for target_id in filemeta_ids:
            resp = await mythic_utilities.graphql_post(mythic=mythic, query=get_mutation("filemeta_id"), variables={
                "tagtype_id": tag_type_id, "source": source, "url": url, "data": data, "filemeta_id": target_id
            })
            output.append(resp)
    if keylog_ids is not None:
        for target_id in keylog_ids:
            resp = await mythic_utilities.graphql_post(mythic=mythic, query=get_mutation("keylog_id"), variables={
                "tagtype_id": tag_type_id, "source": source, "url": url, "data": data, "keylog_id": target_id
            })
            output.append(resp)
    if mythictree_ids is not None:
        for target_id in mythictree_ids:
            resp = await mythic_utilities.graphql_post(mythic=mythic, query=get_mutation("mythictree_id"), variables={
                "tagtype_id": tag_type_id, "source": source, "url": url, "data": data, "mythictree_id": target_id
            })
            output.append(resp)
    if response_ids is not None:
        for target_id in response_ids:
            resp = await mythic_utilities.graphql_post(mythic=mythic, query=get_mutation("response_id"), variables={
                "tagtype_id": tag_type_id, "source": source, "url": url, "data": data, "response_id": target_id
            })
            output.append(resp)
    if task_ids is not None:
        for target_id in task_ids:
            resp = await mythic_utilities.graphql_post(mythic=mythic, query=get_mutation("task_id"), variables={
                "tagtype_id": tag_type_id, "source": source, "url": url, "data": data, "task_id": target_id
            })
            output.append(resp)
    if taskartifact_ids is not None:
        for target_id in taskartifact_ids:
            resp = await mythic_utilities.graphql_post(mythic=mythic, query=get_mutation("taskartifact_id"), variables={
                "tagtype_id": tag_type_id, "source": source, "url": url, "data": data, "taskartifact_id": target_id
            })
            output.append(resp)
    return output


async def create_tag_for_multiple_objects(mythic: mythic_classes.Mythic,
                                          tag_type_id: int,
                                          source: str = "",
                                          url: str = "",
                                          data: str = "",
                                          credential_id: int = None,
                                          filemeta_id: int = None,
                                          keylog_id: int = None,
                                          mythictree_id: int = None,
                                          response_id: int = None,
                                          task_id: int = None,
                                          taskartifact_id: int = None) -> dict:
    # This will create a single tag instance and associate it with multiple objects within Mythic
    add_tag_query = f"""
        mutation createTag($tagtype_id: Int!, $source: String!, $url: String!, $data: jsonb!, $credential_id: Int, $filemeta_id: Int, $keylog_id: Int, $mythictree_id: Int, $response_id: Int, $task_id: Int, $taskartifact_id: Int) {{
          insert_tag_one(object: {{data: $data, source: $source, tagtype_id: $tagtype_id, url: $url, credential_id: $credential_id, filemeta_id: $filemeta_id, keylog_id: $keylog_id, mythictree_id: $mythictree_id, response_id:$response_id, task_id:$task_id, taskartifact_id: $taskartifact_id }}) {{
            id
          }}
        }}
        """
    return await mythic_utilities.graphql_post(mythic=mythic, query=add_tag_query, variables={
        "tagtype_id": tag_type_id, "source": source, "url": url, "data": data, "credential_id": credential_id,
        "filemeta_id": filemeta_id, "keylog_id": keylog_id, "mythictree_id": mythictree_id, "response_id": response_id,
        "task_id": task_id, "taskartifact_id": taskartifact_id
    })


async def remove_tag(mythic: mythic_classes.Mythic, tag_id: int) -> dict:
    # This deletes a tag from Mythic by its tag id (this doesn't remove the type of tag, just a single instance of a tag)
    remove_tag_query = f"""
    mutation removeTag($tag_id: Int!) {{
        delete_tag_by_pk(id: $tag_id) {{
        id
        }}
    }}
    """
    return await mythic_utilities.graphql_post(mythic=mythic, query=remove_tag_query, variables={
        "tag_id": tag_id,
    })


### INTROSPECTION QUERIES ###
async def get_command_parameter_options(mythic: mythic_classes.Mythic, command_name: str, payload_type_name: str) -> str:
    command_parameter_query = """
    query filenameFileMetaUploadQuery($command_name: String!, $payload_type_name: String!) {
        commandparameters(where: {command: {cmd: {_eq: $command_name}, payloadtype: {name: {_eq: $payload_type_name}}}}) {
            choice_filter_by_command_attributes
            choices
            choices_are_all_commands
            choices_are_loaded_commands
            cli_name
            default_value
            dynamic_query_function
            name
            parameter_group_name
            required
            supported_agent_build_parameters
            supported_agents
            type
            ui_position
        }
        command(where: {cmd: {_eq: $command_name}, payloadtype: {name: {_eq: $payload_type_name}}}) {
            id
        }
    }
"""
    parameters = await mythic_utilities.graphql_post(mythic=mythic, query=command_parameter_query, variables={
        "command_name": command_name,
        "payload_type_name": payload_type_name
    })
    if len(parameters['command']) == 0:
        return f"[-] Failed to find that command"
    # get all the parameters
    parameters = parameters["commandparameters"]
    if len(parameters) == 0:
        return f"[*] No parameters specified\n\tCalled via: {command_name}"
    # get all the parameter groups in a set
    groups = {x['parameter_group_name'] for x in parameters}
    output = f"There are {len(groups)} ways to call this function:\n"
    for group in groups:
        output += f"Parameter Group: {group}\n"
        group_parameters = [x for x in parameters if x["parameter_group_name"] == group]
        example_call = {}
        for param in group_parameters:
            output += f"\tScripting Name: {param['cli_name']}\n"
            output += f"\t\tRequired: {param['required']}\n"
            output += f"\t\tParameter Type: {param['type']}\n"
            if param['type'] == "String":
                example_call[param['cli_name']] = param['default_value']
            elif param['type'] == "ChooseOne" or param['type'] == "ChooseMultiple":
                if param['dynamic_query_function'] != "":
                    output += f"\t\t\tA function will be dynamically called to offer options for this command when the UI modal is displayed.\n"
                if param['choices_are_all_commands']:
                    output += f"\t\t\tThe choices for this are all commands for the agent (those built in and those not)\n"
                if param["choices_are_loaded_commands"]:
                    output += f"\t\t\tThe choices for this are all loaded commands for the callback\n"
                if param["choice_filter_by_command_attributes"]:
                    output += f"\t\t\tThe command options are further limited by certain attributes: {param['choices_filter_by_command_attributes']}\n"
                try:
                    if len(param['default_value']) > 0:
                        parsed_default = json.loads(param['default_value'])
                        example_call[param['cli_name']] = parsed_default
                    else:
                        example_call[param['cli_name']] = "" if param['type'] == 'ChooseOne' else []
                except Exception:
                    example_call[param['cli_name']] = "" if param['type'] == 'ChooseOne' else []
                if len(param['choices']) > 0:
                    output += f"\t\t\tThe available choices are: {param['choices']}\n"
            elif param['type'] == "File":
                output += "\t\t\tThe user will upload a file through the UI and get back a UUID, that UUID is supplied here.\n"
                example_call[param['cli_name']] = "00000000-0000-0000-0000-000000000000"
            elif param['type'] == "Boolean":
                example_call[param['cli_name']] = False if param['default_value'] == "false" else True
            elif param['type'] == "Number":
                example_call[param['cli_name']] = param['default_value']
            elif param['type'] == "Array":
                example_call[param['cli_name']] = param['default_value']
            elif param['type'] == "CredentialJson":
                output += f"\t\t\tThis expects a dictionary of credential material\n"
                example_call[param['cli_name']] = {
                    "realm": "some realm",
                    "credential": "the actual credential",
                    "account": "some user",
                    "type": "plaintext, hash, ticket, etc",
                }
            elif param['type'] == "PayloadList":
                output += "\t\t\tThe UI will show a list of available payloads to select from and the resulting payload UUID will be supplied here.\n"
                if len(param['supported_agents']) > 0:
                    output += f"\t\t\tThis is limited to the following agents: {param['supported_agents']}\n"
                if len(param['supported_agent_build_parameters']) > 0:
                    output += f"\t\t\tThe available agents are further restricted by build parameters: {param['supported_agent_build_parameters']}\n"
                example_call[param['cli_name']] = "00000000-0000-0000-0000-000000000000"
            elif param['type'] == "AgentConnect":
                output += f"\t\t\tThis will populate the UI with a modal to select an existing callback or payload to connect to that has a P2P C2 Profile.\n"
                output += f"\t\t\tThis will have either 'agent_uuid' or 'callback_uuid' in it depending if you're linking to an existing callback or new payload.\n"
                output += f"\t\t\tThis value consists of the host, uuid, and c2 profile information for the agent to make a connection.\n"
                example_call[param['cli_name']] = {
                    "host": "HOSTNAME of remote host",
                    "agent_uuid": "00000000-0000-0000-0000-000000000000",
                    "c2_profile": {
                        "name": "poseidon_tcp",
                        "parameters": {
                            "AESPSK": {"crypto_type": "aes256_hmac",
                                       "enc_key": "base64 blob",
                                       "dec_key": "base64 blob"},
                            "port": "8085",
                            "killdate": "2024-09-06",
                            "encrypted_exchange_check": "true"
                        }
                    }
                }
            elif param['type'] == "LinkInfo":
                output += f"\t\t\tThis will populate the UI with a modal to select an existing P2P connection for this callback.\n"
                output += f"\t\t\tThis value consists of the host, callback uuid, and c2 profile information for the agent to make a connection.\n"
                example_call[param['cli_name']] = {
                    "host": "HOSTNAME of remote host",
                    "callback_uuid": "00000000-0000-0000-0000-000000000000",
                    "c2_profile": {
                        "name": "poseidon_tcp",
                        "parameters": {
                            "AESPSK": {"crypto_type": "aes256_hmac",
                                       "enc_key": "base64 blob",
                                       "dec_key": "base64 blob"},
                            "port": "8085",
                            "killdate": "2024-09-06",
                            "encrypted_exchange_check": "true"
                        }
                    }
                }
            elif param['type'] == "TypedArray":
                output += f"\t\t\tThis is a nested array of data where the first part is a 'type' and the second part is the 'value'"
                output += f"\t\t\tAvailable type choices are: {param['choices']}"
                if len(param['choices']) > 0:
                    example_call[param['cli_name']] = [[param['choices'][0], '']]
                else:
                    example_call[param['cli_name']] = []
        output += f"\tAn example call would look like:\n{json.dumps(example_call, indent=2, sort_keys=True)}\n"
    return output
