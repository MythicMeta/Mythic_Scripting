import pytest
from aiohttp.client_exceptions import ClientConnectionError, InvalidURL
from mythic import mythic, mythic_classes


async def test_get_me_not_logged_in(blank_mythic_instance):
    with pytest.raises(InvalidURL):
        await mythic.get_me(mythic=blank_mythic_instance)


async def test_log_in(valid_no_login_mythic_instance):
    mythic_instance = await mythic.login(
        username=valid_no_login_mythic_instance.username,
        password=valid_no_login_mythic_instance.password,
        server_ip=valid_no_login_mythic_instance.server_ip,
        server_port=valid_no_login_mythic_instance.server_port,
    )
    assert mythic_instance.access_token is not None
    assert mythic_instance.apitoken is None


async def test_get_me(authenticated_valid_mythic_instance):
    me = await mythic.get_me(mythic=authenticated_valid_mythic_instance)
    assert "whoami" in me and me["whoami"]["user_id"] is not None


async def test_get_me_uses_whoami_action(monkeypatch):
    async def fake_execute_custom_query(mythic, query, variables=None):
        assert "whoami" in query
        assert "meHook" not in query
        return {"whoami": {"status": "success", "user_id": 1}}

    monkeypatch.setattr(mythic, "execute_custom_query", fake_execute_custom_query)
    me = await mythic.get_me(mythic=mythic_classes.Mythic())

    assert me["whoami"]["user_id"] == 1


async def test_set_password_returns_update_password_and_email(monkeypatch):
    async def fake_execute_custom_query(mythic, query, variables=None):
        if "query getUserID" in query:
            return {"operator": [{"id": 7}]}
        assert "updatePasswordAndEmail" in query
        assert variables["user_id"] == 7
        return {"updatePasswordAndEmail": {"status": "success", "error": None}}

    monkeypatch.setattr(mythic, "execute_custom_query", fake_execute_custom_query)

    response = await mythic.set_password(
        mythic=mythic_classes.Mythic(),
        username="mythic_admin",
        new_password="new_password",
    )

    assert response == {"status": "success", "error": None}


async def test_register_file_uses_current_upload_route(monkeypatch):
    captured = {}

    async def fake_http_post_form(mythic, data, url):
        captured["url"] = url
        return {"status": "success", "agent_file_id": "file-id"}

    monkeypatch.setattr(mythic.mythic_utilities, "http_post_form", fake_http_post_form)
    client = mythic_classes.Mythic(server_ip="127.0.0.1", server_port=7443, ssl=True)

    file_id = await mythic.register_file(
        mythic=client,
        filename="payload.bin",
        contents=b"payload",
    )

    assert file_id == "file-id"
    assert captured["url"] == "https://127.0.0.1:7443/task_upload_file_webhook"


async def test_get_command_parameter_options_groups_and_orders_parameters(monkeypatch):
    captured = {}

    async def fake_graphql_post(mythic, query, variables):
        captured["query"] = query
        captured["variables"] = variables
        return {
            "command": [{"id": 7}],
            "commandparameters": [
                {
                    "id": 3,
                    "name": "credential",
                    "parameter_group_name": "Default",
                    "type": "CredentialJson",
                    "ui_position": 2,
                },
                {
                    "id": 4,
                    "name": "edge",
                    "parameter_group_name": "Remove",
                    "type": "LinkInfo",
                    "ui_position": 1,
                },
                {
                    "id": 2,
                    "name": "connection",
                    "parameter_group_name": "Default",
                    "type": "AgentConnect",
                    "ui_position": 1,
                },
                {
                    "id": 1,
                    "name": "note",
                    "parameter_group_name": "Default",
                    "type": "String",
                    "ui_position": 1,
                },
            ],
        }

    monkeypatch.setattr(mythic.mythic_utilities, "graphql_post", fake_graphql_post)

    result = await mythic.get_command_parameter_options(
        mythic=mythic_classes.Mythic(),
        payload_type_name="poseidon",
        command_name="link",
    )

    assert captured["variables"] == {
        "command_name": "link",
        "payload_type_name": "poseidon",
    }
    assert "deleted: {_eq: false}" in captured["query"]
    assert "limit_credentials_by_type" in captured["query"]
    assert list(result) == ["Default", "Remove"]
    assert [parameter["id"] for parameter in result["Default"]] == [1, 2, 3]
    assert "LLM_Help" not in result["Default"][0]
    assert "@link:callback=" in result["Default"][1]["LLM_Help"]
    assert "@link:payload=" in result["Default"][1]["LLM_Help"]
    assert "@cred:<credential_id>" in result["Default"][2]["LLM_Help"]
    assert "@link:edge=" in result["Remove"][0]["LLM_Help"]


async def test_get_command_parameter_options_handles_parameterless_command(monkeypatch):
    async def fake_graphql_post(mythic, query, variables):
        return {"command": [{"id": 7}], "commandparameters": []}

    monkeypatch.setattr(mythic.mythic_utilities, "graphql_post", fake_graphql_post)

    result = await mythic.get_command_parameter_options(
        mythic=mythic_classes.Mythic(),
        payload_type_name="poseidon",
        command_name="exit",
    )

    assert result == {"Default": []}


async def test_get_command_parameter_options_rejects_unknown_command(monkeypatch):
    async def fake_graphql_post(mythic, query, variables):
        return {"command": [], "commandparameters": []}

    monkeypatch.setattr(mythic.mythic_utilities, "graphql_post", fake_graphql_post)

    with pytest.raises(Exception, match="missing.*poseidon"):
        await mythic.get_command_parameter_options(
            mythic=mythic_classes.Mythic(),
            payload_type_name="poseidon",
            command_name="missing",
        )


@pytest.mark.slow
async def test_connect_error():
    with pytest.raises(ClientConnectionError):
        await mythic.login(
            username="bob",
            password="bob",
            server_ip="192.168.53.140",
            server_port=7443,
        )
