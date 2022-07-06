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

Version 0.0.26 of the `mythic` package supports version 2.3+ of the Mythic project (reports as version "3").

Version 0.0.29-0.0.36 of the `mythic` package supports version 2.3+ of the Mythic project utilizing the new GraphQL endpoints and reports as version "3".
This will be the last version that supports the old mythic_rest interface. Starting with version 0.1.0, the `mythic` PyPi package will only support the new GraphQL interface and will report as version "4".

## New GraphQL Interface

In addition to thte old RESTful interfaces and websockets, this version includes a beta set of the GraphQL features. 

```
import asyncio
from time import time

from mythic import mythic, mythic_classes


async def main():
    mythic_instance = await mythic.login(
        username="mythic_admin",
        password="mythic_password",
        server_ip="192.168.53.139",
        server_port=7443,
        timeout=-1
    )

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

    # ################ Get all Payloads #############
    """payloads = await mythic.get_all_payloads(mythic=mythic_instance)
    print(payloads)"""

    # ############### Download a Payload ############
    """payload_bytes = await mythic.download_payload(
        mythic=mythic_instance, payload_uuid="04467b89-dc46-42d1-b7c4-03aca84b194c"
    )
    print(payload_bytes)"""

    # ############## Update a callback #############
    """await mythic.update_callback(
        mythic=mythic_instance,
        description="test set",
        locked=True,
        callback_id=156,
        active=False,
    )"""

    # ########### Get latest Processes #######
    """processes = await mythic.get_latest_processes_on_host(
        mythic=mythic_instance, host="SPOOKY.LOCAL"
    )
    print(processes)"""

    # ########## Search Files and Add Comments ###########
    """ files = await mythic.search_files(mythic=mythic_instance, filename="apfe")
    for f in files:
        print(f["filename_text"])
        await mythic.update_file_comment(
            mythic=mythic_instance, file_uuid=f["agent_file_id"], comment="auto updated"
        ) """

    # ########## Get Compromised Hosts, Users, IP Addresses ###########
    hosts = await mythic.get_unique_compromised_hosts(mythic=mythic_instance)
    print(hosts)
    users = await mythic.get_unique_compromised_accounts(mythic=mythic_instance)
    print(users)
    ips = await mythic.get_unique_compromised_ips(mythic=mythic_instance)
    print(ips)


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

### Custom Attributes
To supply your own custom attributes to many of the functions, you need to have each one on their own line like follows:
```
custom_attributes = """
host
user
payload {
    id
    uuid
}
"""
results = await mythic.get_all_callbacks(
    mythic=mythic_instance, custom_return_attributes=custom_attributes
)
```

# Information

The Mythic documentation has a whole section on scripting examples (https://docs.mythic-c2.net/scripting) that are useful for how to leverage this package. The `mythic` package leverages async HTTP requests and WebSocket connections, so it's important to make sure your codebase is running asynchronously. An example stub to help with this is on the Mythic documentation scripting page.


## Testing

To run unit testing:

```
pip3 install pytest, gql[aiohttp,websockets], aiohttp, asyncio
make all_tests
```