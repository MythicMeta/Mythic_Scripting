from os import path, remove

import pytest
from mythic import mythic, mythic_classes


def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow network tests"
    )
    parser.addoption(
        "--server-ip",
        action="store",
        default="192.168.53.139",
        help="specify the IP address of Mythic to use",
    )
    parser.addoption(
        "--admin-username",
        action="store",
        default="mythic_admin",
        help="specify the mythic admin username",
    )
    parser.addoption(
        "--admin-password",
        action="store",
        default="mythic_password",
        help="specify the password for the admin user",
    )
    parser.addoption(
        "--apitoken",
        action="store",
        default=None,
        help="specify an apitoken to use for requests",
    )
    parser.addoption(
        "--server-port", action="store", default=7443, help="specify port for mythic"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow network test to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # -- runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture
async def blank_mythic_instance():
    return mythic_classes.Mythic()


@pytest.fixture
async def authenticated_valid_mythic_instance(request):
    mythic_instance = await mythic.login(
        username=request.config.getoption("--admin-username"),
        password=request.config.getoption("--admin-password"),
        server_ip=request.config.getoption("--server-ip"),
        apitoken=request.config.getoption("--apitoken"),
        server_port=request.config.getoption("--server-port"),
    )
    yield mythic_instance
    if path.exists("mythic_schema.graphql"):
        remove("mythic_schema.graphql")


@pytest.fixture
async def invalid_apitoken_mythic_instance(request):
    return mythic_classes.Mythic(
        username=request.config.getoption("--admin-username"),
        password=request.config.getoption("--admin-password"),
        server_ip=request.config.getoption("--server-ip"),
        server_port=request.config.getoption("--server-port"),
        apitoken="test",
    )


@pytest.fixture
async def valid_no_login_mythic_instance(request):
    return mythic_classes.Mythic(
        username=request.config.getoption("--admin-username"),
        password=request.config.getoption("--admin-password"),
        server_ip=request.config.getoption("--server-ip"),
        server_port=request.config.getoption("--server-port"),
    )


@pytest.fixture
async def bad_graphql_method():
    return """
    qeury GetAPITokens {
        apitokens(where: {active: {_eq: true}}) {
            token_value
            active
            id
        }
    }
    """


@pytest.fixture
async def bad_graphql_query_root():
    return """
    query GetAPITokens {
        apitoken(where: {active: {_eq: true}}) {
            token_value
            active
            id
        }
    }"""


@pytest.fixture
async def bad_graphql_attribute():
    return """
    query GetAPITokens {
        apitokens(where: {active: {_eq: true}}) {
            token_value_bad
            active
            id
        }
    }"""
