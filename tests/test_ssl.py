import ssl

import pytest
from mythic import mythic_classes, mythic_utilities

CA_FILE = "/path/to/mythic-ca.pem"


def make_mythic(**kwargs):
    return mythic_classes.Mythic(server_ip="mythic.example", server_port=7443, apitoken="token", **kwargs)


def test_plain_http_has_no_tls():
    instance = make_mythic(ssl=False, verify_ssl=True)
    assert mythic_utilities.get_ssl(instance) is False
    assert mythic_utilities.get_ssl(instance, websocket=True) is False


def test_default_keeps_unverified_behaviour():
    instance = make_mythic(ssl=True)
    assert instance.verify_ssl is False
    assert mythic_utilities.get_ssl(instance) is False
    websocket_context = mythic_utilities.get_ssl(instance, websocket=True)
    assert websocket_context.verify_mode == ssl.CERT_NONE
    assert websocket_context.check_hostname is False


def test_verify_ssl_uses_system_trust_store():
    context = mythic_utilities.get_ssl(make_mythic(ssl=True, verify_ssl=True))
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True


def test_ssl_ca_file_is_used_when_verifying(monkeypatch):
    seen = []
    real = ssl.create_default_context

    def create(*args, **kwargs):
        seen.append(kwargs.get("cafile"))
        return real()

    monkeypatch.setattr(mythic_utilities.ssl, "create_default_context", create)
    context = mythic_utilities.get_ssl(make_mythic(ssl=True, verify_ssl=True, ssl_ca_file=CA_FILE))
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert seen == [CA_FILE]


def test_ssl_ca_file_ignored_without_verify_ssl():
    assert mythic_utilities.get_ssl(make_mythic(ssl=True, ssl_ca_file=CA_FILE)) is False


def test_invalid_ssl_ca_file_raises(tmp_path):
    bad = tmp_path / "bad.pem"
    bad.write_text("not a certificate")
    with pytest.raises(ssl.SSLError):
        mythic_utilities.get_ssl(make_mythic(ssl=True, verify_ssl=True, ssl_ca_file=str(bad)))


async def test_transports_use_get_ssl():
    instance = make_mythic(ssl=True, verify_ssl=True)
    http_transport = await mythic_utilities.get_http_transport(instance)
    ws_transport = await mythic_utilities.get_ws_transport(instance)
    assert http_transport.ssl.verify_mode == ssl.CERT_REQUIRED
    assert ws_transport.ssl.verify_mode == ssl.CERT_REQUIRED
