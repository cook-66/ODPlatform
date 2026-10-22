#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : __init__.py
# @Project   : ODPlatform / frame_source
# @Function  : frame_source 包入口 —— 公共 API + 触发内置源自注册
"""
frame_source: 统一帧输入源抽象层(可插拔 · 多模态) —— 精简版。

把任意输入源封装成同一套 `for frame in source` 接口。派发用配置类型(注册表)。

最常用:
    from od_platform.frame_source import create_frame_source
    with create_frame_source("0") as src:          # "0"/"x.mp4"/"rtsp://..."/"./imgs"
        for frame in src:
            model(frame.image)

显式选型(硬件/高帧率):
    from od_platform.frame_source import create_frame_source, CameraConfig
    with create_frame_source(CameraConfig(fps=90, backend="msmf")) as src:
        ...
"""
from __future__ import annotations

__version__ = "0.2.0-lite"

# ── core: 类型 / 配置 / 协议 / 注册表 ──
from .core import (
    SourceType, FrameInfo, Frame, CameraIntrinsics,
    IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, STREAM_SCHEMES, is_stream_url,
    SourceConfig, CameraConfig, VideoConfig, ImageConfig, ImageFolderConfig,
    CameraBackend, CameraCodec,
    FrameSource,
    register_source, build_from_config,
)

# ── sources: import 即触发四个内置源自注册(勿删)──
from .sources import CameraSource, VideoSource, ImageSource, ImageFolderSource

# ── factory: 主入口 ──
from .factory import create_frame_source

__all__ = [
    "__version__",
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
    # 内置源
    "CameraSource", "VideoSource", "ImageSource", "ImageFolderSource",
    # 工厂
    "create_frame_source",
]
