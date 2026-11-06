import unittest
import uuid
from httpx import ASGITransport, AsyncClient
from app.database import async_engine
from app.main import app


class TestAuthAPI(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self):
        await async_engine.dispose()

    async def test_complete_auth_and_multitenancy_flow(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            unique_id = uuid.uuid4().hex[:8]
            email_a = f"admin_a_{unique_id}@tenant-a.com"
            email_b = f"admin_b_{unique_id}@tenant-b.com"
            password = "SecurePassword123!"

            # 1. Register Tenant A
            res_reg_a = await client.post(
                "/auth/register",
                json={
                    "tenant_name": f"Tenant Alpha {unique_id}",
                    "email": email_a,
                    "password": password,
                    "role": "admin",
                },
            )
            self.assertEqual(res_reg_a.status_code, 201)
            data_reg_a = res_reg_a.json()
            token_a = data_reg_a["access_token"]
            tenant_id_a = data_reg_a["tenant_id"]
            user_id_a = data_reg_a["user_id"]
            self.assertIsNotNone(token_a)

            # 2. Login as Tenant A
            res_login_a = await client.post(
                "/auth/login",
                json={"email": email_a, "password": password},
            )
            self.assertEqual(res_login_a.status_code, 200)
            data_login_a = res_login_a.json()
            self.assertEqual(data_login_a["tenant_id"], tenant_id_a)
            self.assertEqual(data_login_a["user_id"], user_id_a)

            # 3. Access /auth/me with Tenant A token
            res_me_a = await client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {token_a}"},
            )
            self.assertEqual(res_me_a.status_code, 200)
            data_me_a = res_me_a.json()
            self.assertEqual(data_me_a["id"], user_id_a)
            self.assertEqual(data_me_a["tenant_id"], tenant_id_a)

            # 4. Register Tenant B
            res_reg_b = await client.post(
                "/auth/register",
                json={
                    "tenant_name": f"Tenant Beta {unique_id}",
                    "email": email_b,
                    "password": password,
                    "role": "admin",
                },
            )
            self.assertEqual(res_reg_b.status_code, 201)
            data_reg_b = res_reg_b.json()
            tenant_id_b = data_reg_b["tenant_id"]

            # 5. Verify Multi-Tenancy Isolation (Tenant A != Tenant B)
            self.assertNotEqual(tenant_id_a, tenant_id_b)

            # 6. Duplicate Email Registration Conflict
            res_dup = await client.post(
                "/auth/register",
                json={
                    "tenant_name": "Conflict Corp",
                    "email": email_a,
                    "password": password,
                },
            )
            self.assertEqual(res_dup.status_code, 409)

            # 7. Invalid Credentials
            res_bad_login = await client.post(
                "/auth/login",
                json={"email": email_a, "password": "WrongPassword!"},
            )
            self.assertEqual(res_bad_login.status_code, 401)


if __name__ == "__main__":
    unittest.main()

