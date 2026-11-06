import unittest
import uuid
from app.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class TestAuthSecurity(unittest.TestCase):
    def test_password_hashing_and_verification(self):
        raw_password = "SuperSecretPassword123!"
        hashed = hash_password(raw_password)

        self.assertNotEqual(hashed, raw_password)
        self.assertTrue(hashed.startswith("$2b$") or hashed.startswith("$2a$"))

        self.assertTrue(verify_password(raw_password, hashed))
        self.assertFalse(verify_password("WrongPassword!", hashed))
        self.assertFalse(verify_password("", hashed))

    def test_jwt_lifecycle(self):
        user_id = str(uuid.uuid4())
        tenant_id = str(uuid.uuid4())
        role = "admin"

        token = create_access_token(
            subject=user_id,
            tenant_id=tenant_id,
            role=role,
        )

        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 20)

        payload = decode_access_token(token)
        self.assertEqual(payload["sub"], user_id)
        self.assertEqual(payload["tenant_id"], tenant_id)
        self.assertEqual(payload["role"], role)
        self.assertIn("exp", payload)
        self.assertIn("iat", payload)

    def test_jwt_tampering_fails(self):
        user_id = str(uuid.uuid4())
        tenant_id = str(uuid.uuid4())

        token = create_access_token(
            subject=user_id,
            tenant_id=tenant_id,
        )

        tampered_token = token[:-5] + "XXXXX"
        with self.assertRaises(Exception):
            decode_access_token(tampered_token)


if __name__ == "__main__":
    unittest.main()
