import asyncio
import base64
import json
import sys
from time import time
from typing import Dict, List, Union

import aiohttp


async def json_print(thing):
    print(json.dumps(thing, indent=2, default=lambda o: o.to_json()))


async def obj_to_json(thing):
    return json.loads(json.dumps(thing, default=lambda o: o.to_json()))


class APIToken:
    def __init__(
        self,
        token_type: str = None,
        token_value: str = None,
        creation_time: str = None,
        active: bool = None,
        id: int = None,
        operator: Union["Operator", str] = None,
        **kwargs,
    ):
        self.token_type = token_type
        self.token_value = token_value
        self.creation_time = creation_time
        self.active = active
        self.id = id
        if isinstance(operator, Operator) or operator is None:
            self.operator = operator
        else:
            self.operator = Operator(username=operator)
        vars(self).update(kwargs)

    def to_json(self):
        r = {}
        for k in vars(self):
            if getattr(self, k) is not None:
                try:
                    if k[0] == "_":
                        r[k[1:]] = getattr(self, k)
                    else:
                        r[k] = getattr(self, k)
                except:
                    if k[0] == "_":
                        r[k[1:]] = json.dumps(
                            getattr(self, k), default=lambda o: o.to_json()
                        )
                    else:
                        r[k] = json.dumps(getattr(self, k), default=lambda o: o.to_json())
        return r

    def __str__(self):
        return json.dumps(self.to_json())


class Operation:
    def __init__(
        self,
        name: str = None,
        admin: Union["Operator", str] = None,
        complete: bool = None,
        webhook: str = None,
        id: int = None,
        channel: str = None,
        display_name: str = None,
        icon_emoji: str = None,
        icon_url: str = None,
        members: List[Union["Operator", Dict[str, str], str]] = None,
        webhook_message: str = None,
        **kwargs,
    ):
        if isinstance(admin, Operator) or admin is None:
            self.admin = admin
        else:
            self.admin = Operator(username=admin)
        self.complete = complete
        self.webhook = webhook
        self.channel = channel
        self.display_name = display_name
        self.icon_emoji = icon_emoji
        self.icon_url = icon_url
        self.webhook_message = webhook_message
        self.id = id
        self.name = name
        if members is not None:
            if isinstance(members, list):
                self.members = [
                    Operator(username=x)
                    if isinstance(x, str)
                    else Operator(**x)
                    if isinstance(x, Dict)
                    else x
                    for x in members
                ]
            else:
                raise ValueError("members must be a list")
        else:
            self.members = members
        vars(self).update(kwargs)

    def to_json(self):
        r = {}
        for k in vars(self):
            if getattr(self, k) is not None:
                try:
                    if k[0] == "_":
                        r[k[1:]] = getattr(self, k)
                    else:
                        r[k] = getattr(self, k)
                except:
                    if k[0] == "_":
                        r[k[1:]] = json.dumps(
                            getattr(self, k), default=lambda o: o.to_json()
                        )
                    else:
                        r[k] = json.dumps(getattr(self, k), default=lambda o: o.to_json())
        return r

    def __str__(self):
        return json.dumps(self.to_json())


class Operator:
    def __init__(
        self,
        username: str = None,
        password: str = None,
        admin: bool = None,
        creation_time: str = None,
        last_login: str = None,
        active: bool = None,
        current_operation: Union[Operation, str] = None,
        current_operation_id: int = None,
        ui_config: str = None,
        id: int = None,
        view_utc_time: bool = None,
        deleted: bool = None,
        view_mode: str = None,
        base_disabled_commands: str = None,
        failed_login_count: int = None,
        last_failed_login_timestamp: str = None,
        **kwargs,
    ):
        self.username = username
        self.admin = admin
        self.creation_time = creation_time
        self.last_login = last_login
        self.active = active
        if isinstance(current_operation, Operation) or current_operation is None:
            self.current_operation = current_operation
        else:
            self.current_operation = Operation(name=current_operation)
        self.ui_config = ui_config
        self.id = id
        self.password = password
        self.view_utc_time = view_utc_time
        self.deleted = deleted
        self.failed_login_count = failed_login_count
        self.last_failed_login_timestamp = last_failed_login_timestamp
        if self.current_operation is not None:
            self.current_operation.id = current_operation_id
        if view_mode in ["spectator", "operator", "developer", "lead", None]:
            self.view_mode = view_mode
        else:
            raise Exception("Bad value for view_mode")
        self.base_disabled_commands = base_disabled_commands
        vars(self).update(kwargs)

    def to_json(self):
        r = {}
        for k in vars(self):
            if getattr(self, k) is not None:
                try:
                    if k[0] == "_":
                        r[k[1:]] = getattr(self, k)
                    else:
                        r[k] = getattr(self, k)
                except:
                    if k[0] == "_":
                        r[k[1:]] = json.dumps(
                            getattr(self, k), default=lambda o: o.to_json()
                        )
                    else:
                        r[k] = json.dumps(getattr(self, k), default=lambda o: o.to_json())
        return r

    def __str__(self):
        return json.dumps(self.to_json())


class PayloadType:
    def __init__(
        self,
        ptype: str = None,
        mythic_encrypts: bool = None,
        creation_time: str = None,
        file_extension: str = None,
        wrapper: bool = None,
        wrapped: Union["PayloadType", str] = None,
        supported_os: str = None,
        last_heartbeat: str = None,
        container_running: bool = None,
        service: str = None,
        author: str = None,
        note: str = None,
        supports_dynamic_loading: bool = None,
        deleted: bool = None,
        build_parameters: List[Dict] = None,
        id: int = None,
        c2_profiles: List[Union["C2Profile", Dict]] = None,
        commands: List[Union["Command", str, Dict]] = None,
        translation_container: dict = None,
        **kwargs,
    ):
        self.ptype = ptype
        self.mythic_encrypts = mythic_encrypts
        self.translation_container = translation_container
        self.creation_time = creation_time
        self.file_extension = file_extension
        self.wrapper = wrapper
        self.translation_container = translation_container
        if isinstance(wrapped, PayloadType) or wrapped is None:
            self.wrapped = wrapped
        else:
            self.wrapped_ = PayloadType(ptype=wrapped)
        self.supported_os = supported_os
        self.last_heartbeat = last_heartbeat
        self.container_running = container_running
        self.service = service
        self.id = id
        self.author = author
        self.note = note
        self.build_parameters = build_parameters
        self.supports_dynamic_loading = supports_dynamic_loading
        self.deleted = deleted
        if isinstance(c2_profiles, List):
            self.c2_profiles = [
                C2Profile(**x) if isinstance(x, Dict) else x for x in c2_profiles
            ]
        else:
            self.c2_profiles = c2_profiles
        if isinstance(commands, List):
            self.commands = [
                Command(**x)
                if isinstance(x, Dict)
                else Command(cmd=x)
                if isinstance(x, str)
                else x
                for x in commands
            ]
        else:
            self.commands = commands
        vars(self).update(kwargs)

    def to_json(self):
        r = {}
        for k in vars(self):
            if getattr(self, k) is not None:
                try:
                    if k[0] == "_":
                        r[k[1:]] = getattr(self, k)
                    else:
                        r[k] = getattr(self, k)
                except:
                    if k[0] == "_":
                        r[k[1:]] = json.dumps(
                            getattr(self, k), default=lambda o: o.to_json()
                        )
                    else:
                        r[k] = json.dumps(getattr(self, k), default=lambda o: o.to_json())
        return r

    def __str__(self):
        return json.dumps(self.to_json())


class Command:
    def __init__(
        self,
        needs_admin: bool = None,
        help_cmd: str = None,
        description: str = None,
        cmd: str = None,
        payload_type: Union[PayloadType, str] = None,
        creation_time: str = None,
        version: int = None,
        supported_ui_features: str = None,
        attributes: str = None,
        opsec: dict = None,
        author: str = None,
        mythic_version: int = None,
        deleted: bool = None,
        id: int = None,
        params: List[Union["CommandParameters", Dict[str, str]]] = None,
        **kwargs,
    ):
        self.needs_admin = needs_admin
        self.help_cmd = help_cmd
        self.description = description
        self.cmd = cmd
        self.supported_ui_features = supported_ui_features
        if isinstance(payload_type, PayloadType) or payload_type is None:
            self.payload_type = payload_type
        else:
            self.payload_type = PayloadType(ptype=payload_type)
        self.creation_time = creation_time
        self.version = version
        self.attributes = attributes
        self.opsec = opsec
        self.author = author
        self.deleted = deleted
        self.mythic_version = mythic_version
        self.id = id
        if params is not None and params != []:
            if isinstance(params, list):
                self.params = [
                    CommandParameters(**x) if isinstance(x, Dict) else x for x in params
                ]
            else:
                raise ValueError("params must be a list")
        else:
            self.params = None
        vars(self).update(kwargs)

    def to_json(self):
        r = {}
        for k in vars(self):
            if getattr(self, k) is not None:
                try:
                    if k[0] == "_":
                        r[k[1:]] = getattr(self, k)
                    else:
                        r[k] = getattr(self, k)
                except:
                    if k[0] == "_":
                        r[k[1:]] = json.dumps(
                            getattr(self, k), default=lambda o: o.to_json()
                        )
                    else:
                        r[k] = json.dumps(getattr(self, k), default=lambda o: o.to_json())
        return r

    def __str__(self):
        return json.dumps(self.to_json())


class CommandParameters:
    def __init__(
        self,
        command: Union[Command, int] = None,  # database ID for the corresponding command
        cmd: str = None,  # cmd string the command refers to (like shell)
        payload_type: Union[PayloadType, str] = None,
        name: str = None,
        type: str = None,
        default_value: str = None,
        description: str = None,
        supported_agents: str = None,
        choices: Union[List[str], str] = None,
        supported_agent_build_parameters: str = None,
        choice_filter_by_command_attributes: str = None,
        choices_are_all_commands: bool = None,
        choices_are_loaded_commands: bool = None,
        required: bool = None,
        ui_position: int = None,
        id: int = None,
        **kwargs,
    ):
        if isinstance(command, Command) or command is None:
            self.command = command
        else:
            self.command = Command(id=command)
        self.cmd = cmd
        if isinstance(payload_type, PayloadType) or payload_type is None:
            self.payload_type = payload_type
        else:
            self.payload_type = PayloadType(ptype=payload_type)
        self.name = name
        self.type = type
        self.choice_filter_by_command_attributes = choice_filter_by_command_attributes
        self.supported_agent_build_parameters = supported_agent_build_parameters
        self.choices_are_all_commands = choices_are_all_commands
        self.choices_are_loaded_commands = choices_are_loaded_commands
        self.description = description
        self.supported_agents = supported_agents
        self.default_value = default_value
        self.ui_position = ui_position
        if isinstance(choices, List) or choices is None:
            self.choices = choices
        else:
            self.choices = choices.split("\n")
        self.required = required
        self.id = id
        vars(self).update(kwargs)

    def to_json(self):
        r = {}
        for k in vars(self):
            if getattr(self, k) is not None:
                try:
                    if k[0] == "_":
                        r[k[1:]] = getattr(self, k)
                    else:
                        r[k] = getattr(self, k)
                except:
                    if k[0] == "_":
                        r[k[1:]] = json.dumps(
                            getattr(self, k), default=lambda o: o.to_json()
                        )
                    else:
                        r[k] = json.dumps(getattr(self, k), default=lambda o: o.to_json())
        return r

    def __str__(self):
        return json.dumps(self.to_json())


