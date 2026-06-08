def test_widget_config_js(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "widget_embed_api_key", "test-embed-key")
    response = client.get("/widget/config.js")
    assert response.status_code == 200
    assert "test-embed-key" in response.text
    assert "window.__SUPPORT_API_KEY__" in response.text
