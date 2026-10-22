#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : factory.py
# @Project   : ODPlatform / frame_source
# @Function  : 便捷工厂 —— str|config 收口到注册表
"""
便捷工厂(精简版): frame_source 对外的主入口, 只有 create_frame_source 一个。

输入是 SourceConfig → 交给 build_from_config;
输入是 str         → 用一个直白的 if/else 翻译成 config, 再走同一条派发。

字符串规则(精简版: 不做 matcher 注册/仲裁, 就按顺序判断):
    rtsp:// rtmp:// http:// https://    → VideoConfig(网络流)
    *.mp4 *.avi *.mov ...               → VideoConfig
    *.jpg *.png ...                     → ImageConfig
    已存在的目录                         → ImageFolderConfig
    裸数字 "0"/"1"/...                  → CameraConfig(默认彩色 webcam)
"""
from __future__ import annotations

from pathlib import Path

from .core.base     import FrameSource
from .core.config   import (
    CameraConfig, ImageConfig, ImageFolderConfig, SourceConfig, VideoConfig,
)
from .core.registry import build_from_config
from .core.types    import (
    IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, is_stream_url,
)

# 触发四个内置源的自注册(删掉这行, 工厂就查不到任何源)
from . import sources as _sources  # noqa: F401


def _config_from_string(source: str) -> SourceConfig:
    """把一个源字符串翻译成对应的 config。认不出就抛 ValueError。"""
    if is_stream_url(source):
        return VideoConfig(path=source)

    suffix = Path(source).suffix.lower()
    if suffix in VIDEO_EXTENSIONS:
        return VideoConfig(path=source)
    if suffix in IMAGE_EXTENSIONS:
        return ImageConfig(path=source)
    if Path(source).is_dir():
        return ImageFolderConfig(path=source)
    if source.isdigit():
        return CameraConfig(camera_id=int(source))

    raise ValueError(
        f"无法识别的源字符串: {source!r}。"
        f"支持: 裸数字(摄像头) / 视频后缀 {sorted(VIDEO_EXTENSIONS)} / "
        f"图片后缀 {sorted(IMAGE_EXTENSIONS)} / 已存在目录 / 网络流 URL。"
        f"硬件或内存源请显式传对应 config。"
    )


def create_frame_source(source: str | SourceConfig) -> FrameSource:
    """
    创建一个帧源(最常用入口)。

    Args:
        source: 字符串糖("0"/"x.mp4"/"rtsp://..."/"./imgs")或显式 config
                (CameraConfig(...) / VideoConfig(...) / ImageConfig(...) / ...)。

    Returns:
        尚未 open 的 FrameSource; 建议用 with 使用。

    Raises:
        TypeError : source 既不是 str 也不是 SourceConfig。
        ValueError: 字符串无法识别; 或命中的源在构造 config 时校验失败(路径不存在等)。
    """
    if isinstance(source, SourceConfig):
        return build_from_config(source)
    if isinstance(source, str):
        return build_from_config(_config_from_string(source))
    raise TypeError(
        f"source 必须是 str 或 SourceConfig, 收到 {type(source).__name__}。"
        f"内存/硬件源请传对应的 config 对象。"
    )