class C2Profile:
    def __init__(
        self,
        name: str = None,
        description: str = None,
        creation_time: str = None,
        running: bool = None,
        last_heartbeat: str = None,
        container_running: bool = None,
        author: str = None,
        is_p2p: bool = None,
        is_server_routed: bool = None,
        deleted: bool = None,
        id: int = None,
        ptype: List[Union[PayloadType, str]] = None,
        parameters: Dict = None,
        **kwargs,
    ):  # list of payload types that support this c2 profile
        self.name = name
        self.description = description
        self.creation_time = creation_time
        self.running = running
        self.last_heartbeat = last_heartbeat
        self.container_running = container_running
        self.id = id
        self.author = author
        self.is_p2p = is_p2p
        self.is_server_routed = is_server_routed
        self.deleted = deleted
        if ptype is not None:
            if isinstance(ptype, list):
                self.ptype = [
                    PayloadType(ptype=x) if isinstance(x, str) else x for x in ptype
                ]
            else:
                raise ValueError("ptype must be a list")
        else:
            self.ptype = ptype
        self.parameters = parameters
        vars(self).update(kwargs)

    def to_json(self):
        r = {}
        for k in vars(self):
            if getattr(self, k) is not None:
                try:
                    if k[0] == "_":
                        r[k[1:]] = getattr(self, k)
                    else:
                        r[k] = getattr(self, k)
                except:
                    if k[0] == "_":
                        r[k[1:]] = json.dumps(
                            getattr(self, k), default=lambda o: o.to_json()
                        )
                    else:
                        r[k] = json.dumps(getattr(self, k), default=lambda o: o.to_json())
        return r

    def __str__(self):
        return json.dumps(self.to_json())


class C2ProfileParameters:
    """
    This class combines C2ProfileParameters and C2ProfileParametersInstance
    """

    def __init__(
        self,
        c2_profile: Union[C2Profile, str] = None,
        name: str = None,
        default_value: any = None,
        required: bool = None,
        verifier_regex: str = None,
        randomize: bool = None,
        parameter_type: str = None,
        description: str = None,
        id: int = None,
        value: any = None,
        instance_name: str = None,
        operation: Union[Operation, str] = None,
        callback: Union["Callback", int] = None,
        payload: Union["Payload", str] = None,
        crypto_type: bool = None,
        **kwargs,
    ):
        if isinstance(c2_profile, C2Profile) or c2_profile is None:
            self.c2_profile = c2_profile
        else:
            self.c2_profile = C2Profile(name=c2_profile)
        self.name = name
        self.default_value = default_value
        self.required = required
        self.verifier_regex = verifier_regex
        self.parameter_type = parameter_type
        self.description = description
        self.instance_name = instance_name
        self.value = value
        self.randomize = randomize
        self.crypto_type = crypto_type
        self.id = id
        if isinstance(payload, Payload) or payload is None:
            self.payload = payload
        else:
            self.payload = Payload(uuid=payload)
        if isinstance(operation, Operation) or operation is None:
            self.operation = operation
        else:
            self.operation = Operation(name=operation)
        if isinstance(callback, Callback) or callback is None:
            self.callback = callback
        else:
            self.callback = Callback(id=callback)
        vars(self).update(kwargs)

    def to_json(self):
        r = {}
        for k in vars(self):
            if getattr(self, k) is not None:
                try:
                    if k[0] == "_":
                        r[k[1:]] = getattr(self, k)
                    else:
                        r[k] = getattr(self, k)
                except:
                    if k[0] == "_":
                        r[k[1:]] = json.dumps(
                            getattr(self, k), default=lambda o: o.to_json()
                        )
                    else:
                        r[k] = json.dumps(getattr(self, k), default=lambda o: o.to_json())
        return r

    def __str__(self):
        return json.dumps(self.to_json())


class Callback:
    def __init__(
        self,
        init_callback: str = None,
        last_checkin: str = None,
        user: str = None,
        host: str = None,
        pid: int = None,
        ip: str = None,
        os: str = None,
        domain: str = None,
        architecture: str = None,
        description: str = None,
        operator: Union[Operator, str] = None,
        active: bool = None,
        port: int = None,
        socks_task: int = None,
        pcallback: Union["Callback", int] = None,
        registered_payload: str = None,  # corresponding payload's UUID
        payload_type: Union[PayloadType, str] = None,  # corresponding payload's type
        c2_profile: Union[C2Profile, str] = None,  # corresponding payload's c2 profile
        payload_description: str = None,  # corresponding payload's description
        integrity_level: int = None,
        operation: Union[Operation, str] = None,
        crypto_type: str = None,
        dec_key: str = None,
        enc_key: str = None,
        locked: bool = None,
        locked_operator: str = None,
        tasks: List[Union["Task", Dict]] = None,
        id: int = None,
        agent_callback_id: str = None,
        extra_info: str = None,
        sleep_info: str = None,
        external_ip: str = None,
        payload_type_id: int = None,
        supported_profiles: List[Union[C2Profile, Dict]] = None,
        tokens: list = None,
        loaded_commands: list = None,
        c2_profiles: dict = None,
        build_parameters: list = None,
        payload_uuid: str = None,
        payload_name: str = None,
        path: list = None,
        process_name: str = None,
        **kwargs,
    ):
        self.init_callback = init_callback
        self.last_checkin = last_checkin
        self.process_name = process_name
        self.user = user
        self.host = host
        self.pid = pid
        self.ip = ip
        self.port = port
        self.socks_task = socks_task
        self.domain = domain
        self.description = description
        self.agent_callback_id = agent_callback_id
        self.external_ip = external_ip
        self.payload_type_id = payload_type_id
        self.locked_operator = locked_operator
        self.os = os
        self.c2_profiles = c2_profiles
        self.loaded_commands = loaded_commands
        self.build_parameters = build_parameters
        self.path = path
        self.payload_uuid = payload_uuid
        self.payload_name = payload_name
        self.architecture = architecture
        if isinstance(operator, Operator) or operator is None:
            self.operator = operator
        else:
            self.operator = Operator(username=operator)
        self.active = active
        if isinstance(pcallback, Callback) or pcallback is None:
            self.pcallback = pcallback
        elif pcallback == "null":
            self.pcallback = None
        else:
            self.pcallback = Callback(id=pcallback)
        if registered_payload is None:
            self.registered_payload = registered_payload
        else:
            self.registered_payload = Payload(uuid=registered_payload)
        if isinstance(payload_type, PayloadType) or payload_type is None:
            self.payload_type = payload_type
        else:
            self.payload_type = PayloadType(ptype=payload_type)
        if isinstance(c2_profile, C2Profile) or c2_profile is None:
            self.c2_profile = c2_profile
        else:
            self.c2_profile = C2Profile(name=c2_profile)
        self.payload_description = payload_description
        self.integrity_level = integrity_level
        if isinstance(operation, Operation) or operation is None:
            self.operation = operation
        else:
            self.operation = Operation(name=operation)
        self.crypto_type = crypto_type
        self.dec_key = dec_key
        self.enc_key = enc_key
        self.tokens = tokens
        if isinstance(tasks, List):
            self.tasks = [Task(**x) if isinstance(x, Dict) else x for x in tasks]
        elif tasks is None:
            self.tasks = tasks
        else:
            self.tasks = [Task(**tasks) if isinstance(tasks, Dict) else tasks]
        self.id = id
        if supported_profiles is None:
            self.supported_profiles = supported_profiles
        else:
            self.supported_profiles = [
                x if isinstance(x, C2Profile) else C2Profile(**x)
                for x in supported_profiles
            ]
        vars(self).update(kwargs)

    def to_json(self):
        r = {}
        for k in vars(self):
            if getattr(self, k) is not None:
                try:
                    if k[0] == "_":
                        r[k[1:]] = getattr(self, k)
                    else:
                        r[k] = getattr(self, k)
                except:
                    if k[0] == "_":
                        r[k[1:]] = json.dumps(
                            getattr(self, k), default=lambda o: o.to_json()
                        )
                    else:
                        r[k] = json.dumps(getattr(self, k), default=lambda o: o.to_json())
        return r

    def __str__(self):
        return json.dumps(self.to_json())


class TaskFile:
    def __init__(self, content: Union[bytes, str], filename: str, param_name: str):
        self.filename = filename
        if isinstance(content, bytes):
            self.content = content
        else:
            self.content = base64.b64decode(content)
        self.param_name = param_name

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, filename):
        self._filename = filename

    @property
    def param_name(self):
        return self._param_name

    @param_name.setter
    def param_name(self, param_name):
        self._param_name = param_name

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, content):
        if isinstance(content, bytes):
            self._content = content
        else:
            self._content = base64.b64decode(content)

    def to_json(self):
        r = {}
        for k in vars(self):
            if getattr(self, k) is not None:
                try:
                    if k[0] == "_":
                        r[k[1:]] = getattr(self, k)
                    else:
                        r[k] = getattr(self, k)
                except:
                    if k[0] == "_":
                        r[k[1:]] = json.dumps(
                            getattr(self, k), default=lambda o: o.to_json()
                        )
                    else:
                        r[k] = json.dumps(getattr(self, k), default=lambda o: o.to_json())
        return r

    def __str__(self):
        return json.dumps(self.to_json())


class Task:
    def __init__(
        self,
        command: Union[Command, str] = None,
        agent_task_id: str = None,
        command_id: str = None,
        params: str = None,
        files: List[TaskFile] = None,
        timestamp: str = None,
        callback: Union[Callback, int, Dict] = None,
        operator: Union[Operator, str] = None,
        payload_type: str = None,
        status: str = None,
        task_status: str = None,  # sometimes this is set to not conflict with overall status message
        original_params: str = None,
        display_params: str = None,
        comment: str = None,
        comment_operator: Union[Operator, str] = None,
        completed: bool = None,
        id: int = None,
        status_timestamp_preprocessing: str = None,
        status_timestamp_processed: str = None,
        status_timestamp_submitted: str = None,
        status_timestamp_processing: str = None,
        operation: str = None,
        responses: List[Union["Response", Dict]] = None,
        stdout: str = None,
        stderr: str = None,
        token: dict = None,
        opsec_pre_blocked: bool = None,
        opsec_pre_bypassed: bool = None,
        opsec_pre_message: str = None,
        opsec_pre_bypass_role: str = None,
        opsec_pre_bypass_user: Union[Operator, str] = None,
        opsec_post_blocked: bool = None,
        opsec_post_bypassed: bool = None,
        opsec_post_message: str = None,
        opsec_post_bypass_role: str = None,
        opsec_post_bypass_user: Union[Operator, str] = None,
        parent_task: int = None,
        subtask_callback_function: str = None,
        group_callback_function: str = None,
        completed_callback_function: str = None,
        subtask_group_name: str = None,
        **kwargs,
    ):
        if isinstance(command, Command) or command is None:
            self.command = command
        else:
            self.command = Command(cmd=command)
        self.params = params
        self.timestamp = timestamp
        self.agent_task_id = agent_task_id
        self.command_id = command_id
        self.status_timestamp_preprocessing = status_timestamp_preprocessing
        self.status_timestamp_processed = status_timestamp_processed
        self.status_timestamp_submitted = status_timestamp_submitted
        self.status_timestamp_processing = status_timestamp_processing
        self.parent_task = parent_task
        self.subtask_callback_function = subtask_callback_function
        self.group_callback_function = group_callback_function
        self.completed_callback_function = completed_callback_function
        self.subtask_group_name = subtask_group_name
        self.operation = operation
        self.completed = completed
        self.display_params = display_params
        self.payload_type = payload_type
        if isinstance(callback, Callback) or callback is None:
            self.callback = callback
        elif isinstance(callback, Dict):
            self.callback = Callback(**callback)
        else:
            self.callback = Callback(id=callback)
        if isinstance(operator, Operator) or operator is None:
            self.operator = operator
        else:
            self.operator = Operator(username=operator)
        self.status = status
        self.original_params = original_params
        if comment == "":
            self.comment = None
        else:
            self.comment = comment
        if isinstance(comment_operator, Operator) or comment_operator is None:
            self.comment_operator = comment_operator
        elif comment_operator == "null":
            self.comment_operator = None
        else:
            self.comment_operator = Operator(username=comment_operator)
        self.id = id
        if isinstance(responses, List):
            self.responses = [
                Response(**x) if isinstance(x, Dict) else x for x in responses
            ]
        elif responses is None:
            self.responses = responses
        else:
            self.responses = [
                Response(**responses)
                if isinstance(responses, Dict)
                else Response(response=responses)
            ]
        if self.status is None:
            self.status = task_status
        self.display_params = display_params
        self.stdout = stdout
        self.stderr = stderr
        self.token = token
        self.opsec_pre_blocked = opsec_pre_blocked
        self.opsec_pre_bypassed = opsec_pre_bypassed
        self.opsec_pre_message = opsec_pre_message
        self.opsec_pre_bypass_role = opsec_pre_bypass_role
        self.opsec_pre_bypass_user = opsec_pre_bypass_user
        self.opsec_post_bypassed = opsec_post_bypassed
        self.opsec_post_blocked = opsec_post_blocked
        self.opsec_post_message = opsec_post_message
        self.opsec_post_bypass_role = opsec_post_bypass_role
        self.opsec_post_bypass_user = opsec_post_bypass_user
        if isinstance(files, List):
            self.files = files
        elif isinstance(files, TaskFile):
            self.files = [files]
        elif files is None:
            self.files = None
        else:
            raise Exception("Invalid value for files parameter")
        vars(self).update(kwargs)

    def to_json(self):
        r = {}
        for k in vars(self):
            if getattr(self, k) is not None:
                try:
                    if k[0] == "_":
                        r[k[1:]] = getattr(self, k)
                    else:
                        r[k] = getattr(self, k)
                except:
                    if k[0] == "_":
                        r[k[1:]] = json.dumps(
                            getattr(self, k), default=lambda o: o.to_json()
                        )
                    else:
                        r[k] = json.dumps(getattr(self, k), default=lambda o: o.to_json())
        return r

    def __str__(self):
        return json.dumps(self.to_json())


