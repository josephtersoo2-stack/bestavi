import csv
import json
from django.http import HttpResponse
from django.db.models import Avg, Count, Max, Min, Sum
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import BotConfig, ExtractedOdds, BetRecord, BotLog
from .serializers import (
    BotConfigSerializer,
    ExtractedOddsSerializer,
    BetRecordSerializer,
    BotLogSerializer,
)
from .service import DjangoBotService


class BotConfigView(APIView):
    def get(self, request):
        config = BotConfig.get_active()
        serializer = BotConfigSerializer(config)
        return Response(serializer.data)

    def put(self, request):
        config = BotConfig.get_active()
        serializer = BotConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # If bot is running, update live settings
            service = DjangoBotService.get_instance()
            if service.controller and service.controller.running:
                from dataclasses import replace
                from pathlib import Path
                from django.conf import settings as django_settings
                from aviator_bot.config.settings import BotSettings, BrowserSelectors, load_settings
                from aviator_bot.config.site_profiles import profile
                project_root = Path(django_settings.BASE_DIR).parent.resolve()
                settings_file = project_root / "config" / "settings.json"
                user_data_path = str(project_root / "data" / ("browser_profile_bcgame" if "bc" in (config.site or "").lower() else "browser_profile"))
                try:
                    file_settings = load_settings(str(settings_file))
                    base_b = replace(file_settings.browser, url=config.get_decrypted_game_url(), headless=False, user_data_dir=user_data_path)
                except Exception:
                    base_b = BrowserSelectors(url=config.get_decrypted_game_url(), headless=False, user_data_dir=user_data_path)
                browser_selectors = replace(profile(config.site, base=base_b), user_data_dir=user_data_path, headless=False)

                settings = BotSettings(
                    base_stake=config.base_stake,
                    strategy=config.strategy,
                    multiplier=config.multiplier,
                    auto_cashout=config.auto_cashout,
                    max_stake=config.max_stake,
                    max_loss_steps=config.max_loss_steps,
                    stop_loss=config.stop_loss,
                    profit_target=config.profit_target,
                    dry_run=config.dry_run,
                    network_auto_retry=config.network_auto_retry,
                    network_retry_delay=config.network_retry_delay,
                    network_max_retries=config.network_max_retries,
                    site=config.site,
                    browser=browser_selectors
                )
                service.controller.update_settings(settings)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BotControlView(APIView):
    throttle_scope = "bot_control"

    def post(self, request):
        action = request.data.get("action", "").lower()
        service = DjangoBotService.get_instance()

        if action == "prepare":
            res = service.prepare()
        elif action == "start":
            res = service.start_staking()
        elif action == "pause":
            res = service.pause_staking()
        elif action == "stop":
            res = service.emergency_stop()
        elif action == "schedule":
            start_in_seconds = request.data.get("start_in_seconds")
            duration_minutes = request.data.get("duration_minutes")
            target_iso_time = request.data.get("target_iso_time")
            auto_stake = request.data.get("auto_stake", True)
            if isinstance(auto_stake, str):
                auto_stake = auto_stake.lower() in ("true", "1", "yes")
            if start_in_seconds is None or float(start_in_seconds) < 0:
                return Response({"status": "error", "message": "Invalid start_in_seconds"}, status=status.HTTP_400_BAD_REQUEST)
            res = service.schedule_auto_start(
                start_in_seconds=float(start_in_seconds),
                duration_minutes=int(duration_minutes) if duration_minutes else None,
                target_iso_time=target_iso_time,
                auto_stake=bool(auto_stake)
            )
        elif action == "cancel_schedule":
            res = service.cancel_schedule()
        else:
            return Response({"status": "error", "message": f"Unknown action: {action}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(res)


class BotStatusView(APIView):
    def get(self, request):
        service = DjangoBotService.get_instance()
        status_data = service.get_status()
        return Response(status_data)


class ExtractedOddsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExtractedOdds.objects.all()
    serializer_class = ExtractedOddsSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        min_mult = self.request.query_params.get("min_multiplier")
        max_mult = self.request.query_params.get("max_multiplier")
        site = self.request.query_params.get("site") or self.request.query_params.get("platform")
        game = self.request.query_params.get("game")
        under_2x = self.request.query_params.get("under_2x")

        if min_mult:
            try: qs = qs.filter(multiplier__gte=float(min_mult))
            except ValueError: pass
        if max_mult:
            try: qs = qs.filter(multiplier__lte=float(max_mult))
            except ValueError: pass
        if site:
            qs = qs.filter(site=site)
        if game:
            qs = qs.filter(game=game)
        if under_2x is not None:
            qs = qs.filter(is_under_2x=under_2x.lower() in ("true", "1"))
        return qs


class BetRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BetRecord.objects.all()
    serializer_class = BetRecordSerializer


class BotLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BotLog.objects.all()[:100]
    serializer_class = BotLogSerializer


class AnalyticsView(APIView):
    def get(self, request):
        total_odds = ExtractedOdds.objects.count()
        avg_mult = ExtractedOdds.objects.aggregate(avg=Avg('multiplier'))['avg'] or 0.0
        max_mult = ExtractedOdds.objects.aggregate(max=Max('multiplier'))['max'] or 0.0
        under_2x_count = ExtractedOdds.objects.filter(is_under_2x=True).count()
        under_2x_pct = (under_2x_count / total_odds * 100) if total_odds > 0 else 0.0

        # Bets stats
        total_bets = BetRecord.objects.count()
        wins = BetRecord.objects.filter(won=True).count()
        win_rate = (wins / total_bets * 100) if total_bets > 0 else 0.0
        total_profit = BetRecord.objects.aggregate(total=Sum('profit_loss'))['total'] or 0.0

        # Multiplier distribution buckets
        b_1_to_1_49 = ExtractedOdds.objects.filter(multiplier__gte=1.0, multiplier__lt=1.50).count()
        b_1_50_to_1_99 = ExtractedOdds.objects.filter(multiplier__gte=1.50, multiplier__lt=2.00).count()
        b_2_to_5 = ExtractedOdds.objects.filter(multiplier__gte=2.0, multiplier__lt=5.0).count()
        b_5_to_10 = ExtractedOdds.objects.filter(multiplier__gte=5.0, multiplier__lt=10.0).count()
        b_over_10 = ExtractedOdds.objects.filter(multiplier__gte=10.0).count()

        # Cumulative P/L history (last 50 bets)
        recent_bets = list(BetRecord.objects.order_by('created_at')[:50])
        cum_pnl = []
        running_sum = 0.0
        for b in recent_bets:
            running_sum += b.profit_loss
            cum_pnl.append({
                "time": b.created_at.strftime("%H:%M:%S"),
                "profit_loss": round(running_sum, 2),
                "multiplier": b.crash_multiplier,
            })

        return Response({
            "total_odds_extracted": total_odds,
            "average_multiplier": round(avg_mult, 2),
            "max_multiplier": round(max_mult, 2),
            "under_2x_percentage": round(under_2x_pct, 1),
            "total_bets": total_bets,
            "win_rate": round(win_rate, 1),
            "total_profit_loss": round(total_profit, 2),
            "distribution": [
                {"range": "1.00x - 1.49x", "count": b_1_to_1_49, "label": "Sub-1.50x Loss Zone"},
                {"range": "1.50x - 1.99x", "count": b_1_50_to_1_99, "label": "1.50x Safe Target Zone"},
                {"range": "2.00x - 4.99x", "count": b_2_to_5, "label": "2.00x - 4.99x Mid Zone"},
                {"range": "5.00x - 9.99x", "count": b_5_to_10, "label": "5.00x - 9.99x High Zone"},
                {"range": "10.00x+", "count": b_over_10, "label": "10.00x+ Jackpot Zone"},
            ],
            "profit_loss_curve": cum_pnl,
        })


class ExportOddsView(APIView):
    def get(self, request):
        fmt = request.query_params.get("export_format") or request.query_params.get("format", "csv")
        fmt = str(fmt).lower()
        odds = ExtractedOdds.objects.all().order_by('-timestamp')

        if fmt == "json":
            data = [
                {
                    "id": o.id,
                    "multiplier": o.multiplier,
                    "site": o.site,
                    "phase": o.phase,
                    "timestamp": o.timestamp.isoformat(),
                }
                for o in odds
            ]
            response = HttpResponse(json.dumps(data, indent=2), content_type="application/json")
            response['Content-Disposition'] = 'attachment; filename="extracted_odds.json"'
            return response

        # Default CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="extracted_odds.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Multiplier', 'Site', 'Phase', 'Timestamp'])
        for o in odds:
            writer.writerow([o.id, f"{o.multiplier:.2f}", o.site, o.phase, o.timestamp.strftime('%Y-%m-%d %H:%M:%S')])
        return response


class SafeZoneAnalyticsView(APIView):
    def get(self, request):
        try:
            target_odds = float(request.query_params.get("target_odds", 1.50))
        except (ValueError, TypeError):
            target_odds = 1.50

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        site = request.query_params.get("site") or request.query_params.get("platform")
        game = request.query_params.get("game")
        min_mult = request.query_params.get("min_multiplier")
        max_mult = request.query_params.get("max_multiplier")

        qs = ExtractedOdds.objects.all().order_by("timestamp")

        if site:
            qs = qs.filter(site=site)
        if game:
            qs = qs.filter(game=game)
        if start_date:
            try:
                qs = qs.filter(timestamp__date__gte=start_date)
            except Exception:
                pass
        if end_date:
            try:
                qs = qs.filter(timestamp__date__lte=end_date)
            except Exception:
                pass
        if min_mult:
            try:
                qs = qs.filter(multiplier__gte=float(min_mult))
            except ValueError:
                pass
        if max_mult:
            try:
                qs = qs.filter(multiplier__lte=float(max_mult))
            except ValueError:
                pass

        odds_list = list(qs.values("id", "multiplier", "site", "timestamp"))
        total_count = len(odds_list)

        cur_loss_streak = 0
        cur_win_streak = 0
        max_loss_streak = 0
        max_win_streak = 0
        loss_streaks_list = []
        win_streaks_list = []
        daily_stats = {}
        serial_rounds = []

        for idx, item in enumerate(odds_list, 1):
            m = item["multiplier"]
            dt = item["timestamp"]
            date_str = dt.strftime("%Y-%m-%d")
            time_str = dt.strftime("%H:%M:%S")

            is_safe = bool(m >= target_odds)

            if is_safe:
                if cur_loss_streak > 0:
                    loss_streaks_list.append(cur_loss_streak)
                    cur_loss_streak = 0
                cur_win_streak += 1
                if cur_win_streak > max_win_streak:
                    max_win_streak = cur_win_streak
                loss_streak_at_round = 0
                win_streak_at_round = cur_win_streak
            else:
                if cur_win_streak > 0:
                    win_streaks_list.append(cur_win_streak)
                    cur_win_streak = 0
                cur_loss_streak += 1
                if cur_loss_streak > max_loss_streak:
                    max_loss_streak = cur_loss_streak
                loss_streak_at_round = cur_loss_streak
                win_streak_at_round = 0

            # Daily tracking
            if date_str not in daily_stats:
                daily_stats[date_str] = {
                    "date": date_str,
                    "total": 0,
                    "wins": 0,
                    "losses": 0,
                    "max_mult": m,
                    "cur_loss_streak": 0,
                    "max_loss_streak": 0,
                }
            d = daily_stats[date_str]
            d["total"] += 1
            if m > d["max_mult"]:
                d["max_mult"] = m
            if is_safe:
                d["wins"] += 1
                d["cur_loss_streak"] = 0
            else:
                d["losses"] += 1
                d["cur_loss_streak"] += 1
                if d["cur_loss_streak"] > d["max_loss_streak"]:
                    d["max_loss_streak"] = d["cur_loss_streak"]

            serial_rounds.append({
                "serial_number": idx,
                "id": item["id"],
                "multiplier": m,
                "date": date_str,
                "time": time_str,
                "timestamp": dt.isoformat(),
                "is_safezone": is_safe,
                "loss_streak_at_round": loss_streak_at_round,
                "win_streak_at_round": win_streak_at_round,
            })

        if cur_loss_streak > 0:
            loss_streaks_list.append(cur_loss_streak)
        if cur_win_streak > 0:
            win_streaks_list.append(cur_win_streak)

        # Consecutive loss cluster distribution (1 up to 20, plus 21+)
        streak_freq = {str(i): 0 for i in range(1, 21)}
        streak_freq["21+"] = 0
        streak_freq["5+"] = 0  # Kept for backwards compatibility

        for s in loss_streaks_list:
            if s >= 5:
                streak_freq["5+"] += 1
            if 1 <= s <= 20:
                streak_freq[str(s)] += 1
            elif s > 20:
                streak_freq["21+"] += 1

        total_loss_clusters = len(loss_streaks_list)

        daily_breakdown = []
        for date_str in sorted(daily_stats.keys(), reverse=True):
            d = daily_stats[date_str]
            win_pct = round((d["wins"] / d["total"] * 100), 1) if d["total"] > 0 else 0.0
            daily_breakdown.append({
                "date": date_str,
                "total_rounds": d["total"],
                "safezone_wins": d["wins"],
                "losszone_losses": d["losses"],
                "win_rate": win_pct,
                "loss_rate": round(100.0 - win_pct, 1),
                "max_loss_streak": d["max_loss_streak"],
                "peak_multiplier": round(d["max_mult"], 2),
            })

        total_wins = sum(1 for item in odds_list if item["multiplier"] >= target_odds)
        total_losses = total_count - total_wins
        overall_win_rate = round((total_wins / total_count * 100), 1) if total_count > 0 else 0.0
        avg_loss_streak = round(sum(loss_streaks_list) / len(loss_streaks_list), 1) if loss_streaks_list else 0.0

        current_streak_type = "SAFEZONE" if (cur_win_streak > 0) else ("LOSS" if cur_loss_streak > 0 else "NONE")
        current_streak_count = cur_win_streak if cur_win_streak > 0 else cur_loss_streak

        order = request.query_params.get("order", "desc").lower()
        try:
            limit = int(request.query_params.get("limit", 200))
        except (ValueError, TypeError):
            limit = 200

        ordered_serial = serial_rounds if order == "asc" else list(reversed(serial_rounds))
        if limit > 0:
            final_serial = ordered_serial[:limit]
        else:
            final_serial = ordered_serial

        return Response({
            "target_odds": target_odds,
            "summary": {
                "total_rounds": total_count,
                "safezone_wins": total_wins,
                "safezone_win_rate": overall_win_rate,
                "losszone_losses": total_losses,
                "losszone_loss_rate": round(100.0 - overall_win_rate, 1) if total_count > 0 else 0.0,
                "max_loss_streak": max_loss_streak,
                "max_win_streak": max_win_streak,
                "avg_loss_streak": avg_loss_streak,
                "current_streak_type": current_streak_type,
                "current_streak_count": current_streak_count,
                "total_loss_clusters": total_loss_clusters,
                "loss_streak_frequency": streak_freq,
            },
            "daily_breakdown": daily_breakdown,
            "serial_rounds": final_serial,
            "total_serial_count": len(serial_rounds),
        })
