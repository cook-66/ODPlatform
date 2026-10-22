#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : __init__.py
# @Project   : ODPlatform / frame_source
# @Function  : core 子包入口 — 核心类型 / 配置 / 协议 / 注册表
"""core 子包:数据类型、每源配置、抽象协议、注册表。"""
from __future__ import annotations

from .types import (
    SourceType, FrameInfo, Frame, CameraIntrinsics,
    IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, STREAM_SCHEMES, is_stream_url,
)
from .config import (
    SourceConfig, CameraConfig, VideoConfig, ImageConfig, ImageFolderConfig,
    CameraBackend, CameraCodec,
)
from .base   import FrameSource
from .registry import register_source, build_from_config

__all__ = [
    # 类型
    "SourceType", "FrameInfo", "Frame", "CameraIntrinsics",
    "IMAGE_EXTENSIONS", "VIDEO_EXTENSIONS", "STREAM_SCHEMES", "is_stream_url",
    # 配置
    "SourceConfig", "CameraConfig", "VideoConfig", "ImageConfig", "ImageFolderConfig",
    "CameraBackend", "CameraCodec",
    # 协议
    "FrameSource",
    # 注册表
    "register_source", "build_from_config",
]
