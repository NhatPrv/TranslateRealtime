"""Module bộ nhớ đệm (LRU Cache) in-memory an toàn luồng với khóa MD5."""
import hashlib
import threading
from typing import Any, Optional
from cachetools import LRUCache
from config.settings import settings
from utils.logger import app_logger


class TranslationLRUCache:
    """Bộ nhớ đệm LRU lưu kết quả phân tích và dịch để phản hồi 0ms cho văn bản lặp lại."""

    def __init__(self, maxsize: int = settings.cache_max_size):
        self._cache = LRUCache(maxsize=maxsize)
        self._lock = threading.Lock()

    @staticmethod
    def _generate_key(text: str, source_lang: str = "ja", target_lang: str = "vi") -> str:
        """Tạo khóa MD5 duy nhất dựa trên nội dung văn bản và cặp ngôn ngữ."""
        normalized_str = f"{source_lang.strip().lower()}:{target_lang.strip().lower()}:{text.strip()}"
        return hashlib.md5(normalized_str.encode("utf-8")).hexdigest()

    def get(self, text: str, source_lang: str = "ja", target_lang: str = "vi") -> Optional[Any]:
        """Truy xuất kết quả đã lưu trong bộ nhớ đệm nếu tồn tại."""
        key = self._generate_key(text, source_lang, target_lang)
        with self._lock:
            if key in self._cache:
                app_logger.debug(f"[Cache HIT] Khóa: {key} cho chuỗi: '{text[:20]}...'")
                return self._cache[key]
        app_logger.debug(f"[Cache MISS] Khóa: {key}")
        return None

    def set(self, text: str, value: Any, source_lang: str = "ja", target_lang: str = "vi") -> None:
        """Lưu trữ kết quả mới vào bộ nhớ đệm."""
        key = self._generate_key(text, source_lang, target_lang)
        with self._lock:
            self._cache[key] = value
            app_logger.debug(f"[Cache STORE] Đã lưu khóa: {key} (Tổng phần tử cache: {len(self._cache)})")

    def clear(self) -> None:
        """Xóa toàn bộ bản ghi trong bộ nhớ đệm."""
        with self._lock:
            self._cache.clear()
            app_logger.info("[Cache CLEAR] Đã xóa toàn bộ bộ nhớ đệm.")


# Khởi tạo singleton cache toàn cục
global_cache = TranslationLRUCache()
