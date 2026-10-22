#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : video.py
# @Project   : ODPlatform / frame_source
# @Function  : 视频源 —— 本地视频文件 + rtsp/rtmp/http(s) 网络流
"""
视频输入源(VideoSource, 精简版)。

关键处理:
    - 网络流诚实标注: is_stream_url 检测 → total_frames=None(流没有总帧数)
    - fps 缺失/异常 → 明确 warning + 置 None(时间戳不可用)
    - 文件帧号用解码器位置(POS_FRAMES); 流不可靠 → 退回自增计数

已按精简要求去掉: stride 跳采(原用 cap.grab())、seek、_just_sought 标志。
"""
from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Optional

import cv2

from ..core.base     import FrameSource
from ..core.config   import VideoConfig
from ..core.registry import register_source
from ..core.types    import Frame, FrameInfo, SourceType, is_stream_url


logger = logging.getLogger(__name__)


@register_source(VideoConfig)
class VideoSource(FrameSource):
    """视频文件 / 网络流源。"""

    def __init__(self, config: VideoConfig):
        super().__init__(config)
        self._path: str = config.path
        self._is_stream: bool = is_stream_url(config.path)
        self._cap: Optional[cv2.VideoCapture] = None
        self._fps: Optional[float] = None
        self._total: Optional[int] = None

    def open(self) -> bool:
        # 复位位置状态
        self._frame_index = 0

        self._cap = cv2.VideoCapture(self._path)
        if not self._cap.isOpened():
            logger.error(f"无法打开视频源: {self._path}")
            self._cap = None
            return False

        # fps: 缺失/0/NaN → 明确置 None
        fps = self._cap.get(cv2.CAP_PROP_FPS)
        if fps is None or fps <= 0 or math.isnan(fps):
            logger.warning(f"视频 fps 缺失或异常({fps}), 时间戳不可用: {self._path}")
            self._fps = None
        else:
            self._fps = float(fps)

        # total_frames: 网络流没有总帧数(无限流); 文件读 FRAME_COUNT, ≤0 也置 None(诚实)
        if self._is_stream:
            self._total = None
            logger.info(f"网络流已打开(无总帧数): {self._path}")
        else:
            n = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self._total = n if n > 0 else None
        return True

    def read(self) -> Optional[Frame]:
        if self._cap is None:
            return None

        ret, img = self._cap.read()
        if not ret:
            return None

        # 当前帧号: 文件用解码器位置(POS_FRAMES); 流不可靠 → 退回自增计数
        if self._is_stream:
            idx = self._frame_index
        else:
            idx = max(0, int(self._cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1)
        self._frame_index = idx + 1     # 下一帧位置

        h, w = img.shape[:2]
        timestamp = (idx / self._fps) if self._fps else 0.0
        info = FrameInfo(
            width=w, height=h,
            source_type=SourceType.VIDEO,
            source_path=self._path,
            frame_index=idx, total_frames=self._total,
            timestamp=timestamp, fps=self._fps,
            filename=(self._path if self._is_stream else Path(self._path).name),
        )
        return Frame(image=img, info=info)   # 零拷贝

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def get_source_type(self) -> SourceType:
        return SourceType.VIDEO
