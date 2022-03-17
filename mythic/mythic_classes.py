import json


class Mythic:
    def __init__(
        self,
        username: str = None,
        password: str = None,
        apitoken: str = None,
        access_token: str = None,
        refresh_token: str = None,
        server_ip: str = None,
        ssl: bool = False,
        server_port: int = None,
        server_api_version: float = 1.4,
        global_timeout: int = None,
        schema: str = None,
    ):
        self.username = username
        self.password = password
        self.apitoken = apitoken
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.server_ip = server_ip
        self.server_port = server_port
        self.server_api_version = server_api_version
        self.ssl = ssl
        self.http = "http://" if not ssl else "https://"
        self.ws = "ws://" if not ssl else "wss://"
        self.global_timeout = global_timeout if global_timeout is not None else -1
        self.scripting_version = 3
        self.current_operation_id = 0
        self.operator_id = None
        self.operator = None
        self.schema = schema

    def __str__(self):
        return json.dumps(
            {
                "username": self.username,
                "password": self.password,
                "apitoken": self.apitoken,
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "server_ip": self.server_ip,
                "server_port": self.server_port,
                "ssl": self.ssl,
                "current_operation_id": self.current_operation_id,
                "operator": self.operator,
                "operator_id": self.operator_id,
            },
            indent=4,
        )


class MythicStatus:
    Error = "error"
    Completed = "completed"
    Processed = "processed"
    Processing = "processing"
    Preprocessing = "preprocessing"
    Delegating = "delegating"
    Submitted = "submitted"

    def __init__(self, status: str):
        self.status = status

    def __str__(self):
        return self.status

    def __eq__(self, obj):
        # override == operator
        if isinstance(obj, str):
            return self.status == obj
        elif isinstance(obj, MythicStatus):
            return self.status == obj.status
        else:
            return False

    def __ge__(self, obj):
        # override >= operator
        # self.status is lefthand side, obj is right hand side
        target_obj = obj.status.lower() if isinstance(obj, MythicStatus) else obj.lower()
        if "delegating" in target_obj:
            target_obj = "delegating"
        elif "error" in target_obj:
            target_obj = "error"
        self_obj = self.status.lower()
        if "delegating" in self_obj:
            self_obj = "delegating"
        if "error" in self_obj:
            # all errors are >= other steps in the status line
            return True
        elif MythicStatus.Completed == self_obj:
            # completed status is >= all other steps in line
            return True
        enum_mapping = {
            "preprocessing": 0,
            "submitted": 1,
            "delegating": 2,
            "processing": 3,
            "processed": 4,
            "completed": 5,
            "error": 6,
        }
        if target_obj not in enum_mapping:
            raise ValueError(f"Can't compare status of type: {target_obj}")
        elif self_obj not in enum_mapping:
            raise ValueError(f"Can't compare status of type: {self_obj}")
        else:
            return enum_mapping[self_obj] >= enum_mapping[target_obj]