class Payload:
    def __init__(
        self,
        uuid: str = None,
        tag: str = None,
        operator: Union[Operator, str] = None,
        creation_time: str = None,
        payload_type: Union[PayloadType, str] = None,
        pcallback: Union["Callback", int] = None,
        c2_profiles: Dict[
            Union[C2Profile, str, Dict], List[Union[C2ProfileParameters, Dict]]
        ] = None,
        operation: Union[Operation, str] = None,
        wrapped_payload: Union["Payload", str] = None,
        deleted: bool = None,
        build_container: str = None,
        build_phase: str = None,
        build_message: str = None,
        build_stderr: str = None,
        build_stdout: str = None,
        callback_alert: bool = None,
        auto_generated: bool = None,
        task: Union[Task, Dict] = None,
        file_id: Union["FileMeta", Dict] = None,
        id: int = None,
        build_parameters: List[Dict] = None,
        commands: List = None,
        filename: str = None,
        os: str = None,
        selected_os: str = None,
        **kwargs,
    ):
        self.uuid = uuid
        self.tag = tag
        self.build_container = build_container
        self.callback_alert = callback_alert
        self.auto_generated = auto_generated
        self.build_parameters = build_parameters
        self.build_stderr = build_stderr
        self.build_stdout = build_stdout
        self.os = os
        self.selected_os = selected_os
        if isinstance(operator, Operator) or operator is None:
            self.operator = operator
        else:
            self.operator = Operator(username=operator)
        self.creation_time = creation_time
        if isinstance(payload_type, PayloadType) or payload_type is None:
            self.payload_type = payload_type
        else:
            self.payload_type = PayloadType(ptype=payload_type)
        if isinstance(pcallback, Callback) or pcallback is None:
            self.pcallback = pcallback
        else:
            self.pcallback = Callback(id=pcallback)
        if isinstance(operation, Operation) or operation is None:
            self.operation = operation
        else:
            self.operation = Operation(name=operation)
        if isinstance(task, Task) or task is None:
            self.task = task
        else:
            self.task = Task(**task)
        if isinstance(file_id, FileMeta) or file_id is None:
            self.file_id = file_id
        else:
            self.file_id = FileMeta(**file_id)
        if isinstance(wrapped_payload, Payload) or wrapped_payload is None:
            self.wrapped_payload = wrapped_payload
        else:
            self.wrapped_payload = Payload(uuid=wrapped_payload)
        self.deleted = deleted
        self.build_phase = build_phase
        self.build_message = build_message
        self.id = id
        if isinstance(commands, List) and len(commands) > 0:
            if isinstance(commands[0], Command):
                self.commands = commands
            elif isinstance(commands[0], Dict):
                self.commands = [Command(**x) for x in commands]
            else:
                self.commands = [Command(cmd=x) for x in commands]
        else:
            self.commands = None
        if isinstance(c2_profiles, Dict):
            self.c2_profiles = {}
            for k, v in c2_profiles.items():
                key = (
                    k["name"]
                    if isinstance(k, Dict)
                    else k.name
                    if isinstance(k, C2Profile)
                    else k
                )
                self.c2_profiles[key] = []
                for i in v:
                    # now iterate over each list of parameters for the profile
                    if isinstance(i, C2ProfileParameters):
                        self.c2_profiles[key].append(i)
                    elif isinstance(i, Dict):
                        self.c2_profiles[key].append(C2ProfileParameters(**i))
        else:
            self.c2_profiles = None
        self.filename = filename
        vars(self).update(kwargs)

    def to_json(self):
        r = {}
        for k in vars(self):
            if getattr(self, k) is not None:
                try:
                    if k[0] == "_":
                        r[k[1:]] = getattr(self, k)
                    else:
                        r[k] = getattr(self, k)
                except:
                    if k[0] == "_":
                        r[k[1:]] = json.dumps(
                            getattr(self, k), default=lambda o: o.to_json()
                        )
                    else:
                        r[k] = json.dumps(getattr(self, k), default=lambda o: o.to_json())
        return r

    def __str__(self):
        return json.dumps(self.to_json())


class FileMeta:
    def __init__(
        self,
        agent_file_id: str = None,
        total_chunks: int = None,
        chunks_received: int = None,
        chunk_size: int = None,
        task: Union[Task, Dict] = None,
        complete: bool = None,
        path: str = None,
        full_remote_path: str = None,
        host: str = None,
        is_payload: bool = None,
        is_screenshot: bool = None,
        is_download_from_agent: bool = None,
        file_browser: Dict = None,
        filename: str = None,
        delete_after_fetch: bool = None,
        operation: Union[Operation, str] = None,
        timestamp: str = None,
        deleted: bool = None,
        operator: Union[Operator, str] = None,
        md5: str = None,
        sha1: str = None,
        id: int = None,
        cmd: str = None,
        comment: str = None,
        upload: dict = None,
        params: dict = None,
        **kwargs,
    ):
        self.agent_file_id = agent_file_id
        self.total_chunks = total_chunks
        self.chunks_received = chunks_received
        self.chunk_size = chunk_size
        if isinstance(task, Task) or task is None:
            self.task = task
        else:
            self.task = Task(id=task)
        self.complete = complete
        self.path = path
        self.full_remote_path = full_remote_path
        self.host = host
        self.is_payload = is_payload
        self.is_screenshot = is_screenshot
        self.is_download_from_agent = is_download_from_agent
        self.file_browser = file_browser
        self.filename = filename
        self.delete_after_fetch = delete_after_fetch
        if isinstance(operation, Operation) or operation is None:
            self.operation = operation
        else:
            self.operation = Operation(name=operation)
        self.timestamp = timestamp
        self.deleted = deleted
        if isinstance(operator, Operator) or operator is None:
            self.operator = operator
        else:
            self.operator = Operator(username=operator)
        self.md5 = md5
        self.sha1 = sha1
        self.id = id
        self.cmd = cmd
        self.comment = comment
        self.upload = upload
        self.params = params
        vars(self).update(kwargs)

    def to_json(self):
        r = {}
        for k in vars(self):
            if getattr(self, k) is not None:
                try:
                    if k[0] == "_":
                        r[k[1:]] = getattr(self, k)
                    else:
                        r[k] = getattr(self, k)
                except:
                    if k[0] == "_":
                        r[k[1:]] = json.dumps(
                            getattr(self, k), default=lambda o: o.to_json()
                        )
                    else:
                        r[k] = json.dumps(getattr(self, k), default=lambda o: o.to_json())
        return r

    def __str__(self):
        return json.dumps(self.to_json())


class Response:
    def __init__(
        self,
        response: str = None,
        timestamp: str = None,
        task: Union[Task, int, Dict] = None,  # JSON string of the corresponding task
        id: int = None,
        **kwargs,
    ):
        self.response = response
        self.timestamp = timestamp
        if isinstance(task, Task) or task is None:
            self.task = task
        elif isinstance(task, Dict):
            self.task = Task(**task)
        else:
            self.task = Task(id=task)
        self.id = id
        vars(self).update(kwargs)

    def to_json(self):
        r = {}
        for k in vars(self):
            if getattr(self, k) is not None:
                try:
                    if k[0] == "_":
                        r[k[1:]] = getattr(self, k)
                    else:
                        r[k] = getattr(self, k)
                except:
                    if k[0] == "_":
                        r[k[1:]] = json.dumps(
                            getattr(self, k), default=lambda o: o.to_json()
                        )
                    else:
                        r[k] = json.dumps(getattr(self, k), default=lambda o: o.to_json())
        return r

    def __str__(self):
        return json.dumps(self.to_json())


class Credential:
    def __init__(
        self,
        type: str = None,
        task: Union[Task, int] = None,
        task_command: Union[Command, str] = None,
        account: str = None,
        realm: str = None,
        id: int = None,
        operator: Union[Operator, str] = None,
        operation: Union[Operation, str] = None,
        timestamp: str = None,
        credential: bytes = None,
        comment: str = None,
        deleted: bool = None,
        new: bool = None,
        **kwargs,
    ):
        self.type = type
        if isinstance(task, Task) or task is None:
            self.task = task
        else:
            self.task = Task(id=task)
        if isinstance(task_command, Command) or task_command is None:
            self.task_command = task_command
        else:
            self.task_command = Command(cmd=task_command)
        self.account = account
        self.realm = realm
        self.id = id
        if isinstance(operator, Operator) or operator is None:
            self.operator = operator
        else:
            self.operator = Operator(username=operator)
        if isinstance(operation, Operation) or operation is None:
            self.operation = operation
        else:
            self.operation = Operation(name=operation)
        self.timestamp = timestamp
        self.credential = credential
        self.comment = comment
        self.deleted = deleted
        self.new = new
        vars(self).update(kwargs)

    def to_json(self):
        r = {}
        for k in vars(self):
            if getattr(self, k) is not None:
                try:
                    if k[0] == "_":
                        r[k[1:]] = getattr(self, k)
                    else:
                        r[k] = getattr(self, k)
                except:
                    if k[0] == "_":
                        r[k[1:]] = json.dumps(
                            getattr(self, k), default=lambda o: o.to_json()
                        )
                    else:
                        r[k] = json.dumps(getattr(self, k), default=lambda o: o.to_json())
        return r

    def __str__(self):
        return json.dumps(self.to_json())


class Keylog:
    def __init__(
        self,
        task: Union[Task, int] = None,
        keystrokes: bytes = None,
        window: str = None,
        timestamp: str = None,
        operation: Union[Operation, str] = None,
        user: str = None,
        host: str = None,
        id: int = None,
        callback: Union[Callback, Dict] = None,
        **kwargs,
    ):
        self.keystrokes = keystrokes
        self.window = window
        self.timestamp = timestamp
        self.user = user
        self.host = host
        if isinstance(task, Task) or task is None:
            self.task = task
        else:
            self.task = Task(id=int)
        if isinstance(operation, Operation) or operation is None:
            self.operation = operation
        else:
            self.operation = Operation(name=operation)
        if isinstance(callback, Callback) or callback is None:
            self.callback = callback
        else:
            self.callback = Callback(**callback)
        vars(self).update(kwargs)

    def to_json(self):
        r = {}
        for k in vars(self):
            if getattr(self, k) is not None:
                try:
                    if k[0] == "_":
                        r[k[1:]] = getattr(self, k)
                    else:
                        r[k] = getattr(self, k)
                except:
                    if k[0] == "_":
                        r[k[1:]] = json.dumps(
                            getattr(self, k), default=lambda o: o.to_json()
                        )
                    else:
                        r[k] = json.dumps(getattr(self, k), default=lambda o: o.to_json())
        return r

    def __str__(self):
        return json.dumps(self.to_json())


