import os
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from .models import BotConfig, ExtractedOdds, BetRecord, BotLog
from .security import (
    encrypt_secret,
    decrypt_secret,
    mask_sensitive_url,
    sanitize_log,
    get_expected_api_key,
)


class BotEngineAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.config = BotConfig.get_active()
        self.api_key = get_expected_api_key()
        # Authenticate test client with X-API-Key by default
        self.client.credentials(HTTP_X_API_KEY=self.api_key)

    def test_unauthenticated_request_rejected(self):
        """Verify Grade-A security rejects unauthenticated requests with HTTP 401."""
        unauth_client = APIClient()
        res = unauth_client.get('/api/v1/settings/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_api_key_rejected(self):
        """Verify requests with incorrect API keys are rejected with HTTP 401."""
        bad_client = APIClient()
        bad_client.credentials(HTTP_X_API_KEY="invalid_attacker_token_12345")
        res = bad_client.get('/api/v1/settings/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_and_update_settings(self):
        # 1. GET Settings
        res = self.client.get('/api/v1/settings/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['base_stake'], 50.0)

        # 2. PUT Settings
        update_data = {
            'base_stake': 150.0,
            'auto_cashout': 1.80,
            'multiplier': 2.5,
            'strategy': 'martingale',
        }
        res = self.client.put('/api/v1/settings/', update_data, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['base_stake'], 150.0)
        self.assertEqual(res.data['auto_cashout'], 1.80)

    def test_encryption_at_rest(self):
        """Verify sensitive URLs are encrypted in the database at rest."""
        sensitive_url = "https://www.ilotbet.com/pc/iframe?content=MY_SECRET_CASINO_TOKEN_999"
        self.config.game_url = sensitive_url
        self.config.save()

        # Direct DB value must be encrypted
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT game_url FROM bot_engine_botconfig WHERE id = %s", [self.config.id])
            raw_db_val = cursor.fetchone()[0]
            self.assertTrue(raw_db_val.startswith("enc::"))
            self.assertNotIn("MY_SECRET_CASINO_TOKEN_999", raw_db_val)

        # Decrypted method retrieves original plaintext
        self.assertEqual(self.config.get_decrypted_game_url(), sensitive_url)

        # Serializer representation must mask the token
        res = self.client.get('/api/v1/settings/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('REDACTED', res.data['game_url'])
        self.assertNotIn('MY_SECRET_CASINO_TOKEN_999', res.data['game_url'])

    def test_bot_log_sanitization(self):
        """Verify BotLog automatically strips Telegram tokens, passwords, and casino session tokens."""
        dirty_msg = "Error connecting to bot1234567890:ABCdefGHIjklMNOpqrsTUVwxyz with content=DUMMY_CASINO_TOKEN_ABC123 and password=mysecretpass"
        log = BotLog.objects.create(level="ERROR", message=dirty_msg)
        self.assertNotIn("ABCdefGHIjklMNOpqrsTUVwxyz", log.message)
        self.assertNotIn("DUMMY_CASINO_TOKEN_ABC123", log.message)
        self.assertNotIn("mysecretpass", log.message)
        self.assertIn("[REDACTED]", log.message)

    def test_odds_database_and_pagination(self):
        # Create sample odds
        ExtractedOdds.objects.create(multiplier=1.24, site='ilotbet')
        ExtractedOdds.objects.create(multiplier=11.49, site='ilotbet')
        ExtractedOdds.objects.create(multiplier=2.50, site='ilotbet')

        res = self.client.get('/api/v1/odds/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 3)
        self.assertEqual(len(res.data['results']), 3)

        # Filter under 2.0x
        res_filtered = self.client.get('/api/v1/odds/?under_2x=true')
        self.assertEqual(res_filtered.status_code, status.HTTP_200_OK)
        self.assertEqual(res_filtered.data['count'], 1)
        self.assertEqual(res_filtered.data['results'][0]['multiplier'], 1.24)

    def test_analytics_endpoint(self):
        ExtractedOdds.objects.create(multiplier=1.50)
        ExtractedOdds.objects.create(multiplier=3.00)
        BetRecord.objects.create(
            stake=50.0,
            cashout_target=1.50,
            crash_multiplier=1.80,
            won=True,
            profit_loss=25.0,
            balance_after=125.0
        )

        res = self.client.get('/api/v1/analytics/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_odds_extracted'], 2)
        self.assertEqual(res.data['total_bets'], 1)
        self.assertEqual(res.data['win_rate'], 100.0)
        self.assertEqual(res.data['total_profit_loss'], 25.0)

    def test_export_odds_csv_and_json(self):
        ExtractedOdds.objects.create(multiplier=2.15, site='ilotbet')

        # CSV export
        url = reverse('export-odds')
        res_csv = self.client.get(url, {'export_format': 'csv'})
        self.assertEqual(res_csv.status_code, status.HTTP_200_OK)
        self.assertIn('text/csv', res_csv['Content-Type'])
        self.assertIn('2.15', res_csv.content.decode())

        # JSON export
        res_json = self.client.get(url, {'export_format': 'json'})
        self.assertEqual(res_json.status_code, status.HTTP_200_OK)
        self.assertIn('application/json', res_json['Content-Type'])
        self.assertIn('2.15', res_json.content.decode())

    def test_bot_status_endpoint(self):
        res = self.client.get('/api/v1/bot/status/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('is_running', res.data)
        self.assertIn('state', res.data)
        self.assertIn('recent_multipliers', res.data)

    def test_safezone_analytics_cluster_meter(self):
        """Verify SafeZone analytics endpoint outputs 1 to 20 loss cluster frequencies."""
        from datetime import datetime, timezone
        # Sequence: 1 loss (1.10), win (1.55), 2 losses (1.05, 1.20), win (2.10), 6 losses (1.01 x 6), win (1.80)
        multipliers = [1.10, 1.55, 1.05, 1.20, 2.10, 1.01, 1.02, 1.03, 1.04, 1.05, 1.06, 1.80]
        for m in multipliers:
            ExtractedOdds.objects.create(multiplier=m, site='ilotbet')

        res = self.client.get('/api/v1/analytics/safezone/?target_odds=1.50')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('summary', res.data)
        summary = res.data['summary']
        freq = summary['loss_streak_frequency']

        # Check that 1 through 20 keys are present
        for i in range(1, 21):
            self.assertIn(str(i), freq)
        self.assertIn('21+', freq)
        self.assertIn('5+', freq)

        # 1 loss sequence occurred once
        self.assertEqual(freq['1'], 1)
        # 2 loss sequence occurred once
        self.assertEqual(freq['2'], 1)
        # 6 loss sequence occurred once
        self.assertEqual(freq['6'], 1)
        # 5+ captured the 6-loss sequence
        self.assertEqual(freq['5+'], 1)
        self.assertEqual(summary['total_loss_clusters'], 3)

    def test_settings_update_preserves_masked_api_keys(self):
        """Grade-A Security: verify masked keys in PUT request NEVER destroy real encrypted keys."""
        real_gemini = "AQ.TEST_MOCK_GEMINI_KEY_00000000000000000000"
        real_openrouter = "sk-or-v1-mock-openrouter-testing-secret-token"
        real_url = "https://www.ilotbet.com/pc/iframe?content=SUPER_CONFIDENTIAL_TOKEN_777"

        self.config.gemini_api_key = real_gemini
        self.config.openrouter_api_key = real_openrouter
        self.config.game_url = real_url
        self.config.save()

        # Fetch settings: keys are masked
        get_res = self.client.get('/api/v1/settings/')
        masked_gemini = get_res.data['gemini_api_key']
        masked_openrouter = get_res.data['openrouter_api_key']
        masked_url = get_res.data['game_url']
        self.assertIn("...", masked_gemini)
        self.assertIn("...", masked_openrouter)
        self.assertIn("REDACTED", masked_url)

        # Submit update sending back the masked keys (simulates UI form submission)
        put_payload = {
            'base_stake': 75.0,
            'gemini_api_key': masked_gemini,
            'openrouter_api_key': masked_openrouter,
            'game_url': masked_url,
        }
        put_res = self.client.put('/api/v1/settings/', put_payload, format='json')
        self.assertEqual(put_res.status_code, status.HTTP_200_OK)

        # Refresh from database and verify secrets were NOT overwritten
        self.config.refresh_from_db()
        self.assertEqual(self.config.get_decrypted_gemini_key(), real_gemini)
        self.assertEqual(self.config.get_decrypted_openrouter_key(), real_openrouter)
        self.assertEqual(self.config.get_decrypted_game_url(), real_url)

    def test_settings_update_with_empty_keys_preserves_secrets(self):
        """Verify empty string keys in settings update do NOT wipe existing keys."""
        real_gemini = "AQ.TEST_MOCK_GEMINI_KEY_00000000000000000000"
        self.config.gemini_api_key = real_gemini
        self.config.save()

        put_res = self.client.put('/api/v1/settings/', {'gemini_api_key': ''}, format='json')
        self.assertEqual(put_res.status_code, status.HTTP_200_OK)

        self.config.refresh_from_db()
        self.assertEqual(self.config.get_decrypted_gemini_key(), real_gemini)

    def test_settings_update_with_new_key_encrypts(self):
        """Verify submitting a genuine new key properly encrypts it with Fernet."""
        new_key = "AQ.NEW_TEST_STUDIO_KEY_999988887777"
        put_res = self.client.put('/api/v1/settings/', {'gemini_api_key': new_key}, format='json')
        self.assertEqual(put_res.status_code, status.HTTP_200_OK)

        self.config.refresh_from_db()
        self.assertTrue(self.config.gemini_api_key.startswith("enc::"))
        self.assertEqual(self.config.get_decrypted_gemini_key(), new_key)

    def test_settings_clear_sentinel(self):
        """Verify __CLEAR__ sentinel safely clears an API key."""
        self.config.gemini_api_key = "AQ.SOMETHING_TO_CLEAR_12345"
        self.config.save()

        put_res = self.client.put('/api/v1/settings/', {'gemini_api_key': '__CLEAR__'}, format='json')
        self.assertEqual(put_res.status_code, status.HTTP_200_OK)

        self.config.refresh_from_db()
        self.assertEqual(self.config.gemini_api_key, "")

    def test_comprehensive_secret_scrubbing(self):
        """Verify sanitize_log scrubs all sensitive credentials across formats."""
        log_sample = (
            "OpenRouter sk-or-v1-mock-openrouter-testing-secret-token "
            "Gemini AQ.TEST_MOCK_GEMINI_KEY_00000000000000000000 and AIzaSyDk1234567890123456789012345678901 "
            "Fernet enc::gAAAAABnewEncryptedToken12345678901234567890 "
            "Postgres postgresql://admin:SuperSecretPass123@localhost:5432/aviator_db "
            "Header x-goog-api-key: AIzaSyDkSecretKey1234567890"
        )
        scrubbed = sanitize_log(log_sample)
        self.assertNotIn("mock-openrouter-testing-secret-token", scrubbed)
        self.assertNotIn("AQ.TEST_MOCK_GEMINI_KEY_00000000000000000000", scrubbed)
        self.assertNotIn("SuperSecretPass123", scrubbed)
        self.assertNotIn("gAAAAABnewEncryptedToken", scrubbed)
        self.assertIn("[REDACTED]", scrubbed)

    def test_ai_endpoints_require_authentication(self):
        """Verify all AI endpoints enforce Grade-A authentication."""
        unauth = APIClient()
        self.assertEqual(unauth.get('/api/v1/ai/status/').status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(unauth.get('/api/v1/ai/models/').status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(unauth.post('/api/v1/ai/analyze/').status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(unauth.post('/api/v1/ai/recommend/').status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(unauth.post('/api/v1/ai/chat/').status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticated requests are accepted
        auth_res = self.client.get('/api/v1/ai/status/')
        self.assertEqual(auth_res.status_code, status.HTTP_200_OK)
        self.assertIn('ai_enabled', auth_res.data)

    def test_persistent_chat_and_swarm_endpoints(self):
        """Verify chat session creation, listing, detail, message sending, and swarm status."""
        from .models import AIChatSession, AIChatMessage

        # 1. Create chat session
        create_res = self.client.post('/api/v1/ai/chats/', {'title': 'Best Aviator Staking Plan'}, format='json')
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        session_id = create_res.data['id']
        self.assertEqual(create_res.data['title'], 'Best Aviator Staking Plan')

        # 2. List sessions
        list_res = self.client.get('/api/v1/ai/chats/')
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_res.data['sessions']), 1)

        # 3. Post user message to session
        msg_res = self.client.post(
            f'/api/v1/ai/chats/{session_id}/message/',
            {'content': 'What is our current risk profile?'},
            format='json'
        )
        self.assertEqual(msg_res.status_code, status.HTTP_201_CREATED)
        self.assertIn('user_message', msg_res.data)
        self.assertIn('assistant_message', msg_res.data)
        self.assertIn('swarm', msg_res.data)

        # 4. Swarm status endpoint
        swarm_res = self.client.get('/api/v1/ai/swarm/status/')
        self.assertEqual(swarm_res.status_code, status.HTTP_200_OK)
        self.assertIn('consensus', swarm_res.data)
        self.assertIn('consensus_directive', swarm_res.data['consensus'])

        # 5. Delete session
        del_res = self.client.delete(f'/api/v1/ai/chats/{session_id}/')
        self.assertEqual(del_res.status_code, status.HTTP_200_OK)
        self.assertEqual(AIChatSession.objects.count(), 0)

    def test_desktop_runner_relay_integration(self):
        """Verify hybrid desktop runner connection, telemetry ingestion, and control routing."""
        from .service import bot_service
        from .models import ExtractedOdds

        # Initially runner is disconnected
        bot_service.set_runner_connected(False)
        self.assertFalse(bot_service.runner_connected)

        # Simulate runner connection from residential IP
        bot_service.set_runner_connected(True, "197.210.55.12")
        self.assertTrue(bot_service.runner_connected)
        self.assertEqual(bot_service.runner_ip, "197.210.55.12")

        # Simulate runner streaming live odds
        initial_odds_count = ExtractedOdds.objects.count()
        bot_service.handle_remote_odds(3.45)
        self.assertEqual(ExtractedOdds.objects.count(), initial_odds_count + 1)
        self.assertTrue(bot_service.is_running)

        # Simulate runner updating status and balance
        bot_service.handle_remote_balance(25400.50)
        bot_service.handle_remote_status("Live Auto-Staking Active", is_running=True, is_staking=True)
        self.assertEqual(bot_service.last_balance, 25400.50)
        self.assertTrue(bot_service.is_staking)

        # Verify get_status includes runner metadata
        bot_status = bot_service.get_status()
        self.assertTrue(bot_status['runner_connected'])
        self.assertEqual(bot_status['runner_ip'], "197.210.55.12")
        self.assertEqual(bot_status['balance'], 25400.50)

        # Remote control actions route to runner
        res_pause = bot_service.pause_staking()
        self.assertEqual(res_pause['status'], 'ok')
        self.assertFalse(bot_service.is_staking)

        res_stop = bot_service.emergency_stop()
        self.assertEqual(res_stop['status'], 'ok')
        self.assertFalse(bot_service.is_running)

        # Disconnect runner
        bot_service.set_runner_connected(False)
        self.assertFalse(bot_service.runner_connected)




