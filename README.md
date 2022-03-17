# Mythic Scripting Interface

The `mythic` package creates a way to programmatically interact and control a Mythic instance. Mythic is a Command and Control (C2) framework for Red Teaming. The code is on GitHub (https://github.com/its-a-feature/Mythic) and the Mythic project's documentation is on GitBooks (https://docs.mythic-c2.net).

## Installation

You can install the mythic scripting interface from PyPI:

```
pip install mythic
```

## How to use

Version 0.0.13 of the `mythic` package supports version 2.1.* of the Mythic project.

Version 0.0.15 of the `mythic` package supports version 2.2.1 of the Mythic project.

Version 0.0.20 of the `mythic` package supports version 2.2.6 of the Mythic project (reports as version "3").

Version 0.0.21-25 of the `mythic` package supports version 2.2.8+ of the Mythic project (reports as version "3").

Version 0.0.26 of the `mythic` package supports version 2.3+ of the Mythic project (reports as version "3"). This version uses the new GraphQL interfaces.


```
from mythic import mythic_rest
mythic = mythic_rest.Mythic(
    username="mythic_admin",
    password="mythic_password",
    server_ip="192.168.205.151",
    server_port="7443",
    ssl=True,
    global_timeout=-1,
)
await mythic.login()
```

## New GraphQL Interface

In addition to thte old RESTful interfaces and websockets, this version includes a beta set of the GraphQL features. 

```
import asyncio
import logging
from mythic import mythic, mythic_classes


async def main():
    mythic_instance = await mythic.login(
        username="mythic_admin",
        password="mythic_password",
        server_ip="127.0.0.1",
        server_port=7443,
        logging_level=logging.WARNING,
    )
    print(mythic_instance)
        # ################ Execute custom GraphQL Query ################
    custom_query = """
    query GetAPITokens($id: Int!) {
        apitokens(where: {id: {_eq: $id}}) {
            token_value
            active
            id
        }
    }
    """
    result = await mythic.execute_custom_query(
        mythic=mythic_instance, query=custom_query, variables={"id": 30}
    )
    print(result)

    # ################ Registering a file with Mythic for use in Tasking ################

    """ resp = await mythic.register_file(
       mythic=mythic_instance, filename="test.txt", contents=b"this is a test"
    )
    print(f"registered file UUID: {resp}")
    status = await mythic.issue_task(
       mythic=mythic_instance,
       command_name="upload",
       parameters={"remote_path": "test.js", "new-file": resp},
       callback_id=20,
    )
    print(f"Issued a task: {status}") """

    # ################ Issue Task and Wait for completion or timeout ################
    """
    try:
        status = await mythic.issue_task(
            mythic=mythic_instance,
            command_name="shell",
            parameters={"command": "whoami"},
            callback_id=0,
            timeout=20,
            return_on_status=mythic_classes.MythicStatus.Completed,
        )
        print(f"Issued a task: {status}")
    except Exception as e:
        print(f"Got exception trying to issue task: {str(e)}")
    """

    # ################ Issue Task against all active callbacks ################

    """status = await mythic.issue_task_all_active_callbacks(
        mythic=mythic_instance, command_name="shell", parameters="whoami"
    )
    print(f"Got the following list back: {status}")"""

    # ################ Issue Task and wait for output ################

    """ status = await mythic.issue_task_and_waitfor_task_output(
        mythic=mythic_instance,
        command_name="shell",
        parameters="whoami",
        callback_id=156,
        timeout=60,
        return_on_status=mythic_classes.MythicStatus.Completed,
    )
    print(f"Got the following output: {status}\n")

    task = await mythic.issue_task(
        mythic=mythic_instance,
        command_name="shell",
        parameters="whoami",
        callback_id=156,
        timeout=60,
        return_on_status=mythic_classes.MythicStatus.Completed,
    )
    output = await mythic.waitfor_for_task_output(
        mythic=mythic_instance, task_id=task["id"], timeout=60
    )
    print(f"Got the following output the 2nd time: {output}\n") """

    # ################ Wait for Multiple Subscriptions ################
    """await asyncio.gather(
        new_callbacks(mythic_instance=mythic_instance),
        new_tasks(mythic_instance=mythic_instance),
        all_tasks(mythic_instance=mythic_instance),
        all_tasks_by_callback(mythic_instance=mythic_instance, callback_id=156),
    )"""

    # ################ Adding MITRE ATT&CK Techniques To Task ################

    """ await mythic.add_mitre_attack_to_task(
        mythic=mythic_instance, task_id=1, mitre_attack_numbers=["T1033"]
    ) """

    # ################ Create a Payload ################
    """ await mythic.create_payload(
        mythic=mythic_instance,
        payload_type_name="poseidon",
        filename="test.bin",
        operating_system="macOS",
        commands=[],
        c2_profiles=[
            {
                "c2_profile": "http",
                "c2_profile_parameters": {
                    "callback_host": "http://192.168.53.139",
                    "callback_port": "80",
                },
            }
        ],
        build_parameters=[{"name": "mode", "value": "default"}],
        return_on_complete=True,
    )
    await mythic.create_payload(
        mythic=mythic_instance,
        payload_type_name="apfell",
        filename="apfell_test.js",
        operating_system="macOS",
        c2_profiles=[
            {
                "c2_profile": "http",
                "c2_profile_parameters": {
                    "callback_host": "http://192.168.53.139",
                    "callback_port": "80",
                },
            }
        ],
    ) """

    # ################ Add User to Operation ################
    """ try:
        await mythic.add_operator_to_operation(
            mythic=mythic_instance,
            operation_name="Operation Chimera",
            operator_username="bob",
        )
    except Exception as e:
        print(f"Got exception adding user to operation: {e}") """

    # ################ Update Operator View Mode ################

    """ try:
        await mythic.update_operator_in_operation(
            mythic=mythic_instance,
            operation_name="Operation Chimera",
            operator_username="bob",
            view_mode="spectator",
        )
    except Exception as e:
        print(f"Got exception updating user in operation: {e}") """

    # ################ Update Operation ################

    """ try:
        await mythic.update_operation(
            mythic=mythic_instance,
            operation_name="Operation Chimera",
            webhook_message="test",
            lead_operator_username="bob",
        )
    except Exception as e:
        print(f"Got exception updating operation: {e}") """

    # ################ Remove User from Operation ################
    """ try:
        await mythic.remove_operator_from_operation(
            mythic=mythic_instance,
            operation_name="Operation Chimera",
            operator_username="bob",
        )
    except Exception as e:
        print(f"Got exception removing user from operation: {e}") """

    while True:
        await asyncio.sleep(1)

async def new_callbacks(mythic_instance: mythic_classes.Mythic):
    async for callback in mythic.subscribe_new_callbacks(mythic=mythic_instance):
        print(f"got new callback:\n{callback}")


async def new_tasks(mythic_instance: mythic_classes.Mythic):
    async for task in mythic.subscribe_new_tasks(mythic=mythic_instance, timeout=3):
        print(f"got new task: {task}")


async def all_tasks(mythic_instance: mythic_classes.Mythic):
    async for task in mythic.subscribe_all_tasks(mythic=mythic_instance):
        print(f"got new task: {task}")


async def all_tasks_by_callback(mythic_instance: mythic_classes.Mythic, callback_id: int):
    async for task in mythic.subscribe_all_tasks(
        mythic=mythic_instance, callback_id=callback_id
    ):
        print(f"got new task by callback {callback_id}: {task}")


async def all_filebrowser(mythic_instance: mythic_classes.Mythic):
    async for f in mythic.subscribe_all_filebrowser(mythic=mythic_instance):
        print(f"got all filebrowser obj: {f}")


asyncio.run(main())
```

# Information

The Mythic documentation has a whole section on scripting examples (https://docs.mythic-c2.net/scripting) that are useful for how to leverage this package. The `mythic` package leverages async HTTP requests and WebSocket connections, so it's important to make sure your codebase is running asynchronously. An example stub to help with this is on the Mythic documentation scripting page.


## Testing

To run unit testing:

```
pip3 install pytest
make all_tests
```