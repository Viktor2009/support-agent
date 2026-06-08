from app.config import parse_api_keys, parse_cors_origins
from app.observability import graph_invoke_config


def test_parse_api_keys():
    legacy = parse_api_keys("cust_456:key1,cust_789:key2")
    assert legacy == {
        "key1": ("default", "cust_456"),
        "key2": ("default", "cust_789"),
    }
    tenant = parse_api_keys("acme:cust_acme:acme-key")
    assert tenant == {"acme-key": ("acme", "cust_acme")}


def test_parse_cors_origins_wildcard():
    assert parse_cors_origins("*") == ["*"]


def test_parse_cors_origins_list():
    assert parse_cors_origins("http://a.com, http://b.com") == [
        "http://a.com",
        "http://b.com",
    ]


def test_graph_invoke_config_includes_thread_id():
    config = graph_invoke_config("session-xyz")
    assert config["configurable"]["thread_id"] == "session-xyz"