class DisabledCommandsProfile:
    def __init__(
        self,
        payload_types: List[Union[PayloadType, str, Dict]] = None,
        name: str = None,
        **kwargs,
    ):
        self.name = name
        if isinstance(payload_types, List):
            self.payload_types = [
                PayloadType(ptype=x)
                if isinstance(x, str)
                else PayloadType(**x)
                if isinstance(x, Dict)
                else x
                for x in payload_types
            ]
        else:
            self.payload_types = payload_types
        vars(self).update(kwargs)

    def to_json(self):
        r = {}
        for k in vars(self):
            if getattr(self, k) is not None:
                try:
                    if k[0] == "_":
                        r[k[1:]] = getattr(self, k)
                    else:
                        r[k] = getattr(self, k)
                except:
                    if k[0] == "_":
                        r[k[1:]] = json.dumps(
                            getattr(self, k), default=lambda o: o.to_json()
                        )
                    else:
                        r[k] = json.dumps(getattr(self, k), default=lambda o: o.to_json())
        return r

    def __str__(self):
        return json.dumps(self.to_json())


class EventMessage:
    def __init__(
        self,
        operator: Union[Operator, str] = None,
        timestamp: str = None,
        message: str = None,
        operation: Union[Operation, str] = None,
        level: str = None,
        deleted: bool = None,
        resolved: bool = None,
        id: int = None,
        channel: str = None,
        alerts: List[Dict] = None,
        source: str = None,
        count: int = None,
        **kwargs,
    ):
        self.timestamp = timestamp
        self.message = message
        self.level = level
        self.deleted = deleted
        self.resolved = resolved
        self.id = id
        self.channel = channel
        self.alerts = alerts
        self.source = source
        self.count = count
        if isinstance(operator, Operator) or operator is None:
            self.operator = operator
        else:
            self.operator = Operator(username=operator)
        if isinstance(operation, Operation) or operation is None:
            self.operation = operation
        else:
            self.operation = Operation(name=operation)
        vars(self).update(kwargs)

    def to_json(self):
        r = {}
        for k in vars(self):
            if getattr(self, k) is not None:
                try:
                    if k[0] == "_":
                        r[k[1:]] = getattr(self, k)
                    else:
                        r[k] = getattr(self, k)
                except:
                    if k[0] == "_":
                        r[k[1:]] = json.dumps(
                            getattr(self, k), default=lambda o: o.to_json()
                        )
                    else:
                        r[k] = json.dumps(getattr(self, k), default=lambda o: o.to_json())
        return r

    def __str__(self):
        return json.dumps(self.to_json())


class MythicResponse:
    def __init__(
        self,
        response=None,
        raw_response: Dict[str, str] = None,
        response_code: int = None,
        status: str = None,
        **kwargs,
    ):
        # set the response_code and raw_response automatically
        self.response_code = response_code
        self.raw_response = raw_response
        # determine and set status if it's not explicitly specified
        if status is None and "status" in raw_response:
            self.status = raw_response["status"]
        elif status is None and self.response_code != 200:
            self.status = "error"
        else:
            self.status = status
        # if the raw_response has a status indicator, remove it and set the response
        #   otherwise just set response to raw_response and process later
        if "status" in raw_response and response is None:
            del raw_response["status"]
            self.response = raw_response
        elif response is None:
            self.response = raw_response
        vars(self).update(kwargs)

    def to_json(self):
        r = {}
        for k in vars(self):
            try:
                r[k] = getattr(self, k)
            except:
                r[k] = json.dumps(getattr(self, k))
        return r

    def __str__(self):
        return json.dumps(self.to_json())


