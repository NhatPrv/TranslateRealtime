"""Module ghi log chuyên dụng sử dụng loguru với định dạng chuẩn hiệu năng cao."""
import sys
from pathlib import Path
from loguru import logger
from config.settings import settings


def setup_logger():
    """Khởi tạo cấu hình logger đa kênh (Console màu + File log xoay vòng)."""
    # Đảm bảo thư mục logs tồn tại
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = settings.logs_dir / "app_{time:YYYY-MM-DD}.log"

    # Xóa handler mặc định của loguru
    logger.remove()

    # Console Handler: Định dạng trực quan, hiển thị microsecond để theo dõi latency SLA
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level="DEBUG",
        colorize=True,
    )

    # File Handler: Ghi log chi tiết, tự động cắt file sau 10MB và giữ trong 7 ngày
    logger.add(
        str(log_file_path),
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        encoding="utf-8",
    )

    return logger


# Khởi tạo instance logger chuẩn
app_logger = setup_logger()
