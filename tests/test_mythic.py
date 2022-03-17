import pytest
from aiohttp.client_exceptions import ClientConnectionError, InvalidURL
from mythic import mythic


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
    assert mythic_instance.apitoken is not None


async def test_get_me(authenticated_valid_mythic_instance):
    me = await mythic.get_me(mythic=authenticated_valid_mythic_instance)
    assert "me" in me and me["me"]["user_id"] is not None


@pytest.mark.slow
async def test_connect_error():
    with pytest.raises(ClientConnectionError):
        await mythic.login(
            username="bob",
            password="bob",
            server_ip="192.168.53.140",
            server_port=7443,
        )
