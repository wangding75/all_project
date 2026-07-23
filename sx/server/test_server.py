import asyncio
import hashlib
import os
import unittest
from fastapi.testclient import TestClient

# Ensure test DB environment
os.environ["DATABASE_URL"] = "./test_sx_license.db"
os.environ["SERVER_SECRET"] = "sx_dev_secret_2026"
os.environ["CARDNET_WEBHOOK_SECRET"] = "sx_webhook_dev"
os.environ["ADMIN_API_KEY"] = "sx_admin_dev"

from database import init_db
from main import app

class TestLicenseServer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if os.path.exists("./test_sx_license.db"):
            try:
                os.remove("./test_sx_license.db")
            except Exception:
                pass
        asyncio.run(init_db())

    @classmethod
    def tearDownClass(cls):
        if os.path.exists("./test_sx_license.db"):
            try:
                os.remove("./test_sx_license.db")
            except Exception:
                pass

    def setUp(self):
        self.client_cm = TestClient(app)
        self.client = self.client_cm.__enter__()

    def tearDown(self):
        self.client_cm.__exit__(None, None, None)

    def _calc_sign(self, card_key: str, device_id: str) -> str:
        raw = card_key + device_id + "sx_dev_secret_2026"
        return hashlib.md5(raw.encode()).hexdigest().upper()

    def test_01_health(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "ok")

    def test_02_card_generate_and_status(self):
        payload = {
            "duration_days": 30,
            "count": 2,
            "admin_api_key": "sx_admin_dev"
        }
        resp = self.client.post("/api/cards/generate", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["code"], 200)
        self.assertEqual(len(data["cards"]), 2)
        card1 = data["cards"][0]

        resp_status = self.client.get(f"/api/cards/status/{card1}?admin_api_key=sx_admin_dev")
        self.assertEqual(resp_status.status_code, 200)
        st_data = resp_status.json()
        self.assertEqual(st_data["status"], "unused")

    def test_03_card_deliver_webhook(self):
        headers = {"Authorization": "Bearer sx_webhook_dev"}
        payload = {
            "order_id": "ORDER_10001",
            "product_id": "sx_30d",
            "quantity": 1
        }
        resp = self.client.post("/api/cards/deliver", json=payload, headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["code"], 200)
        self.assertEqual(len(data["cards"]), 1)

    def test_04_license_activation_flow(self):
        # 1. Generate 1 card
        gen_payload = {"duration_days": 7, "count": 1, "admin_api_key": "sx_admin_dev"}
        resp = self.client.post("/api/cards/generate", json=gen_payload)
        card_key = resp.json()["cards"][0]
        device_a = "DEVICE_ANDROID_AAA"
        device_b = "DEVICE_ANDROID_BBB"

        # 2. Activate with bad sign -> 401
        bad_sign_req = {
            "card_key": card_key,
            "device_id": device_a,
            "sign": "INVALID_SIGN"
        }
        resp_bad = self.client.post("/api/license/activate", json=bad_sign_req)
        self.assertEqual(resp_bad.status_code, 401)

        # 3. Activate with valid sign on Device A -> 200
        valid_sign_a = self._calc_sign(card_key, device_a)
        act_req_a = {
            "card_key": card_key,
            "device_id": device_a,
            "sign": valid_sign_a
        }
        resp_act_a = self.client.post("/api/license/activate", json=act_req_a)
        self.assertEqual(resp_act_a.status_code, 200)
        act_data_a = resp_act_a.json()
        self.assertEqual(act_data_a["code"], 200)
        token_a = act_data_a["data"]["token"]
        self.assertTrue(len(token_a) > 0)

        # 4. Re-activate on Device A should succeed
        resp_react = self.client.post("/api/license/activate", json=act_req_a)
        self.assertEqual(resp_react.status_code, 200)
        self.assertEqual(resp_react.json()["code"], 200)

        # 5. Activate on Device B should fail (bound to A)
        valid_sign_b = self._calc_sign(card_key, device_b)
        act_req_b = {
            "card_key": card_key,
            "device_id": device_b,
            "sign": valid_sign_b
        }
        resp_act_b = self.client.post("/api/license/activate", json=act_req_b)
        self.assertEqual(resp_act_b.status_code, 200)
        self.assertEqual(resp_act_b.json()["code"], 400)

        # 6. Verify license with token on Device A
        headers_a = {"Authorization": f"Bearer {token_a}"}
        resp_verify_a = self.client.get(f"/api/license/verify?device_id={device_a}", headers=headers_a)
        self.assertEqual(resp_verify_a.status_code, 200)
        self.assertTrue(resp_verify_a.json()["data"]["valid"])

        # 7. Verify license on Device B should fail
        resp_verify_b = self.client.get(f"/api/license/verify?device_id={device_b}", headers=headers_a)
        self.assertEqual(resp_verify_b.status_code, 200)
        self.assertFalse(resp_verify_b.json()["data"]["valid"])

        # 8. Unbind card by admin
        unbind_req = {
            "card_key": card_key,
            "admin_api_key": "sx_admin_dev"
        }
        resp_unbind = self.client.post("/api/license/unbind", json=unbind_req)
        self.assertEqual(resp_unbind.status_code, 200)
        self.assertEqual(resp_unbind.json()["code"], 200)

        # 9. Now Device B can activate with card_key
        resp_act_b2 = self.client.post("/api/license/activate", json=act_req_b)
        self.assertEqual(resp_act_b2.status_code, 200)
        self.assertEqual(resp_act_b2.json()["code"], 200)

if __name__ == "__main__":
    unittest.main()
