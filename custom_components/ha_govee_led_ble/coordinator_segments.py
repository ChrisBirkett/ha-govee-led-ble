"""Segment painting and per-segment brightness for the Govee BLE coordinator."""

import asyncio
import logging

from .control_arbiter import ControlIntent, async_control_intent
from .coordinator_base import _CoordinatorBase
from .light_commands import SegmentColorGroup, build_segment_brightness, build_segment_paint

_LOGGER = logging.getLogger(__name__)


class _SegmentMixin(_CoordinatorBase):
    async def async_paint_segments(self, groups: list[SegmentColorGroup]) -> None:
        async with self.async_mask_transaction():
            await self._async_paint_segments(groups)

    async def _async_paint_segments(self, groups: list[SegmentColorGroup]) -> None:
        """Optimistically paint colour groups onto the segment slots.

        Each group pairs 1-based segment indices with an RGB colour. The device does not
        publish segment state after writes, so the complete segment query verifies the
        optimistic state without resending or rolling back a completed write.
        """
        resolved: list[SegmentColorGroup] = [(list(segments), rgb) for segments, rgb in groups]
        packets = build_segment_paint(resolved, self.model, profile=self.profile)
        expected_colors = {segment - 1: rgb for segments, rgb in resolved for segment in segments}
        expected_brightness: list[int] | None = None
        attempted = False
        async with async_control_intent(self, ControlIntent.USER):
            segment_revision = self._field_revisions.get("segment_colors", 0)
            try:
                for packet in packets:

                    def before_write() -> None:
                        nonlocal attempted, expected_colors, expected_brightness
                        # Historical observations cannot prove pre-write sibling state.
                        if (
                            not attempted
                            and self.segment_state_source == "observed"
                            and self._field_revisions.get("segment_colors", 0) > segment_revision
                        ):
                            expected_colors = dict(enumerate(self.segment_colors)) | expected_colors
                            expected_brightness = list(self.segment_brightness)
                        attempted = True

                    attempts = self._static_write_attempts
                    try:
                        await self.send_command(packet, write_guard=before_write)
                    except Exception:
                        # A later pre-write failure still leaves earlier groups applied.
                        if attempted and self._static_write_attempts == attempts:
                            try:
                                async with asyncio.timeout(2.0):
                                    await self.async_refresh_segments()
                            except Exception:
                                _LOGGER.debug("Partial segment paint reconciliation failed", exc_info=True)
                        raise
                if (
                    not await self.async_refresh_segments()
                    or any(self.segment_colors[index] != rgb for index, rgb in expected_colors.items())
                    or (expected_brightness is not None and self.segment_brightness != expected_brightness)
                ):
                    raise RuntimeError("Failed to confirm segment paint")
            finally:
                if attempted:
                    self.async_set_updated_data(self.data or {})

    async def async_set_segment_brightness(self, segments: list[int], brightness: int) -> None:
        async with self.async_mask_transaction():
            await self._async_set_segment_brightness(segments, brightness)

    async def _async_set_segment_brightness(self, segments: list[int], brightness: int) -> None:
        segments = list(segments)
        value = max(0, min(100, brightness))
        packet = build_segment_brightness(segments, value, self.model, profile=self.profile)
        expected_brightness = {segment - 1: value for segment in segments}
        expected_colors: list[tuple[int, int, int]] | None = None
        attempted = False

        def before_write() -> None:
            nonlocal attempted, expected_colors, expected_brightness
            if (
                not attempted
                and self.segment_state_source == "observed"
                and self._field_revisions.get("segment_colors", 0) > segment_revision
            ):
                expected_brightness = dict(enumerate(self.segment_brightness)) | expected_brightness
                expected_colors = list(self.segment_colors)
            attempted = True

        async with async_control_intent(self, ControlIntent.USER):
            segment_revision = self._field_revisions.get("segment_colors", 0)
            try:
                await self.send_command(packet, write_guard=before_write)
                if (
                    not await self.async_refresh_segments()
                    or any(self.segment_brightness[index] != value for index, value in expected_brightness.items())
                    or (expected_colors is not None and self.segment_colors != expected_colors)
                ):
                    raise RuntimeError("Failed to confirm segment brightness")
            finally:
                if attempted:
                    self.async_set_updated_data(self.data or {})
