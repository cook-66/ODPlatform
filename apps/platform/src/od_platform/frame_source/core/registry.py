#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : registry.py
# @Project   : ODPlatform / frame_source
# @Function  : 源注册表(精简版) —— 配置类型是派发轴
"""
源注册表(精简版): 只保留 register_source + build_from_config。

派发轴 = 配置类型:
    build_from_config(cfg) 靠 type(cfg) 在 _BY_CONFIG 里一步查到源类。

字符串糖(如 "0" / "x.mp4" / "rtsp://..." / "./imgs")不在本模块做规则仲裁,
由 factory.py 用一个直白的 if/else 翻译成 config 后进来 —— 精简版不做
matcher 打分/优先级/歧义仲裁那套机制。
"""
from __future__ import annotations

import logging
from typing import Callable, TypeVar

from .base   import FrameSource
from .config import SourceConfig


logger = logging.getLogger(__name__)

_SrcT = TypeVar("_SrcT", bound=type[FrameSource])

# 配置类型 → 源类(主派发表)
_BY_CONFIG: dict[type[SourceConfig], type[FrameSource]] = {}


def register_source(config_cls: type[SourceConfig]) -> Callable[[_SrcT], _SrcT]:
    """
    源自注册装饰器。

    Args:
        config_cls: 该源对应的配置类(派发的钥匙, 必填)。

    用法:
        @register_source(VideoConfig)
        class VideoSource(FrameSource): ...

    Raises:
        TypeError : config_cls 不是 SourceConfig 子类, 或被装饰类不是 FrameSource 子类。
        ValueError: 该 config 已被别的源注册(一种配置只能对应一个源)。
    """
    if not (isinstance(config_cls, type) and issubclass(config_cls, SourceConfig)):
        raise TypeError(f"config_cls 必须是 SourceConfig 的子类, 收到: {config_cls!r}")

    def decorator(source_cls: _SrcT) -> _SrcT:
        if not (isinstance(source_cls, type) and issubclass(source_cls, FrameSource)):
            raise TypeError(f"被注册的类必须是 FrameSource 的子类, 收到: {source_cls!r}")

        existing = _BY_CONFIG.get(config_cls)
        if existing is not None and existing is not source_cls:
            raise ValueError(
                f"配置 {config_cls.__name__} 已被 {existing.__name__} 注册, "
                f"拒绝用 {source_cls.__name__} 覆盖(一种配置只能对应一个源)"
            )

        _BY_CONFIG[config_cls] = source_cls
        logger.debug(f"已注册源: {config_cls.__name__} → {source_cls.__name__}")
        return source_cls

    return decorator


def build_from_config(config: SourceConfig) -> FrameSource:
    """
    按配置类型派发, 造出对应的源。这是唯一的"造源"出口。

    Args:
        config: 任意 SourceConfig 子类实例。

    Returns:
        对应的 FrameSource 实例(尚未 open)。

    Raises:
        TypeError : config 不是 SourceConfig 实例。
        ValueError: config 的类型没有被任何源注册。
    """
    if not isinstance(config, SourceConfig):
        raise TypeError(f"build_from_config 需要 SourceConfig 实例, 收到 {type(config).__name__}")

    source_cls = _BY_CONFIG.get(type(config))
    if source_cls is None:
        raise ValueError(
            f"未注册的配置类型: {type(config).__name__}。"
            f"已注册: {sorted(c.__name__ for c in _BY_CONFIG)}"
        )
    return source_cls(config)
