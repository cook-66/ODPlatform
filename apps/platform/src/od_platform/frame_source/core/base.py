#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : base.py
# @Project   : ODPlatform / frame_source
# @Function  : FrameSource 抽象基类 — 统一所有输入源的协议(精简版)
"""
帧源抽象基类(精简版)。只保留跑通推理流水线必需的部分:

    __init__(config)      config 驱动: 源吃 SourceConfig, 不吃裸字符串
    open / read / close   三个抽象方法, 子类必须实现
    get_source_type()     返回源类型(内置枚举或第三方字符串)
    modalities            能力发现: 本源能产哪些平面, 默认 {'image'}
    + 上下文管理器
    + 迭代器

已按精简要求去掉: seek / set_stride(stride 跳采) / end_reason 断线重连语义。
"""
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Iterator, Optional

from .config import SourceConfig
from .types import Frame, SourceType


logger = logging.getLogger(__name__)


class FrameSource(ABC):
    """
    帧源抽象基类(config 驱动)。

    标准用法:
        with SomeSource(some_config) as source:
            for frame in source:
                process(frame.image)
                print(frame.width, frame.height)

    能力发现(开循环前决策):
        if "depth" in source.modalities:
            prepare_pointcloud_pipeline()

    注意:
        同一 source 对象只能迭代一次(标准迭代器协议)。
        需要重头迭代请重新 open() 或重新创建对象。
    """

    def __init__(self, config: SourceConfig):
        self.config       = config
        self.source_path  = config.identity     # 日志/调试用的人类可读标识
        self._frame_index = 0
        self._start_time  = time.time()

    # ── 子类必须实现 ────────────────────────────────────────
    @abstractmethod
    def open(self) -> bool:
        """打开输入源,返回是否成功。实现必须复位位置状态(重新 open 即重头)。"""

    @abstractmethod
    def read(self) -> Optional[Frame]:
        """读取一帧,源耗尽时返回 None。"""

    @abstractmethod
    def close(self) -> None:
        """关闭输入源,释放资源。"""

    @abstractmethod
    def get_source_type(self) -> SourceType:
        """返回输入源类型(内置源返回 SourceType 成员; 第三方源可返回自己的字符串)。"""

    # ── 能力发现(默认只产主图, 多模态源覆盖)────────────────
    @property
    def modalities(self) -> frozenset[str]:
        """
        本源能产出的平面集合。默认 {'image'}(只有主视觉平面)。
        深度源覆盖为 {'image', 'depth'}, 双目源覆盖为 {'image', 'right'} 等。
        供调用方在开循环前决策是否准备额外管线。
        """
        return frozenset({"image"})

    # ── 上下文管理器协议 ────────────────────────────────────
    def __enter__(self) -> "FrameSource":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.close()
        return False  # 不吞异常

    # ── 迭代器协议 ──────────────────────────────────────────
    def __iter__(self) -> Iterator[Frame]:
        return self

    def __next__(self) -> Frame:
        frame = self.read()
        if frame is None:
            raise StopIteration
        return frame
