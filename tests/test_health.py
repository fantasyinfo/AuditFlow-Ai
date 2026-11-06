import unittest
from httpx import ASGITransport, AsyncClient
from app.database import async_engine
from app.main import app


class TestHealthEndpoints(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self):
        await async_engine.dispose()

    async def test_root_endpoint(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("AuditFlow AI API is running", data["message"])


if __name__ == "__main__":
    unittest.main()
