"""
ImageProvider — LRU cache for numpy image arrays.

Provides a unified interface for SplitterNode to access images
by file path, regardless of whether it's the current scan or
an external file used in a diptych swap.

Eviction is based on total byte size, not item count,
to prevent excessive memory usage with large 16-bit TIFFs.
"""

from collections import OrderedDict
from typing import Optional

import cv2
import numpy as np

from src.core.io.reader import read_image


MAX_CACHE_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB


class ImageProvider:
    """
    LRU cache of numpy arrays keyed by file_path.

    Stores both full-resolution and proxy (downscaled) versions.
    Evicts oldest entries when total memory exceeds MAX_CACHE_BYTES.
    """

    def __init__(self, max_bytes: int = MAX_CACHE_BYTES) -> None:
        self._full_cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self._proxy_cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self._total_bytes: int = 0
        self._max_bytes: int = max_bytes

    def get_image(self, file_path: str, is_proxy: bool = False) -> np.ndarray:
        """
        Returns a numpy array for the given file_path.

        If not cached, reads from disk and caches both full and proxy versions.
        The returned array is a REFERENCE to the cache. Callers MUST .copy()
        before any in-place mutation.

        Args:
            file_path: Absolute path to the image file.
            is_proxy: If True, returns the downscaled proxy version.

        Returns:
            np.ndarray: The image array (reference to cache).
        """
        target_cache = self._proxy_cache if is_proxy else self._full_cache

        if file_path in target_cache:
            # LRU touch: move to end
            self._full_cache.move_to_end(file_path, last=True)
            if file_path in self._proxy_cache:
                self._proxy_cache.move_to_end(file_path, last=True)
            return target_cache[file_path]

        # Cache miss: read from disk
        raw = read_image(file_path)
        if raw is None:
            # Return a tiny black placeholder to avoid crashes
            return np.zeros((16, 16, 3), dtype=np.float32)

        proxy = self._make_proxy(raw, max_dim=1024)

        self._full_cache[file_path] = raw
        self._proxy_cache[file_path] = proxy
        self._total_bytes += raw.nbytes + proxy.nbytes

        self._evict()

        return self._proxy_cache[file_path] if is_proxy else self._full_cache[file_path]

    def inject(self, file_path: str, full: np.ndarray, proxy: np.ndarray) -> None:
        """
        Injects an already-loaded image into the cache.

        Used when MainController creates a FrameContainer — avoids
        redundant disk reads for the currently active image.

        Args:
            file_path: Absolute path to the image file.
            full: Full-resolution numpy array.
            proxy: Downscaled proxy numpy array.
        """
        if file_path not in self._full_cache:
            self._total_bytes += full.nbytes + proxy.nbytes
        self._full_cache[file_path] = full
        self._proxy_cache[file_path] = proxy
        self._full_cache.move_to_end(file_path, last=True)
        self._proxy_cache.move_to_end(file_path, last=True)
        self._evict()

    def _evict(self) -> None:
        """Evicts the oldest entries until total memory is within limits."""
        while self._total_bytes > self._max_bytes and self._full_cache:
            key, arr = self._full_cache.popitem(last=False)
            self._total_bytes -= arr.nbytes
            if key in self._proxy_cache:
                proxy_arr = self._proxy_cache.pop(key)
                self._total_bytes -= proxy_arr.nbytes

    @staticmethod
    def _make_proxy(img: np.ndarray, max_dim: int = 1024) -> np.ndarray:
        """
        Generates a downscaled proxy image.

        Args:
            img: The full-resolution source image.
            max_dim: Maximum dimension (width or height) for the proxy.

        Returns:
            np.ndarray: The downscaled proxy.
        """
        h, w = img.shape[:2]
        scale = max_dim / max(h, w)
        if scale < 1.0:
            new_w, new_h = int(w * scale), int(h * scale)
            return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return img.copy()
