from time import time

import pytest
from mythic import mythic, mythic_utilities


class ClosableSubscription:
    def __init__(self, result):
        self.result = result
        self.closed = False
        self.yielded = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.yielded:
            raise StopAsyncIteration
        self.yielded = True
        return self.result

    async def aclose(self):
        self.closed = True


async def test_no_query_for_graphql_post(blank_mythic_instance):
    with pytest.raises(Exception):
        await mythic_utilities.graphql_post(mythic=blank_mythic_instance)


async def test_waitfor_task_complete_closes_subscription(monkeypatch):
    task = {"status": "completed", "completed": True}
    subscription = ClosableSubscription({"task_stream": [task]})
    monkeypatch.setattr(
        mythic_utilities, "graphql_subscription", lambda **kwargs: subscription
    )

    result = await mythic.waitfor_task_complete(mythic=None, task_display_id=1)

    assert result == task
    assert subscription.closed


async def test_waitfor_payload_complete_closes_subscription(monkeypatch):
    payload = {"build_phase": "success"}
    subscription = ClosableSubscription({"payload": [payload]})
    monkeypatch.setattr(
        mythic_utilities, "graphql_subscription", lambda **kwargs: subscription
    )

    result = await mythic.waitfor_payload_complete(mythic=None, payload_uuid="uuid")

    assert result == payload
    assert subscription.closed


async def test_waitfor_task_output_closes_subscription(monkeypatch):
    subscription = ClosableSubscription(
        {"task_stream": [{"status": "completed", "completed": True, "responses": []}]}
    )
    monkeypatch.setattr(
        mythic_utilities, "graphql_subscription", lambda **kwargs: subscription
    )

    async def get_no_subtasks(**kwargs):
        return []

    monkeypatch.setattr(mythic, "get_all_subtask_ids", get_no_subtasks)

    result = await mythic.waitfor_for_task_output(mythic=None, task_display_id=1)

    assert result == b""
    assert subscription.closed


async def test_bad_graphql_method(
    bad_graphql_method, authenticated_valid_mythic_instance
):
    with pytest.raises(TypeError):
        await mythic_utilities.graphql_post(
            mythic=authenticated_valid_mythic_instance, gql_query=bad_graphql_method
        )


async def test_bad_graphql_query_root(
    bad_graphql_query_root, authenticated_valid_mythic_instance
):
    with pytest.raises(TypeError):
        await mythic_utilities.graphql_post(
            mythic=authenticated_valid_mythic_instance, gql_query=bad_graphql_query_root
        )


async def test_bad_graphql_attribute(
    bad_graphql_attribute, authenticated_valid_mythic_instance
):
    with pytest.raises(TypeError):
        await mythic_utilities.graphql_post(
            mythic=authenticated_valid_mythic_instance, gql_query=bad_graphql_attribute
        )


async def test_get_schema(authenticated_valid_mythic_instance):
    with pytest.raises(AssertionError):
        # AssertionError from gql: Cannot fetch the schema from transport if it is already provided
        await mythic_utilities.fetch_graphql_schema(
            mythic=authenticated_valid_mythic_instance
        )


async def test_load_local_schema_fetch_valid(valid_no_login_mythic_instance):
    assert not await mythic_utilities.load_mythic_schema(
        mythic=valid_no_login_mythic_instance
    )


async def test_load_local_schema_fetch_already_logged_in(
    authenticated_valid_mythic_instance,
):
    assert await mythic_utilities.load_mythic_schema(
        mythic=authenticated_valid_mythic_instance
    )


async def test_query_bad_variable_type(authenticated_valid_mythic_instance):
    custom_query = """
    query GetAPITokens($id: Int!) {
        apitokens(where: {id: {_eq: $id}}) {
            token_value
            active
            id
        }
    }
    """
    with pytest.raises(Exception):
        await mythic_utilities.graphql_post(
            mythic=authenticated_valid_mythic_instance,
            query=custom_query,
            variables={"id": []},
        )


async def test_query_missing_variable(authenticated_valid_mythic_instance):
    custom_query = """
    query GetAPITokens($id: Int!) {
        apitokens(where: {id: {_eq: $id}}) {
            token_value
            active
            id
        }
    }
    """
    with pytest.raises(Exception):
        await mythic_utilities.graphql_post(
            mythic=authenticated_valid_mythic_instance,
            query=custom_query,
            variables={"bob": []},
        )


async def test_load_local_schema_fetch_invalid(invalid_apitoken_mythic_instance):
    assert not await mythic_utilities.load_mythic_schema(
        mythic=invalid_apitoken_mythic_instance
    )


@pytest.mark.slow
async def test_graphql_subscription_timeout(authenticated_valid_mythic_instance):
    custom_query = """
    subscription getOperations {
        operation {
            id
        }
    }
    """
    start = time()
    async for result in mythic_utilities.graphql_subscription(
        mythic=authenticated_valid_mythic_instance, query=custom_query, timeout=5
    ):
        pass
    assert time() - start < 7
