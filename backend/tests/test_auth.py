import uuid

import jwt as pyjwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.config import settings
from app.main import app
from app.models.user import User
from tests.conftest import db_session_factory

client = TestClient(app)


def make_payload() -> dict:
    """每次调用生成唯一用户数据，避免历史残留数据导致冲突"""
    suffix = uuid.uuid4().hex[:8]
    return {
        "email": f"u{suffix}@test.dev",
        "username": f"u{suffix}",
        "password": "passw0rd123",
    }


@pytest.fixture(autouse=True)
async def cleanup_users():
    yield
    # 测试数据统一以 @test.dev 结尾，结束后清理本批用户
    async with db_session_factory() as session:
        await session.execute(delete(User).where(User.email.like("%@test.dev")))
        await session.commit()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_register_success():
    payload = make_payload()
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == payload["email"]
    assert data["username"] == payload["username"]
    assert data["id"] > 0
    # 响应体绝不能泄漏哈希
    assert "password_hash" not in data
    assert "password" not in data


def test_register_duplicate_email():
    payload = make_payload()
    client.post("/auth/register", json=payload)
    second = make_payload()
    second["email"] = payload["email"]
    resp = client.post("/auth/register", json=second)
    assert resp.status_code == 409


def test_register_duplicate_username():
    payload = make_payload()
    client.post("/auth/register", json=payload)
    second = make_payload()
    second["username"] = payload["username"]
    resp = client.post("/auth/register", json=second)
    assert resp.status_code == 409


def test_register_short_password_rejected():
    payload = make_payload()
    payload["password"] = "short"
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 422


def test_login_success_returns_valid_jwt():
    payload = make_payload()
    client.post("/auth/register", json=payload)
    resp = client.post(
        "/auth/login", json={"email": payload["email"], "password": payload["password"]}
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    # 用服务端密钥解码验证签名与 claims
    decoded = pyjwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert decoded["sub"]


def test_login_wrong_password():
    payload = make_payload()
    client.post("/auth/register", json=payload)
    resp = client.post(
        "/auth/login", json={"email": payload["email"], "password": "wrong-password"}
    )
    assert resp.status_code == 401


def test_login_unknown_email():
    resp = client.post("/auth/login", json={"email": "nobody@test.dev", "password": "passw0rd123"})
    assert resp.status_code == 401


def test_register_normalizes_email_and_username_case():
    payload = make_payload()
    payload["email"] = payload["email"].upper()
    payload["username"] = payload["username"].upper()
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 201
    assert resp.json()["email"] == payload["email"].lower()
    assert resp.json()["username"] == payload["username"].lower()
    # 同一邮箱换大小写注册应冲突
    dup = make_payload()
    dup["email"] = payload["email"].lower()
    assert client.post("/auth/register", json=dup).status_code == 409


def test_login_overlong_password_rejected_not_500():
    # bcrypt 5.0 对超 72 字节输入抛 ValueError，schema 层必须拦住（422）而不是 500
    payload = make_payload()
    client.post("/auth/register", json=payload)
    resp = client.post(
        "/auth/login", json={"email": payload["email"], "password": "x" * 80}
    )
    assert resp.status_code == 422


def test_me_with_valid_token():
    payload = make_payload()
    client.post("/auth/register", json=payload)
    token = client.post(
        "/auth/login", json={"email": payload["email"], "password": payload["password"]}
    ).json()["access_token"]
    resp = client.get("/auth/me", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["username"] == payload["username"]


def test_me_without_token():
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_with_invalid_token():
    resp = client.get("/auth/me", headers=auth_headers("not-a-jwt"))
    assert resp.status_code == 401
