#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : image.py
# @Project   : ODPlatform / frame_source
# @Function  : 图片源 —— 单张图片 (ImageSource) + 图片文件夹 (ImageFolderSource)
"""
图片输入源(精简版)。

ImageSource       : 单张图片, read() 只产一帧(第二次返回 None)。
ImageFolderSource : 文件夹, 按排序后的文件列表逐张产出。

统一零拷贝: read() 返回的 Frame.image 直接引用底层数组, 调用方需持久保存自行 .copy()。
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import cv2

from ..core.base     import FrameSource
from ..core.config   import ImageConfig, ImageFolderConfig
from ..core.registry import register_source
from ..core.types    import Frame, FrameInfo, SourceType, IMAGE_EXTENSIONS


logger = logging.getLogger(__name__)


@register_source(ImageConfig)
class ImageSource(FrameSource):
    """单张图片源。read() 只产一帧。"""

    def __init__(self, config: ImageConfig):
        super().__init__(config)
        self._path: str = config.path
        self._image: Optional["cv2.typing.MatLike"] = None
        self._read_count: int = 0

    def open(self) -> bool:
        # 复位位置状态(兑现"重新 open 即重头"契约)
        self._read_count = 0
        self._frame_index = 0

        self._image = cv2.imread(self._path)
        if self._image is None:
            logger.error(f"无法读取图片: {self._path}")
            return False
        return True

    def read(self) -> Optional[Frame]:
        if self._image is None:
            return None
        if self._read_count > 0:
            return None
        self._read_count += 1

        h, w = self._image.shape[:2]
        info = FrameInfo(
            width=w, height=h,
            source_type=SourceType.IMAGE,
            source_path=self._path,
            frame_index=0, total_frames=1,
            timestamp=0.0,                       # 图片无时间概念
            filename=Path(self._path).name,
        )
        # 零拷贝: 与其它源一致, 调用方需持久保存自行 .copy()
        return Frame(image=self._image, info=info)

    def close(self) -> None:
        self._image = None

    def get_source_type(self) -> SourceType:
        return SourceType.IMAGE


@register_source(ImageFolderConfig)
class ImageFolderSource(FrameSource):
    """图片文件夹源。按排序后的文件列表逐张产出。"""

    def __init__(self, config: ImageFolderConfig):
        super().__init__(config)
        self._folder: str = config.path
        self._files: list[Path] = []

    def open(self) -> bool:
        # 复位位置状态
        self._frame_index = 0

        folder = Path(self._folder)
        # 过滤(后缀小写)+ 排序(帧序稳定可复现)
        self._files = sorted(
            p for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        )
        if not self._files:
            logger.warning(f"文件夹内没有支持的图片: {self._folder}")
            return False
        logger.info(f"文件夹共 {len(self._files)} 张图片: {self._folder}")
        return True

    def read(self) -> Optional[Frame]:
        # 跳过读不出的坏图, 直到读到一张或耗尽
        while self._frame_index < len(self._files):
            path = self._files[self._frame_index]
            img = cv2.imread(str(path))
            if img is None:
                logger.warning(f"跳过无法读取的图片: {path}")
                self._frame_index += 1
                continue

            idx = self._frame_index
            self._frame_index += 1

            h, w = img.shape[:2]
            info = FrameInfo(
                width=w, height=h,
                source_type=SourceType.IMAGE_FOLDER,
                source_path=self._folder,
                frame_index=idx, total_frames=len(self._files),
                timestamp=0.0,
                filename=path.name,
            )
            return Frame(image=img, info=info)   # 零拷贝

        return None

    def close(self) -> None:
        self._files = []

    def get_source_type(self) -> SourceType:
        return SourceType.IMAGE_FOLDER
