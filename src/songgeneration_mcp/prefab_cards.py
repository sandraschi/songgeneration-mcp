"""Prefab in-chat cards - @mcp.tool(app=True) with PrefabApp.

Status and model cards for songgeneration-mcp, mirroring the arxiv-mcp
prefab pattern (Card/CardContent/Badge/Text components).
"""

from __future__ import annotations

import logging

from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    Badge,
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
    Separator,
    Text,
)

log = logging.getLogger("songgeneration-mcp.prefab")


def register_prefab_tools(mcp, logic) -> None:
    """Register show_status_card + show_models_card on the FastMCP instance."""

    @mcp.tool(app=True)
    async def show_status_card() -> PrefabApp:
        """SHOW_STATUS_CARD - GPU VRAM, queue and model state as a rich in-chat card.

        Returns:
            PrefabApp card rendered inline in the conversation.
        """
        try:
            s = await logic.get_status()
        except Exception as exc:
            with Card(css_class="max-w-2xl") as view:
                with CardContent():
                    Text(f"Status unavailable: {exc}", css_class="text-destructive")
            return PrefabApp(view=view, title="Error")
        total = s.get("vram_total", 0) or 0
        used = s.get("vram_used", 0) or 0
        pct = (used / total * 100) if total > 0 else 0.0
        running = bool(s.get("server_running"))
        with Card(css_class="max-w-2xl") as view:
            with CardHeader():
                CardTitle("SongGeneration status")
                CardDescription(f"{used} / {total} MB VRAM ({pct:.1f}%)")
            with CardContent():
                Badge(
                    "Studio online" if running else "Studio offline",
                    variant="default" if running else "destructive",
                )
                Separator(spacing=3)
                Text(f"Active tasks: {s.get('active_generations', 0)}", css_class="text-sm mb-1")
                Text(f"Queued tasks: {s.get('queued_tasks', 0)}", css_class="text-sm mb-1")
                Text(f"Model: {s.get('model_loaded') or 'none loaded'}", css_class="text-sm")
        return PrefabApp(view=view, title="SongGeneration status")

    @mcp.tool(app=True)
    async def show_models_card() -> PrefabApp:
        """SHOW_MODELS_CARD - Studio models as a rich in-chat card.

        Returns:
            PrefabApp card rendered inline in the conversation.
        """
        try:
            models = await logic.list_models()
        except Exception as exc:
            with Card(css_class="max-w-2xl") as view:
                with CardContent():
                    Text(f"Model list unavailable: {exc}", css_class="text-destructive")
            return PrefabApp(view=view, title="Error")
        with Card(css_class="max-w-2xl") as view:
            with CardHeader():
                CardTitle("Studio models")
                CardDescription(f"{len(models)} available")
            with CardContent():
                if not models:
                    Text("No models loaded in Studio.", css_class="text-sm text-muted-foreground")
                for m in models[:20]:
                    Badge(str(m), variant="secondary")
        return PrefabApp(view=view, title="Studio models")
