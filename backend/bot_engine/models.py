from django.db import models
from .security import encrypt_secret, decrypt_secret, sanitize_log


class BotConfig(models.Model):
    base_stake = models.FloatField(default=50.0, help_text="Starting stake amount in NGN")
    strategy = models.CharField(max_length=50, default="martingale", help_text="martingale, dalembert, flat, fibonacci")
    multiplier = models.FloatField(default=3.0, help_text="Loss escalation multiplier (e.g. 3.0 for 1.50x cashout)")
    auto_cashout = models.FloatField(default=1.50, help_text="Target cashout multiplier (e.g. 1.50x)")
    max_stake = models.FloatField(default=5000.0, help_text="Safety maximum stake in NGN")
    max_loss_steps = models.IntegerField(default=5, help_text="Maximum consecutive losing streak steps")
    stop_loss = models.FloatField(default=10000.0, help_text="Total session stop-loss in NGN")
    profit_target = models.FloatField(default=5000.0, help_text="Total session profit target in NGN")
    dry_run = models.BooleanField(default=False, help_text="Simulation mode without placing real bets")
    ceiling_rule = models.BooleanField(default=True, help_text="Always round fractional stakes up to next whole integer (Ceiling Rule)")
    network_auto_retry = models.BooleanField(default=True, help_text="Automatically retry on connection loss")
    network_retry_delay = models.IntegerField(default=10, help_text="Seconds to wait between retry attempts")
    network_max_retries = models.IntegerField(default=5, help_text="Maximum consecutive reconnect attempts")
    site = models.CharField(max_length=50, default="ilotbet")
    platform = models.CharField(max_length=50, default="ilotbet", help_text="Active platform addon (ilotbet, bcgame, sportybet)")
    game = models.CharField(max_length=50, default="best_aviator", help_text="Active game type (best_aviator, crash, limbo)")
    game_url = models.TextField(
        default="https://www.ilotbet.com/pc/iframe",
        blank=True,
        help_text="Encrypted at rest: session URL"
    )


    # AI LLM Copilot & Advisor Configuration
    ai_enabled = models.BooleanField(default=True, help_text="Enable AI LLM Advisor & Market Intelligence")
    ai_autonomous_mode = models.BooleanField(default=False, help_text="Allow AI to dynamically adjust target odds or pause staking")
    ai_provider = models.CharField(max_length=50, default="gemini", choices=[("gemini", "Google Gemini"), ("openrouter", "OpenRouter.ai")])
    ai_model = models.CharField(max_length=100, default="gemini-2.0-flash", blank=True, help_text="Model ID dynamically selected from provider")
    gemini_api_key = models.TextField(default="", blank=True, help_text="Encrypted Google AI Studio API Key")
    openrouter_api_key = models.TextField(default="", blank=True, help_text="Encrypted OpenRouter API Key")
    ai_risk_tolerance = models.CharField(
        max_length=20,
        default="conservative",
        choices=[("conservative", "Conservative"), ("balanced", "Balanced"), ("aggressive", "Aggressive")],
        help_text="Risk appetite model used for AI staking adjustments"
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bot Configuration"
        verbose_name_plural = "Bot Configurations"

    def save(self, *args, **kwargs):
        # Synchronize site and platform
        if self.platform and self.platform != self.site:
            self.site = self.platform
        elif self.site and not self.platform:
            self.platform = self.site

        # Encrypt sensitive fields at rest
        if self.game_url and not self.game_url.startswith("enc::"):
            self.game_url = encrypt_secret(self.game_url)
        if self.gemini_api_key and not self.gemini_api_key.startswith("enc::"):
            self.gemini_api_key = encrypt_secret(self.gemini_api_key)
        if self.openrouter_api_key and not self.openrouter_api_key.startswith("enc::"):
            self.openrouter_api_key = encrypt_secret(self.openrouter_api_key)

        super().save(*args, **kwargs)

    def get_decrypted_game_url(self) -> str:
        """Decrypt URL for browser engine access."""
        if self.game_url:
            dec = decrypt_secret(self.game_url)
            if dec and dec != "https://www.ilotbet.com/pc/iframe":
                return dec
        import os
        env_url = os.getenv("GAME_URL", "").strip()
        if env_url:
            return env_url
        return "https://www.ilotbet.com/pc/iframe"

    def get_decrypted_gemini_key(self) -> str:
        if self.gemini_api_key:
            return decrypt_secret(self.gemini_api_key)
        import os
        return os.getenv("GEMINI_API_KEY", "").strip()

    def get_decrypted_openrouter_key(self) -> str:
        if self.openrouter_api_key:
            return decrypt_secret(self.openrouter_api_key)
        import os
        return os.getenv("OPENROUTER_API_KEY", "").strip()

    @classmethod
    def get_active(cls) -> "BotConfig":
        config, _ = cls.objects.get_or_create(id=1)
        return config


class ExtractedOdds(models.Model):
    multiplier = models.FloatField(db_index=True)
    site = models.CharField(max_length=50, default="ilotbet", db_index=True)
    game = models.CharField(max_length=50, default="aviator", db_index=True)
    phase = models.CharField(max_length=50, default="FINISHED")
    is_under_2x = models.BooleanField(default=False, db_index=True)
    is_over_10x = models.BooleanField(default=False, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Extracted Crash Multiplier"
        verbose_name_plural = "Extracted Crash Multipliers"

    def save(self, *args, **kwargs):
        self.is_under_2x = bool(self.multiplier < 2.0)
        self.is_over_10x = bool(self.multiplier >= 10.0)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.multiplier:.2f}x ({self.timestamp.strftime('%H:%M:%S')})"


class BetRecord(models.Model):
    stake = models.FloatField()
    cashout_target = models.FloatField()
    crash_multiplier = models.FloatField()
    won = models.BooleanField(db_index=True)
    profit_loss = models.FloatField()
    balance_after = models.FloatField()
    site = models.CharField(max_length=50, default="ilotbet", db_index=True)
    game = models.CharField(max_length=50, default="aviator", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Bet & Stake Ledger"
        verbose_name_plural = "Bet & Stake Ledgers"

    def __str__(self) -> str:
        res = "WON" if self.won else "LOST"
        return f"[{res}] Stake: {self.stake:.2f} | Crash: {self.crash_multiplier:.2f}x | P/L: {self.profit_loss:+.2f}"


class BotLog(models.Model):
    level = models.CharField(max_length=20, default="INFO")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Bot Log"
        verbose_name_plural = "Bot Logs"

    def save(self, *args, **kwargs):
        self.message = sanitize_log(self.message)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"[{self.level}] {self.message[:60]}"


class AIChatSession(models.Model):
    title = models.CharField(max_length=255, default="New Conversation")
    platform = models.CharField(max_length=50, default="ilotbet")
    game = models.CharField(max_length=50, default="best_aviator")
    is_pinned = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ["-is_pinned", "-updated_at"]
        verbose_name = "AI Chat Session"
        verbose_name_plural = "AI Chat Sessions"

    def __str__(self) -> str:
        return f"[{self.id}] {self.title} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class AIChatMessage(models.Model):
    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System Directive"),
        ("agent", "Swarm Agent"),
    ]

    session = models.ForeignKey(
        AIChatSession,
        related_name="messages",
        on_delete=models.CASCADE,
        db_index=True
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")
    sender_name = models.CharField(max_length=50, default="User")
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "AI Chat Message"
        verbose_name_plural = "AI Chat Messages"

    def __str__(self) -> str:
        return f"{self.sender_name} ({self.role}): {self.content[:50]}"


class AIDiscoveryMemory(models.Model):
    CATEGORY_CHOICES = [
        ("STREAK_TIMING", "Streak Timing & Hour Analysis"),
        ("CLUSTER_PATTERN", "Cluster & Loss Pattern"),
        ("STRATEGY_RULE", "Staking & Cashout Rule"),
        ("RISK_LIMIT", "Risk & Drawdown Barrier"),
        ("MARKET_INSIGHT", "Market Observation"),
        ("GENERAL", "General Discovery"),
    ]

    title = models.CharField(max_length=255, db_index=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="GENERAL", db_index=True)
    content = models.TextField(help_text="Empirical finding, pattern rule, or timing discovery")
    evidence_data = models.JSONField(default=dict, blank=True, help_text="Supporting telemetry metrics (hours, streak length, etc.)")
    source_session = models.ForeignKey(
        AIChatSession,
        related_name="memories",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True
    )
    platform = models.CharField(max_length=50, default="ilotbet", db_index=True)
    game = models.CharField(max_length=50, default="best_aviator", db_index=True)
    is_active = models.BooleanField(default=True, db_index=True, help_text="Fed into active Swarm reasoning if True")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ["-is_active", "-updated_at"]
        verbose_name = "AI Discovery Memory"
        verbose_name_plural = "AI Discovery Memories"

    def __str__(self) -> str:
        return f"[{self.category}] {self.title} ({'Active' if self.is_active else 'Disabled'})"