class Mythic:
    def __init__(
        self,
        username: str = None,
        password: str = None,
        apitoken: Union[APIToken, str] = None,
        access_token: str = None,
        refresh_token: str = None,
        server_ip: str = None,
        ssl: bool = False,
        server_port: str = None,
        server_api_version: int = 1.4,
        operator: Operator = None,
        global_timeout: int = None,
    ):
        self.username = username
        self.password = password
        if isinstance(apitoken, APIToken) or apitoken is None:
            self._apitoken = apitoken
        else:
            self._apitoken = APIToken(token_value=apitoken)
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.server_ip = server_ip
        self.server_port = server_port
        self.server_api_version = server_api_version
        self.operator = operator
        self.ssl = ssl
        self.http = "http://" if not ssl else "https://"
        self.ws = "ws://" if not ssl else "wss://"
        self.global_timeout = global_timeout if global_timeout is not None else -1
        self.scripting_version = 3
        print("[!] ----- DEPRECATION WARNING --------")
        print(
            "[!] This is the last release of Mythic that'll have the mythic_rest interface"
        )
        print(
            "[!] Starting in PyPi version 0.1.0, there will only be the new GraphQL interfaces"
        )
        print(
            "[!] More information can be found here: https://github.com/MythicMeta/Mythic_Scripting#new-graphql-interface"
        )
        print("[!] ------ END DEPRECATION WARNING -------")

    def to_json(self):
        r = {}
        for k in vars(self):
            try:
                if k[0] == "_":
                    r[k[1:]] = getattr(self, k)
                else:
                    r[k] = getattr(self, k)
            except:
                if k[0] == "_":
                    r[k[1:]] = json.dumps(getattr(self, k), default=lambda o: o.to_json())
                else:
                    r[k] = json.dumps(getattr(self, k), default=lambda o: o.to_json())
        return r

    def __str__(self):
        return json.dumps(self.to_json())

    @property
    def apitoken(self):
        return self._apitoken

    @apitoken.setter
    def apitoken(self, apitoken=None):
        if isinstance(apitoken, APIToken) or apitoken is None:
            self._apitoken = apitoken
        else:
            self._apitoken = APIToken(token_value=apitoken)

    # ======== BASIC GET/POST/PUT/DELETE JSON WEB REQUESTS =========

    def get_headers(self) -> dict:
        if self.apitoken is not None:
            return {"apitoken": self.apitoken.token_value}
        elif self.access_token is not None:
            return {"Authorization": "Bearer {}".format(self.access_token)}
        else:
            return {}

    async def get_json(self, url) -> MythicResponse:
        headers = self.get_headers()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, ssl=False) as resp:
                    return MythicResponse(
                        response_code=resp.status, raw_response=await resp.json()
                    )
        except OSError as o:
            # print(o)
            return MythicResponse(
                response_code=0, raw_response={"status": "error", "error": str(o)}
            )
        except Exception as e:
            # print(e)
            return MythicResponse(
                response_code=0, raw_response={"status": "error", "error": str(e)}
            )

    async def get_file(self, url) -> bytes:
        headers = self.get_headers()
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, ssl=False) as resp:
                data = await resp.read()
                return data

    async def put_json(self, url, data) -> MythicResponse:
        headers = self.get_headers()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(
                    url, json=data, headers=headers, ssl=False
                ) as resp:
                    return MythicResponse(
                        response_code=resp.status, raw_response=await resp.json()
                    )
        except OSError as o:
            return MythicResponse(
                response_code=0, raw_response={"status": "error", "error": str(o)}
            )
        except Exception as e:
            return MythicResponse(
                response_code=0, raw_response={"status": "error", "error": str(e)}
            )

    async def post_json(self, url, data) -> MythicResponse:
        headers = self.get_headers()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=data, headers=headers, ssl=False
                ) as resp:
                    return MythicResponse(
                        response_code=resp.status, raw_response=await resp.json()
                    )
        except OSError as o:
            return MythicResponse(
                response_code=0, raw_response={"status": "error", "error": str(o)}
            )
        except Exception as e:
            return MythicResponse(
                response_code=0, raw_response={"status": "error", "error": str(e)}
            )

    async def delete_json(self, url) -> MythicResponse:
        headers = self.get_headers()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, headers=headers, ssl=False) as resp:
                    return MythicResponse(
                        response_code=resp.status, raw_response=await resp.json()
                    )
        except OSError as o:
            return MythicResponse(
                response_code=0, raw_response={"status": "error", "error": str(o)}
            )
        except Exception as e:
            return MythicResponse(
                response_code=0, raw_response={"status": "error", "error": str(e)}
            )

    # ======== WEBSOCKET BASED HELPER ENDPOINTS ========================

    async def print_websocket_output(self, mythic, data) -> None:
        try:
            await json_print(data)
        except Exception as e:
            raise Exception("Failed to decode json data: " + str(e))

    async def cast_data(self, data):
        try:
            json_data = json.loads(data)
            if "channel" in json_data:
                if "callback" in json_data["channel"]:
                    del json_data["channel"]
                    return Callback(**json_data)
                elif "task" in json_data["channel"]:
                    del json_data["channel"]
                    return Task(**json_data)
                elif "response" in json_data["channel"]:
                    del json_data["channel"]
                    return Response(**json_data)
                elif "historic" in json_data["channel"]:
                    return EventMessage(**json_data)
                elif "event" in json_data["channel"]:
                    return EventMessage(**json_data)
            elif "chunks_received" in json_data:
                return FileMeta(**json_data)
            elif "build_phase" in json_data:
                return Payload(**json_data)
            elif "agent_task_id" in json_data:
                return Task(**json_data)
            elif "response" in json_data:
                return Response(**json_data)
            elif "realm" in json_data:
                return Credential(**json_data)
            elif "level" in json_data:
                return EventMessage(**json_data)
            elif "agent_callback_id" in json_data:
                return Callback(**json_data)
            else:
                raise Exception(
                    "Unknown Mythic Object: " + json.dumps(json_data, indent=2)
                )
        except Exception as e:
            raise Exception("Failed to decode json data: " + str(e))

    async def get_ws_error(self, error_code):
        if error_code == 1000:
            return "OK"
        elif error_code == 1001:
            return "GOING_AWAY"
        elif error_code == 1002:
            return "PROTOCOL_ERROR"
        elif error_code == 1003:
            return "UNSUPPORTED_DATA"
        elif error_code == 1007:
            return "UNSUPPORTED_TEXT"
        elif error_code == 1008:
            return "POLICY_VIOLATION"
        elif error_code == 1009:
            return "MESSAGE_TOO_BIG"
        elif error_code == 1010:
            return "MANDATORY_EXTENSION"
        elif error_code == 1011:
            return "INTERNAL_ERROR"
        elif error_code == 1012:
            return "SERVICE_RESTART"
        elif error_code == 1013:
            return "TRY_AGAIN_LATER"
        else:
            return "UNKNOWN ERROR CODE: {}".format(str(error_code))

    async def thread_output_helper(
        self, url, callback_function=None, timeout=None, exception_handler=None
    ) -> None:
        headers = self.get_headers()
        if timeout is None:
            timeout = self.global_timeout
        try:
            async with aiohttp.ClientSession() as session:
                ws = await session.ws_connect(url, headers=headers, ssl=False)
                start = time()
                while True:
                    try:
                        if timeout > 0 and (time() - start >= timeout):
                            raise Exception(
                                "Timeout in listening on websocket endpoint: {}".format(
                                    url
                                )
                            )
                        msg = await ws.receive()
                        if msg.type == aiohttp.WSMsgType.CLOSE:
                            raise Exception(
                                "Websocket closed, {}".format(
                                    await self.get_ws_error(msg.data)
                                )
                            )
                        if msg.data is None:
                            raise Exception(
                                "Got no data from websocket: {}".format(str(msg))
                            )
                        if msg.data != "":
                            task = asyncio.get_event_loop().create_task(
                                callback_function(self, await self.cast_data(msg.data))
                            )
                            asyncio.ensure_future(task)
                    except Exception as e:
                        raise Exception(
                            "Got exception reading from websocket, exiting websocket: "
                            + str(e)
                        )
        except Exception as e:
            if exception_handler is not None and callable(exception_handler):
                task = asyncio.get_event_loop().create_task(exception_handler(self, e))
                asyncio.ensure_future(task)
                return
            else:
                print("Failed to get websocket connection: " + str(e))
                return

    async def stream_output(
        self, url, callback_function, timeout, exception_handler
    ) -> asyncio.Task:
        task = asyncio.get_event_loop().create_task(
            self.thread_output_helper(url, callback_function, timeout, exception_handler)
        )
        asyncio.ensure_future(task)
        return task

    # ================== OPERATION ENDPOINTS ======================

    async def get_current_operation_info(self) -> MythicResponse:
        """
        Gets information about the current operation for the user
        """
        if self.operator is None:
            await self.get_self()
        url = "{}{}:{}/api/v{}/operations/{}".format(
            self.http,
            self.server_ip,
            self.server_port,
            self.server_api_version,
            self.operator.current_operation.id,
        )
        resp = await self.get_json(url)
        if resp.response_code == 200 and resp.status == "success":
            resp.response = Operation(**resp.response)
        return resp

    async def get_all_operations(self) -> MythicResponse:
        """
        Gets information about all operations your operator can see
        """
        url = "{}{}:{}/api/v{}/operations".format(
            self.http, self.server_ip, self.server_port, self.server_api_version
        )
        resp = await self.get_json(url)
        if resp.response_code == 200 and resp.status == "success":
            operations = []
            for o in resp.response["output"]:
                operations.append(Operation(**o))
            resp.response = operations
        return resp

    async def get_operation(self, operation: Operation) -> MythicResponse:
        """
        Gets information about the current user
        """
        if operation.id is None:
            resp = await self.get_all_operations()
            if resp.response_code == 200 and resp.status == "success":
                for o in resp.response:
                    if o.name == operation.name:
                        resp.response = o
                        return resp
            raise Exception(
                "Failed to find operation: "
                + json.dumps(resp, indent=2, default=lambda o: o.to_json())
            )
        else:
            url = "{}{}:{}/api/v{}/operations/{}".format(
                self.http,
                self.server_ip,
                self.server_port,
                self.server_api_version,
                str(operation.id),
            )
            resp = await self.get_json(url)
            if resp.response_code == 200 and resp.status == "success":
                resp.response = Operation(**resp.response)
            return resp

    async def add_or_update_operator_for_operation(
        self, operation: Operation, operator: Operator
    ) -> MythicResponse:
        """
        Adds an operator to an operation or updates an operator's view/block lists in an operation
        """
        resp = await self.get_operation(operation)
        if resp.status == "success":
            operation = resp.response
        else:
            raise Exception(
                "failed to get operation in add_or_update_operator_for_operation"
            )
        data = {"add_members": [await obj_to_json(operator)]}
        if operator.base_disabled_commands is not None:
            data["add_disabled_commands"] = [await obj_to_json(operator)]
        url = "{}{}:{}/api/v{}/operations/{}".format(
            self.http,
            self.server_ip,
            self.server_port,
            self.server_api_version,
            str(operation.id),
        )
        resp = await self.put_json(url, data=data)
        if resp.response_code == 200 and resp.status == "success":
            resp.response = Operation(**resp.response)
        return resp

    async def remove_operator_from_operation(
        self, operation: Operation, operator: Operator
    ) -> MythicResponse:
        """
        Removes an operator from an operation
        """
        resp = await self.get_operation(operation)
        if resp.status == "success":
            operation = resp.response
        else:
            raise Exception("failed to get operation in remove_operator_for_operation")
        data = {"remove_members": [operator.username]}
        url = "{}{}:{}/api/v{}/operations/{}".format(
            self.http,
            self.server_ip,
            self.server_port,
            self.server_api_version,
            str(operation.id),
        )
        resp = await self.put_json(url, data=data)
        if resp.response_code == 200 and resp.status == "success":
            resp.response = Operation(**resp.response)
        return resp

    async def update_operation(self, operation: Operation) -> MythicResponse:
        """
        Updates information about an operation such as webhook and completion status
        """
        if operation.id is None:
            resp = await self.get_operation(operation)
            if resp.status == "error":
                raise Exception("Failed to get_operation in update_operation")
            operation.id = resp.response.id
        url = "{}{}:{}/api/v{}/operations/{}".format(
            self.http,
            self.server_ip,
            self.server_port,
            self.server_api_version,
            str(operation.id),
        )
        send_data = await obj_to_json(operation)
        if "admin" in send_data:
            send_data["admin"] = send_data["admin"]["username"]
        resp = await self.put_json(url, data=send_data)
        if resp.response_code == 200 and resp.status == "success":
            resp.response = Operation(**resp.response)
        return resp

    async def create_operation(self, operation: Operation) -> MythicResponse:
        """
        Creates a new operation and specifies the admin of the operation
        """
        url = "{}{}:{}/api/v{}/operations/".format(
            self.http,
            self.server_ip,
            self.server_port,
            self.server_api_version,
        )
        data = await obj_to_json(operation)
        if "admin" in data:
            data["admin"] = data["admin"]["username"]
        resp = await self.post_json(url, data=data)
        if resp.response_code == 200 and resp.status == "success":
            resp.response = Operation(**resp.response)
        return resp

    # ================== OPERATOR ENDPOINTS ======================

    async def get_self(self) -> MythicResponse:
        """
        Gets information about the current user
        """
        url = "{}{}:{}/api/v{}/operators/me".format(
            self.http, self.server_ip, self.server_port, self.server_api_version
        )
        resp = await self.get_json(url)
        if resp.response_code == 200 and resp.status == "success":
            self.operator = Operator(**resp.response)
            resp.response = Operator(**resp.response)
        return resp

    async def get_operator(self, operator: Operator) -> MythicResponse:
        """
        Gets information about the current user
        """
        if operator.id is None:
            # need to get the operator's ID first, which means we need to get all operators and match the username
            url = "{}{}:{}/api/v{}/operators/".format(
                self.http, self.server_ip, self.server_port, self.server_api_version
            )
            resp = await self.get_json(url)
            if resp.response_code == 200:
                if resp.status is None:
                    resp.status = "success"
                for o in resp.response:
                    if o["username"] == operator.username:
                        resp.response = Operator(**o)
                        return resp
                raise Exception(
                    "Operator not found: "
                    + json.dumps(resp, indent=2, default=lambda o: o.to_json())
                )
            return resp
        else:
            url = "{}{}:{}/api/v{}/operators/{}".format(
                self.http,
                self.server_ip,
                self.server_port,
                self.server_api_version,
                str(operator.id),
            )
            resp = await self.get_json(url)
            if resp.response_code == 200:
                resp.response = Operator(**resp.response)
            return resp

    async def create_operator(self, operator: Operator) -> MythicResponse:
        """
        Creates a new operator with the specified username and password.
        If the operator name already exists, just returns information about that operator.
        """
        url = "{}{}:{}/api/v{}/operators".format(
            self.http, self.server_ip, self.server_port, self.server_api_version
        )
        resp = await self.post_json(
            url, data={"username": operator.username, "password": operator.password}
        )
        if resp.response_code == 200 and resp.status == "success":
            resp.response = Operator(**resp.response)
        elif resp.status == "error":
            try:
                resp2 = await self.get_operator(operator)
                if resp2.status == "success":
                    return resp2
            except Exception as e:
                raise Exception(
                    "Unable to create operator and no active operator found: "
                    + json.dumps(resp, indent=2, default=lambda o: o.to_json())
                )
        return resp

    async def update_operator(self, operator: Operator) -> MythicResponse:
        """
        Updates information about the specified operator.
        """
        if operator.id is None:
            resp = await self.get_operator(operator)
            if resp.status == "error":
                raise Exception("Failed to get_operator in update_operator")
            operator.id = resp.response.id
        url = "{}{}:{}/api/v{}/operators/{}".format(
            self.http,
            self.server_ip,
            self.server_port,
            self.server_api_version,
            str(operator.id),
        )
        resp = await self.put_json(url, data=await obj_to_json(operator))
        if resp.response_code == 200 and resp.status == "success":
            resp.response = Operator(**resp.response)
        return resp

    # ================== APITOKEN ENDPOINTS ======================

    async def get_apitokens(self) -> MythicResponse:
        """
        Gets all of the user's API tokens in a List
        :return:
        """
        url = "{}{}:{}/api/v{}/apitokens".format(
            self.http, self.server_ip, self.server_port, self.server_api_version
        )
        resp = await self.get_json(url)
        if resp.response_code == 200 and resp.status == "success":
            # update the response with APIToken objects instead of just a dictionary
            resp.response = [APIToken(**x) for x in resp.response["apitokens"]]
        return resp

    async def create_apitoken(self, token_type="User") -> MythicResponse:
        """
        Creates an API token for the user
        :param token_type:
            must be either "User" or "C2"
        :return:
        """
        # token_type should be C2 or User
        url = "{}{}:{}/api/v{}/apitokens".format(
            self.http, self.server_ip, self.server_port, self.server_api_version
        )
        resp = await self.post_json(url, data={"token_type": token_type})
        if resp.response_code == 200 and resp.status == "success":
            # update the response to be an object
            resp.response = APIToken(**resp.response)
        return resp

    async def remove_apitoken(self, apitoken: Union[APIToken, Dict]) -> MythicResponse:
        """
        Removes the specified API token and invalidates it going forward
        :param apitoken:
            if using the APIToken class, the following must be set:
                id
        :return:
        """
        # take in an object and parse it if the value isn't explicitly given
        url = "{}{}:{}/api/v{}/apitokens/{}".format(
            self.http,
            self.server_ip,
            self.server_port,
            self.server_api_version,
            str(apitoken.id if isinstance(apitoken, APIToken) else apitoken["id"]),
        )
        resp = await self.delete_json(url)
        if resp.response_code == 200 and resp.status == "success":
            # update the response to ben an object
            resp.response = APIToken(**resp.response)
        return resp

    # ================= PAYLOAD ENDPOINTS =======================

    async def get_payloads(self) -> MythicResponse:
        """
        Get all the payloads for the current operation
        :return:
        """
        url = "{}{}:{}/api/v{}/payloads/current_operation".format(
            self.http, self.server_ip, self.server_port, self.server_api_version
        )
        resp = await self.get_json(url)
        if resp.response_code == 200:
            # update the response with APIToken objects instead of just a dictionary
            resp.response = [Payload(**x) for x in resp.response]
        return resp

    async def generate_mod_rewrite(self, target=Union[Payload, str]) -> MythicResponse:
        target_uuid = ""
        if isinstance(target, Payload):
            target_uuid = target.uuid
            if target_uuid is None or target_uuid == "":
                raise Exception(
                    "Missing required parameter mythic_rest.Payload(uuid='uuid here')"
                )
        else:
            target_uuid = target
        url = f"{self.http}{self.server_ip}:{self.server_port}/api/v{self.server_api_version}/redirect_rules_webhook"
        resp = await self.post_json(url, data={"input": {"uuid": target_uuid}})
        if resp.response_code != 200:
            raise Exception(
                "Connection failed with error code: " + str(resp.response_code)
            )
        if resp.status == "success":
            resp.response = resp.response["output"]
        return resp

    async def remove_payload(self, payload: Union[Payload, Dict]) -> MythicResponse:
        """
        Mark a payload as deleted in the database and remove it from disk
        Truly removing it from the database would delete any corresponding tasks/callbacks, so we don't do that
        :param payload:
        :return:
        """
        url = "{}{}:{}/api/v{}/payloads/{}".format(
            self.http,
            self.server_ip,
            self.server_port,
            self.server_api_version,
            str(payload.uuid if isinstance(payload, Payload) else payload["uuid"]),
        )
        resp = await self.delete_json(url)
        if resp.response_code == 200 and resp.status == "success":
            # update the response to ben an object
            resp.response = Payload(**resp.response)
        return resp

    async def create_payload(
        self,
        payload: Payload,
        all_commands: bool = None,
        timeout=None,
        wait_for_build: bool = None,
        exclude_commands: list = [],
    ) -> MythicResponse:
        """
        :param payload:

        :return:
        {"payload_type":"poseidon",
        "c2_profiles":[
          {"c2_profile_parameters":
            {
              "callback_host":"https://domain.com",
              "callback_interval":"10",
              "callback_jitter":"23",
              "callback_port":"80",
              "encrypted_exchange_check":"T",
              "killdate":"yyyy-mm-dd"
            },
          "c2_profile":"http"
          }],
        "selected_os": "macOS",
        "filename":"poseidon.bin",
        "tag":"this is my tag yo for initial access",
        "commands":["cat","cd","cp","curl","download","drives","exit","getenv","getuser","jobkill","jobs","jxa","keylog","keys","kill","libinject","listtasks","ls","mkdir","mv","portscan","ps","pwd","rm","screencapture","setenv","shell","sleep","socks","sshauth","triagedirectory","unsetenv","upload","xpc"],
        "build_parameters":[
          {"name":"mode","value":"default"},
          ]
        }"
        """
        data = {}
        data["payload_type"] = payload.payload_type.ptype
        data["filename"] = payload.filename
        data["tag"] = payload.tag
        if payload.wrapped_payload is None:
            data["c2_profiles"] = []
            for k, v in payload.c2_profiles.items():
                parameters = {i.name: i.value for i in v}
                data["c2_profiles"].append(
                    {"c2_profile": k, "c2_profile_parameters": parameters}
                )
        data["build_parameters"] = []
        if payload.os is not None:
            data["selected_os"] = payload.os
        elif payload.selected_os is not None:
            data["selected_os"] = payload.selected_os
        if all_commands:
            if payload.payload_type.id is None:
                resp = await self.get_payloadtypes()
                for p in resp.response:
                    try:
                        if p.ptype == payload.payload_type.ptype:
                            payload.payload_type = p
                    except Exception as e:
                        print(f"[-] Error trying to get payload type list: {e}")
                        await json_print(resp.response)
                        return resp
            resp = await self.get_payloadtype_commands(payload.payload_type)
            # now iterate over the commands and make sure to not include script_only or wrong supported_os fields
            commands = []
            if isinstance(resp.response, str):
                raise Exception("Failed to get available commands")
            for c in resp.response:
                try:
                    attributes = c.attributes
                    if len(attributes["supported_os"]) == 0:
                        commands.append(c)
                    elif data["selected_os"] in attributes["supported_os"]:
                        commands.append(c)
                except Exception as e:
                    print(f"[-] Error trying to parse command information: {e}")
                    pass
            payload.commands = [c for c in commands if c.cmd not in exclude_commands]
        if payload.commands is not None:
            data["commands"] = [c.cmd for c in payload.commands]
        else:
            data["commands"] = []
        if payload.build_parameters is not None:
            data["build_parameters"] = payload.build_parameters
        if payload.wrapped_payload is not None:
            data["wrapped_payload"] = payload.wrapped_payload.uuid

        url = "{}{}:{}/api/v{}/payloads/create".format(
            self.http, self.server_ip, self.server_port, self.server_api_version
        )
        resp = await self.post_json(url, data=data)
        if resp.response_code == 200 and resp.status == "success":
            # update the response to be an object
            # this will be a very basic payload with just the payload UUID
            resp.response = Payload(**resp.response)
            if wait_for_build is not None and wait_for_build:
                status = await self.wait_for_payload_status_change(
                    resp.response.uuid, "success", timeout
                )
                if status is None:
                    raise Exception(
                        "Failed to get final payload status from wait_for_payload_status_change in creat_payload"
                    )
                else:
                    resp.response = status
        return resp

    async def get_one_payload_info(self, payload: Union[Payload, Dict]) -> MythicResponse:
        """
        Get information about a specific payload
        :param payload:
            if using the Payload class, the following must be set:
                uuid
        :return:
        """
        url = "{}{}:{}/api/v{}/payloads/{}".format(
            self.http,
            self.server_ip,
            self.server_port,
            self.server_api_version,
            str(payload.uuid if isinstance(payload, Payload) else payload["uuid"]),
        )
        resp = await self.get_json(url)
        if resp.response_code == 200 and resp.status == "success":
            # update the response to ben an object
            resp.response = Payload(**resp.response)
        return resp

    async def download_payload(self, payload: Union[Payload, Dict]) -> bytes:
        """
        Get the final payload for a specified payload
        :param payload:
            if using Payload class, the following must be set:
                uuid
        :return:
        """
        url = "{}{}:{}/api/v{}/payloads/download/{}".format(
            self.http,
            self.server_ip,
            self.server_port,
            self.server_api_version,
            str(payload.uuid if isinstance(payload, Payload) else payload["uuid"]),
        )
        resp = await self.get_file(url)
        return resp

    # ================= FILE ENDPOINTS =======================

    async def download_file(self, file: FileMeta) -> bytes:
        """
        Download a file that is either scheduled for upload or is finished downloading
        """
        url = "{}{}:{}/api/v{}/files/download/{}".format(
            self.http,
            self.server_ip,
            self.server_port,
            self.server_api_version,
            file.agent_file_id,
        )
        resp = await self.get_file(url)
        return resp

    # ================ PAYLOAD TYPE ENDPOINTS ====================

    async def get_payloadtypes(self) -> MythicResponse:
        """
        Get all payload types registered with Apfell
        :return:
        """
        url = "{}{}:{}/api/v{}/payloadtypes/".format(
            self.http, self.server_ip, self.server_port, self.server_api_version
        )
        resp = await self.get_json(url)
        if resp.response_code == 200:
            # update the response with APIToken objects instead of just a dictionary
            tmp = []
            for x in resp.response["payloads"]:
                tmp.append(PayloadType(**x))
            for x in resp.response["wrappers"]:
                tmp.append(PayloadType(**x))
            resp.response = tmp
        return resp

    async def get_payloadtype(
        self, payload_type: Union[PayloadType, Dict]
    ) -> MythicResponse:
        """
        Get information about a specific payload type
        :param payload_type:
            if using PayloadType class, the following must be set:
                ptype
        :return:
        """
        url = "{}{}:{}/api/v{}/payloadtypes/{}".format(
            self.http,
            self.server_ip,
            self.server_port,
            self.server_api_version,
            str(
                payload_type.id
                if isinstance(payload_type, PayloadType)
                else payload_type["id"]
            ),
        )
        resp = await self.get_json(url)
        if resp.response_code == 200 and resp.status == "success":
            # update the response with APIToken objects instead of just a dictionary
            resp.response = PayloadType(**resp.response)
        return resp

    async def get_payloadtype_commands(
        self, payload_type: Union[PayloadType, Dict]
    ) -> MythicResponse:
        """
        Get the commands registered for a specific payload type
        :param payload_type:
            if using PayloadType class, the following must be set:
                ptype
        :return:
        """
        url = "{}{}:{}/api/v{}/payloadtypes/{}/commands".format(
            self.http,
            self.server_ip,
            self.server_port,
            self.server_api_version,
            str(
                payload_type.id
                if isinstance(payload_type, PayloadType)
                else payload_type["id"]
            ),
        )
        resp = await self.get_json(url)
        if resp.response_code == 200 and resp.status == "success":
            resp.response = [Command(**x) for x in resp.response["commands"]]
        return resp

    # ================ TASKING ENDPOINTS ========================

    async def get_all_tasks(self) -> MythicResponse:
        """
        Get all of the tasks associated with the user's current operation
        :return:
        """
        url = "{}{}:{}/api/v{}/tasks/".format(
            self.http, self.server_ip, self.server_port, self.server_api_version
        )
        resp = await self.get_json(url)
        if resp.response_code == 200:
            # update the response with APIToken objects instead of just a dictionary
            resp.response = [Task(**x) for x in resp.response]
        return resp

    async def get_all_tasks_for_callback(
        self, callback: Union[Callback, Dict]
    ) -> MythicResponse:
        """
        Get the tasks (no responses) for a specific callback
        :param callback:
            if using the Callback class, the following must be set:
                id
        :return:
        """
        url = "{}{}:{}/api/v{}/tasks/callback/{}".format(
            self.http,
            self.server_ip,
            self.server_port,
            self.server_api_version,
            callback.id if isinstance(callback, Callback) else callback["id"],
        )
        resp = await self.get_json(url)
        if resp.response_code == 200:
            # update the response with APIToken objects instead of just a dictionary
            resp.response = [Task(**x) for x in resp.response]
        return resp

    async def get_all_responses_for_task(self, task: Union[Task, Dict]) -> MythicResponse:
        """
        For the specified task, get all the responses
        :param task:
            if using the Task class, the following must be set:
                id
        :return:
        """
        url = "{}{}:{}/api/v{}/tasks/{}".format(
            self.http,
            self.server_ip,
            self.server_port,
            self.server_api_version,
            task.id if isinstance(task, Task) else task["id"],
        )
        resp = await self.get_json(url)
        if resp.response_code == 200:
            # update the response with APIToken objects instead of just a dictionary
            tsk = Task(**resp.response["task"])
            tsk.callback = Callback(**resp.response["callback"])
            tsk.responses = [Response(**x) for x in resp.response["responses"]]
            resp.response = tsk
        return resp

    async def get_all_tasks_and_responses_grouped_by_callback(self) -> MythicResponse:
        """
        Get all tasks and responses for all callbacks in the current operation
        :return:
        """
        url = "{}{}:{}/api/v{}/task_report_by_callback".format(
            self.http, self.server_ip, self.server_port, self.server_api_version
        )
        resp = await self.get_json(url)
        if resp.response_code == 200:
            # update the response with APIToken objects instead of just a dictionary
            resp.response = [Callback(**x) for x in resp.response["output"]]
        return resp

    async def create_task(
        self, task: Task, return_on="preprocessing", timeout=None
    ) -> MythicResponse:
        """
        Create a new task for a callback
        :param task:
            if using the Task class, the following must be set:
                callback: id
                command: cmd
                params
        :return:
        """
        url = "{}{}:{}/api/v{}/tasks/callback/{}".format(
            self.http,
            self.server_ip,
            self.server_port,
            self.server_api_version,
            task.callback.id if isinstance(task, Task) else task["callback"],
        )
        headers = self.get_headers()
        if task.files is None:
            data = {"command": task.command.cmd}
            if isinstance(task.params, str):
                data["params"] = task.params
            else:
                data["params"] = json.dumps(task.params)
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url, json=data, headers=headers, ssl=False
                    ) as resp:
                        resp = MythicResponse(
                            response_code=resp.status, raw_response=await resp.json()
                        )
            except OSError as o:
                return MythicResponse(
                    response_code=0, raw_response={"status": "error", "error": str(o)}
                )
            except Exception as e:
                return MythicResponse(
                    response_code=0, raw_response={"status": "error", "error": str(e)}
                )
        else:
            form = aiohttp.FormData()
            data = {"command": task.command.cmd, "params": task.params}
            for f in task.files:
                data["params"][f.param_name] = "FILEUPLOAD"
                form.add_field("file" + f.param_name, f.content, filename=f.filename)
            data["params"] = json.dumps(data["params"])
            form.add_field("json", json.dumps(data))
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url, data=form, headers=headers, ssl=False
                    ) as resp:
                        resp = MythicResponse(
                            response_code=resp.status, raw_response=await resp.json()
                        )
            except OSError as o:
                return MythicResponse(
                    response_code=0, raw_response={"status": "error", "error": str(o)}
                )
            except Exception as e:
                return MythicResponse(
                    response_code=0, raw_response={"status": "error", "error": str(e)}
                )
        if resp.response_code == 200 and resp.status == "success":
            resp.response = Task(**resp.response)
            if return_on == "preprocessing":
                return resp.response
            else:
                # we need to loop and wait for the status of the task to change
                resp.response = await self.wait_for_task_status_change(
                    resp.response.id, return_on, timeout
                )
        return resp

    async def set_comment_on_task(self, task: Task) -> MythicResponse:
        """
        Get all of the credentials associated with the user's current operation
        :return:
        """
        url = "{}{}:{}/api/v{}/tasks/comments/{}".format(
            self.http,
            self.server_ip,
            self.server_port,
            self.server_api_version,
            task.id,
        )
        if task.comment == "" or task.comment is None:
            resp = await self.delete_json(url)
        else:
            resp = await self.post_json(url, data={"comment": task.comment})
        if resp.response_code == 200:
            # update the response with APIToken objects instead of just a dictionary
            resp.response = Task(**resp.response["task"])
        return resp

    # ============== CREDENTIAL ENDPOINTS ========================

    async def get_all_credentials(self) -> MythicResponse:
        """
        Get all of the credentials associated with the user's current operation
        :return:
        """
        url = "{}{}:{}/api/v{}/credentials/current_operation".format(
            self.http, self.server_ip, self.server_port, self.server_api_version
        )
        resp = await self.get_json(url)
        if resp.response_code == 200:
            # update the response with APIToken objects instead of just a dictionary
            resp.response = [Credential(**x) for x in resp.response["credentials"]]
        return resp

    async def create_credential(self, credential: Credential) -> MythicResponse:
        """
        Create a new credential associated with the user's current operation
        :return:
        """
        url = "{}{}:{}/api/v{}/credentials".format(
            self.http, self.server_ip, self.server_port, self.server_api_version
        )
        resp = await self.post_json(url, data=await obj_to_json(credential))
        if resp.response_code == 200:
            # update the response with APIToken objects instead of just a dictionary
            resp.response = Credential(**resp.response)
        return resp

    async def update_credential(self, credential: Credential) -> MythicResponse:
        """
        Create a new credential associated with the user's current operation
        :return:
        """
        url = "{}{}:{}/api/v{}/credentials/{}".format(
            self.http,
            self.server_ip,
            self.server_port,
            self.server_api_version,
            str(credential.id),
        )
        resp = await self.put_json(url, data=await obj_to_json(credential))
        if resp.response_code == 200:
            # update the response with APIToken objects instead of just a dictionary
            resp.response = Credential(**resp.response)
        return resp

    # =============== CALLBACK ENDPOINTS =========================

    async def get_one_callback(self, callback: Callback) -> MythicResponse:
        """
        Get info about a single callback
        :return:
        """
        if callback.id is None:
            raise Exception("Callback id is None or < 0, should be number >= 1")
        url = "{}{}:{}/api/v{}/callbacks/{}".format(
            self.http,
            self.server_ip,
            self.server_port,
            self.server_api_version,
            str(callback.id),
        )
        resp = await self.get_json(url)
        if resp.response_code == 200 and resp.status == "success":
            resp.response = Callback(**resp.response)
        return resp

    async def get_all_callbacks(self) -> MythicResponse:
        """
        Get info about all callbacks
        :return:
        """
        url = "{}{}:{}/api/v{}/callbacks".format(
            self.http, self.server_ip, self.server_port, self.server_api_version
        )
        resp = await self.get_json(url)
        if resp.response_code == 200:
            resp.response = [Callback(**x) for x in resp.response]
        return resp

    # =============== DISABLED COMMANDS PROFILES ENDPOINTS =======

    async def get_all_disabled_commands_profiles(self) -> MythicResponse:
        """
        Get all of the disabled command profiles associated with Mythic
        :return:
        """
        url = "{}{}:{}/api/v{}/operations/disabled_commands_profiles".format(
            self.http, self.server_ip, self.server_port, self.server_api_version
        )
        resp = await self.get_json(url)
        if resp.response_code == 200:
            profile_entries = []
            for name, ptypes in resp.response["disabled_command_profiles"].items():
                new_entry = DisabledCommandsProfile(name=name, payload_types=[])
                for ptype, commands in ptypes.items():
                    payload_type = PayloadType(ptype=ptype, commands=[])
                    for command in commands:
                        payload_type.commands.append(
                            Command(cmd=command["command"], id=command["command_id"])
                        )
                    new_entry.payload_types.append(payload_type)
                profile_entries.append(new_entry)
            resp.response = profile_entries
        return resp

    async def create_disabled_commands_profile(
        self, profile: DisabledCommandsProfile
    ) -> MythicResponse:
        """
        Create a new disabled command profiles associated with Mythic
        :return:
        """
        url = "{}{}:{}/api/v{}/operations/disabled_commands_profile".format(
            self.http, self.server_ip, self.server_port, self.server_api_version
        )
        data = {profile.name: {}}
        for payload_type in profile.payload_types:
            data[profile.name][payload_type.ptype] = []
            for command in payload_type.commands:
                data[profile.name][payload_type.ptype].append(command.cmd)
        resp = await self.post_json(url, data=data)
        if resp.response_code == 200 and resp.status == "success":
            profile_entries = []
            for entry in resp.response["disabled_command_profile"]:
                # first check if we have a profile for this
                found = False
                for p in profile_entries:
                    if p.name == entry["name"]:
                        found = True
                        ptype_found = False
                        for payload_type in p.payload_types:
                            if payload_type.ptype == entry["payload_type"]:
                                ptype_found = True
                                payload_type.commands.append(
                                    Command(cmd=entry["command"], id=entry["command_id"])
                                )
                        if not ptype_found:
                            p.payload_types.append(
                                PayloadType(
                                    ptype=entry["payload_type"],
                                    commands=[
                                        Command(
                                            cmd=entry["command"], id=entry["command_id"]
                                        )
                                    ],
                                )
                            )
                if not found:
                    dcp = DisabledCommandsProfile(name=entry["name"], payload_types=[])
                    dcp.payload_types.append(
                        PayloadType(
                            ptype=entry["payload_type"],
                            commands=[
                                Command(cmd=entry["command"], id=entry["command_id"])
                            ],
                        )
                    )
                    profile_entries.append(dcp)
            resp.response = profile_entries
        return resp

    async def update_disabled_commands_profile(
        self, profile: DisabledCommandsProfile
    ) -> MythicResponse:
        """
        Create a new disabled command profiles associated with Mythic
        :return:
        """
        url = "{}{}:{}/api/v{}/operations/disabled_commands_profile".format(
            self.http, self.server_ip, self.server_port, self.server_api_version
        )
        data = {profile.name: {}}
        for payload_type in profile.payload_types:
            data[profile.name][payload_type.ptype] = []
            for command in payload_type.commands:
                data[profile.name][payload_type.ptype].append(command.cmd)
        resp = await self.put_json(url, data=data)
        if resp.response_code == 200 and resp.status == "success":
            profile_entries = []
            for entry in resp.response["disabled_command_profile"]:
                # first check if we have a profile for this
                found = False
                for p in profile_entries:
                    if p.name == entry["name"]:
                        found = True
                        ptype_found = False
                        for payload_type in p.payload_types:
                            if payload_type.ptype == entry["payload_type"]:
                                ptype_found = True
                                payload_type.commands.append(
                                    Command(cmd=entry["command"], id=entry["command_id"])
                                )
                        if not ptype_found:
                            p.payload_types.append(
                                PayloadType(
                                    ptype=entry["payload_type"],
                                    commands=[
                                        Command(
                                            cmd=entry["command"], id=entry["command_id"]
                                        )
                                    ],
                                )
                            )
                if not found:
                    dcp = DisabledCommandsProfile(name=entry["name"], payload_types=[])
                    dcp.payload_types.append(
                        PayloadType(
                            ptype=entry["payload_type"],
                            commands=[
                                Command(cmd=entry["command"], id=entry["command_id"])
                            ],
                        )
                    )
                    profile_entries.append(dcp)
            resp.response = profile_entries
        return resp

    async def update_disabled_commands_profile_for_operator(
        self,
        profile: Union[DisabledCommandsProfile, str],
        operator: Operator,
        operation: Operation,
    ) -> MythicResponse:
        # async def add_or_update_operator_for_operation(self, operation: Operation, operator: Operator)
        if isinstance(profile, DisabledCommandsProfile):
            operator.base_disabled_commands = profile.name
        else:
            operator.base_disabled_commands = profile
        resp = await self.add_or_update_operator_for_operation(operation, operator)
        return resp

    # =============== EVENT LOG MESSAGES ========================

    async def get_all_event_messages(self) -> MythicResponse:
        """
        Get all of the event messages associated with Mythic for the current operation that are not deleted
        :return:
        """
        url = "{}{}:{}/api/v{}/event_message".format(
            self.http, self.server_ip, self.server_port, self.server_api_version
        )
        resp = await self.get_json(url)
        if resp.response_code == 200 and resp.status == "success":
            resp.response = [EventMessage(**x) for x in resp.response["alerts"]]
        return resp

    async def create_event_message(self, message: EventMessage) -> MythicResponse:
        """
        Create new event message for the current operation
        :return:
        """
        url = "{}{}:{}/api/v{}/event_message".format(
            self.http, self.server_ip, self.server_port, self.server_api_version
        )
        resp = await self.post_json(url, data=await obj_to_json(message))
        if resp.response_code == 200 and resp.status == "success":
            resp.response = EventMessage(resp.response)
        return resp

    async def update_event_message(self, message: EventMessage) -> MythicResponse:
        """
        Update event message for the current operation
        :return:
        """
        url = "{}{}:{}/api/v{}/event_message/{}".format(
            self.http,
            self.server_ip,
            self.server_port,
            self.server_api_version,
            str(message.id),
        )
        resp = await self.put_json(url, data=await obj_to_json(message))
        if resp.response_code == 200 and resp.status == "success":
            resp.response = EventMessage(resp.response)
        return resp

    async def remove_event_message(self, message: EventMessage) -> MythicResponse:
        """
        Update event message for the current operation
        :return:
        """
        url = "{}{}:{}/api/v{}/event_message/delete".format(
            self.http, self.server_ip, self.server_port, self.server_api_version
        )
        resp = await self.post_json(url, data={"messages": [message.id]})
        if resp.response_code == 200 and resp.status == "success":
            resp.response = EventMessage(resp.response)
        return resp

    async def remove_event_messages(self, messages: List) -> MythicResponse:
        """
        Update event message for the current operation
        :return:
        """
        url = "{}{}:{}/api/v{}/event_message/delete".format(
            self.http, self.server_ip, self.server_port, self.server_api_version
        )
        msgs = [m.id for m in messages]
        resp = await self.post_json(url, data={"messages": msgs})
        if resp.response_code == 200 and resp.status == "success":
            resp.response = EventMessage(resp.response)
        return resp

    # ============= CUSTOM HELPER FUNCTIONS ======================

    async def login(self):
        """
        Login with username/password and store resulting access_token and refresh_token
        """
        url = "{}{}:{}/auth".format(self.http, self.server_ip, self.server_port)
        data = {
            "username": self.username,
            "password": self.password,
            "scripting_version": self.scripting_version,
        }
        print(
            "[*] Connecting to Mythic as scripting_version {}".format(
                self.scripting_version
            )
        )
        resp = await self.post_json(url, data)
        if resp.response_code == 200:
            if resp.status == "error":
                raise Exception("Failed to log in: " + resp.response["error"])
            self.access_token = resp.response["access_token"]
            self.refresh_token = resp.response["refresh_token"]
            return resp
        else:
            raise Exception(
                "Failed to log in: "
                + json.dumps(resp, indent=2, default=lambda o: o.to_json())
            )
            sys.exit(1)

    async def set_or_create_apitoken(self, token_type="User"):
        """
        Use current auth to check if there are any user tokens. Either get one or create a new user one
        """
        resp = await self.get_apitokens()
        if resp.status == "success":
            for x in resp.response:
                if x.token_type == token_type:
                    self._apitoken = x
                    resp.response = x
                    return resp
        # if we get here, then we don't have a token of the right type for us to just leverage, so we need to get one
        token_resp = await self.create_apitoken(token_type=token_type)
        if token_resp.response_code == 200:
            self._apitoken = token_resp.response
        return token_resp

    async def wait_for_task_status_change(self, task_id, status, timeout=None):
        """
        Uses websockets to listen for notifications related to the specified task within a certain period of time
        if self.timeout is -1, then wait indefinitely
        :param task_id:
        :param status: the status we're waiting for (error is always included)
        :return:
        """
        if timeout is None:
            timeout = self.global_timeout
        url = "{}{}:{}/ws/task/{}".format(
            self.ws, self.server_ip, self.server_port, str(task_id)
        )
        headers = self.get_headers()
        try:
            async with aiohttp.ClientSession() as session:
                ws = await session.ws_connect(url, headers=headers, ssl=False)
                start = time()
                while True:
                    try:
                        if timeout > 0 and (time() - start >= timeout):
                            raise Exception("wait_for_task_status_change has timed out")
                        msg = await ws.receive()
                        if msg.data is None:
                            return None
                        if msg.data != "":
                            task = Task(**json.loads(msg.data))
                            if (
                                task.status == "error"
                                or task.completed == True
                                or task.status.lower() == status.lower()
                            ):
                                return task
                    except Exception as e:
                        raise Exception(
                            "Exception while waiting for task status change: " + str(e)
                        )
        except Exception as e:
            raise Exception(
                "Exception in outer try/catch while waiting for task status change: "
                + str(e)
            )

    async def wait_for_payload_status_change(self, payload_uuid, status, timeout=None):
        """
        Uses websockets to listen for notifications related to the specified pyaload within a certain period of time
        if self.timeout is -1, then wait indefinitely
        :param payload_uuid:
        :param status: the status we're waiting for (error is always included)
        :return:
        """
        if timeout is None:
            timeout = self.global_timeout
        url = "{}{}:{}/ws/payloads/{}".format(
            self.ws, self.server_ip, self.server_port, str(payload_uuid)
        )
        headers = self.get_headers()
        try:
            async with aiohttp.ClientSession() as session:
                ws = await session.ws_connect(url, headers=headers, ssl=False)
                start = time()
                while True:
                    try:
                        if timeout > 0 and (time() - start >= timeout):
                            raise Exception(
                                "wait_for_payload_status_change has timed out"
                            )
                        msg = await ws.receive()
                        if msg.data is None:
                            return None
                        if msg.data != "":
                            payload = Payload(**json.loads(msg.data))
                            if (
                                payload.build_phase == "error"
                                or payload.deleted == True
                                or payload.build_phase == status
                            ):
                                return payload
                    except Exception as e:
                        raise Exception(
                            "Exception while waiting for payload status change: " + str(e)
                        )
        except Exception as e:
            raise Exception(
                "Exception in outer try/catch while waiting for payload status change: "
                + str(e)
            )

    # ============= WEBSOCKET NOTIFICATION FUNCTIONS ===============

    async def listen_for_all_notifications_on_one_callback(
        self, callback_id, callback_function=None, timeout=None, exception_handler=None
    ):
        """
        Uses websockets to listen for all notifications related to a specific callback and prints to the screen.
        To stop listening, call cancel() on the result from this function call
        :param callback_id:
        :param callback_function: gets called on each notification
        :return:
        """
        url = "{}{}:{}/ws/unified_callback/{}".format(
            self.ws, self.server_ip, self.server_port, str(callback_id)
        )
        if callback_function:
            task = await self.stream_output(
                url, callback_function, timeout, exception_handler
            )
        else:
            task = await self.stream_output(
                url, self.print_websocket_output, timeout, exception_handler
            )
        return task

    async def listen_for_new_callbacks(
        self, callback_function=None, timeout=None, exception_handler=None
    ):
        """
        Uses websockets to listen for all notifications related new callbacks.
        To stop listening, call cancel() on the result from this function call
        :param callback_function: gets called on each notification
        :return:
        """
        url = "{}{}:{}/ws/new_callbacks/current_operation".format(
            self.ws, self.server_ip, self.server_port
        )
        if callback_function:
            task = await self.stream_output(
                url, callback_function, timeout, exception_handler
            )
        else:
            task = await self.stream_output(
                url, self.print_websocket_output, timeout, exception_handler
            )
        return task

    async def listen_for_responses_for_task(
        self, task_id, callback_function=None, timeout=None, exception_handler=None
    ):
        """
        Uses websockets to listen for all responses on a given task
        To stop listening, call cancel() on the result from this function call
        :param callback_id:
        :param callback_function: gets called on each notification
        :return:
        """
        url = "{}{}:{}/ws/responses/by_task/{}".format(
            self.ws, self.server_ip, self.server_port, str(task_id)
        )
        if callback_function:
            task = await self.stream_output(
                url, callback_function, timeout, exception_handler
            )
        else:
            task = await self.stream_output(
                url, self.print_websocket_output, timeout, exception_handler
            )
        return task

    async def gather_task_responses(self, task_id, timeout=None) -> List:
        """
        Uses websockets to listen for all responses related to task_id and gather them together into an array until the task is completed or errored.
        :param callback_id:
        :param callback_function: gets called on each notification
        :return:
        """
        if timeout is None:
            timeout = self.global_timeout
        url = "{}{}:{}/ws/responses/by_task/{}".format(
            self.ws, self.server_ip, self.server_port, str(task_id)
        )
        headers = self.get_headers()
        responses = []
        try:
            async with aiohttp.ClientSession() as session:
                ws = await session.ws_connect(url, headers=headers, ssl=False)
                start = time()
                while True:
                    try:
                        if timeout > 0 and (time() - start >= timeout):
                            raise Exception("gather_task_responses has timed out")
                        msg = await ws.receive()
                        if msg.data is None:
                            return responses
                        if msg.data != "":
                            rsp = Response(**json.loads(msg.data))
                            # await json_print(rsp)
                            responses.append(rsp)
                            if rsp.task.status == "error" or rsp.task.completed == True:
                                return responses
                    except Exception as e:
                        raise Exception("Exception while gathering responses: " + str(e))
        except Exception as e:
            raise Exception(
                "Exception in our try/catch while gathering responses: " + str(e)
            )

    async def listen_for_all_files(
        self, callback_function=None, timeout=None, exception_handler=None
    ):
        """
        Uses websockets to listen for all file notifications within mythic for the current operation.
        This includes payloads, uploads, downloads, screenshots.
        :param callback_function: gets called on each notification
        :return:
        """
        url = "{}{}:{}/ws/files/current_operation".format(
            self.ws, self.server_ip, self.server_port
        )
        if callback_function:
            task = await self.stream_output(
                url, callback_function, timeout, exception_handler
            )
        else:
            task = await self.stream_output(
                url, self.print_websocket_output, timeout, exception_handler
            )
        return task

    async def listen_for_new_files(
        self, callback_function=None, timeout=None, exception_handler=None
    ):
        """
        Uses websockets to listen for all file notifications within mythic for the current operation.
        This includes uploads, downloads.
        :param callback_function: gets called on each notification
        :return:
        """
        url = "{}{}:{}/ws/files/new/current_operation".format(
            self.ws, self.server_ip, self.server_port
        )
        if callback_function:
            task = await self.stream_output(
                url, callback_function, timeout, exception_handler
            )
        else:
            task = await self.stream_output(
                url, self.print_websocket_output, timeout, exception_handler
            )
        return task

    async def listen_for_all_responses(
        self, callback_function=None, timeout=None, exception_handler=None
    ):
        """
        Uses websockets to listen for all response notifications within mythic for the current operation.
        :param callback_function: gets called on each notification
        :return:
        """
        url = "{}{}:{}/ws/responses/current_operation".format(
            self.ws, self.server_ip, self.server_port
        )
        if callback_function:
            task = await self.stream_output(
                url, callback_function, timeout, exception_handler
            )
        else:
            task = await self.stream_output(
                url, self.print_websocket_output, timeout, exception_handler
            )
        return task

    async def listen_for_new_responses(
        self, callback_function=None, timeout=None, exception_handler=None
    ):
        """
        Uses websockets to listen for all new response notifications within mythic for the current operation.
        :param callback_function: gets called on each notification
        :return:
        """
        url = "{}{}:{}/ws/responses/new/current_operation".format(
            self.ws, self.server_ip, self.server_port
        )
        if callback_function:
            task = await self.stream_output(
                url, callback_function, timeout, exception_handler
            )
        else:
            task = await self.stream_output(
                url, self.print_websocket_output, timeout, exception_handler
            )
        return task

    async def listen_for_all_tasks(
        self, callback_function=None, timeout=None, exception_handler=None
    ):
        """
        Uses websockets to listen for all tasks within mythic for the current operation.
        :param callback_function: gets called on each notification
        :return:
        """
        url = "{}{}:{}/ws/tasks/current_operation".format(
            self.ws, self.server_ip, self.server_port
        )
        if callback_function:
            task = await self.stream_output(
                url, callback_function, timeout, exception_handler
            )
        else:
            task = await self.stream_output(
                url, self.print_websocket_output, timeout, exception_handler
            )
        return task

    async def listen_for_new_tasks(
        self, callback_function=None, timeout=None, exception_handler=None
    ):
        """
        Uses websockets to listen for all new tasks within mythic for the current operation.
        :param callback_function: gets called on each notification
        :return:
        """
        url = "{}{}:{}/ws/tasks/new/current_operation".format(
            self.ws, self.server_ip, self.server_port
        )
        if callback_function:
            task = await self.stream_output(
                url, callback_function, timeout, exception_handler
            )
        else:
            task = await self.stream_output(
                url, self.print_websocket_output, timeout, exception_handler
            )
        return task

    async def listen_for_all_payloads(
        self, callback_function=None, timeout=None, exception_handler=None
    ):
        """
        Uses websockets to listen for all payloads within mythic for the current operation.
        :param callback_function: gets called on each notification
        :return:
        """
        url = "{}{}:{}/ws/payloads/info/current_operation".format(
            self.ws, self.server_ip, self.server_port
        )
        if callback_function:
            task = await self.stream_output(
                url, callback_function, timeout, exception_handler
            )
        else:
            task = await self.stream_output(
                url, self.print_websocket_output, timeout, exception_handler
            )
        return task

    async def listen_for_all_credentials(
        self, callback_function=None, timeout=None, exception_handler=None
    ):
        """
        Uses websockets to listen for credentials within mythic for the current operation.
        :param callback_function: gets called on each notification
        :return:
        """
        url = "{}{}:{}/ws/credentials/current_operation".format(
            self.ws, self.server_ip, self.server_port
        )
        if callback_function:
            task = await self.stream_output(
                url, callback_function, timeout, exception_handler
            )
        else:
            task = await self.stream_output(
                url, self.print_websocket_output, timeout, exception_handler
            )
        return task

    async def listen_for_new_credentials(
        self, callback_function=None, timeout=None, exception_handler=None
    ):
        """
        Uses websockets to listen for new credentials within mythic for the current operation.
        :param callback_function: gets called on each notification
        :return:
        """
        url = "{}{}:{}/ws/credentials/new/current_operation".format(
            self.ws, self.server_ip, self.server_port
        )
        if callback_function:
            task = await self.stream_output(
                url, callback_function, timeout, exception_handler
            )
        else:
            task = await self.stream_output(
                url, self.print_websocket_output, timeout, exception_handler
            )
        return task

    async def listen_for_all_event_messages(
        self, callback_function=None, timeout=None, exception_handler=None
    ):
        """
        Uses websockets to listen for event messages within mythic for the current operation.
        :param callback_function: gets called on each notification
        :return:
        """
        url = "{}{}:{}/ws/events_all/current_operation".format(
            self.ws, self.server_ip, self.server_port
        )
        if callback_function:
            task = await self.stream_output(
                url, callback_function, timeout, exception_handler
            )
        else:
            task = await self.stream_output(
                url, self.print_websocket_output, timeout, exception_handler
            )
        return task

    async def listen_for_new_event_messages(
        self, callback_function=None, timeout=None, exception_handler=None
    ):
        """
        Uses websockets to listen for new event messages within mythic for the current operation.
        :param callback_function: gets called on each notification
        :return:
        """
        url = "{}{}:{}/ws/events_notifier/current_operation".format(
            self.ws, self.server_ip, self.server_port
        )
        if callback_function:
            task = await self.stream_output(
                url, callback_function, timeout, exception_handler
            )
        else:
            task = await self.stream_output(
                url, self.print_websocket_output, timeout, exception_handler
            )
        return task
