"""Module quản lý cấu hình tập trung cho toàn bộ ứng dụng."""
from pathlib import Path
from pydantic import BaseModel, Field


class ScreenCaptureConfig(BaseModel):
    """Cấu hình bộ chụp màn hình DXGI."""
    device_index: int = Field(default=0, description="Chỉ số màn hình DirectX/DXGI")
    output_color: str = Field(default="BGR", description="Hệ màu trả về cho OpenCV")
    max_buffer_frames: int = Field(default=2, description="Giới hạn hàng đợi khung hình tránh ngốn RAM")


class OCRConfig(BaseModel):
    """Cấu hình các bộ nhận diện ký tự quang học."""
    use_gpu: bool = Field(default=True, description="Kích hoạt CUDA/DirectML cho OCR")
    use_manga_ocr_for_vertical: bool = Field(default=True, description="Dùng Manga-OCR cho văn bản tiếng Nhật in dọc")
    rapid_ocr_det_limit_side: int = Field(default=960, description="Kích thước tối đa cạnh ảnh cho detection")
    min_confidence: float = Field(default=0.4, description="Ngưỡng tin cậy tối thiểu để nhận chữ")


class LLMConfig(BaseModel):
    """Cấu hình kết nối Ollama và ràng buộc suy luận."""
    base_url: str = Field(default="http://localhost:11434", description="URL Ollama daemon nội bộ")
    model_name: str = Field(default="qwen2.5:3b", description="Mô hình LLM đích")
    timeout_seconds: float = Field(default=12.0, description="Thời gian timeout tối đa cho HTTP request")
    keep_alive: str = Field(default="-1", description="Giữ mô hình liên tục trong VRAM tránh reload")
    temperature: float = Field(default=0.2, description="Nhiệt độ sinh dữ liệu thấp để đảm bảo ổn định")
    num_predict: int = Field(default=400, description="Giới hạn token sinh để đạt SLA dưới 1.2s")
    num_ctx: int = Field(default=2048, description="Ngữ cảnh 2K tokens đủ cho đoạn trích màn hình")


class UIConfig(BaseModel):
    """Cấu hình giao diện và phím tắt toàn cục."""
    global_hotkey: str = Field(default="<alt>+q", description="Phím tắt kích hoạt lớp phủ Snipping")
    overlay_opacity: float = Field(default=0.35, description="Độ mờ của lớp phủ màn hình")
    hud_width: int = Field(default=520, description="Chiều rộng mặc định của Popup HUD")
    hud_max_height: int = Field(default=680, description="Chiều cao tối đa của Popup HUD")
    stay_on_top: bool = Field(default=True, description="Cửa sổ HUD luôn nổi trên các ứng dụng khác")


class AppConfig(BaseModel):
    """Cấu hình tổng thể của dự án."""
    app_name: str = "TranslateRealtime"
    version: str = "1.0.0"
    base_dir: Path = Path(__file__).resolve().parent.parent
    logs_dir: Path = base_dir / "logs"

    # Hardware resource budgets
    max_vram_gb: float = Field(default=6.0, description="Ngưỡng an toàn VRAM trên RTX 4060 8GB")
    cache_max_size: int = Field(default=500, description="Số lượng bản ghi tối đa trong LRU Cache")

    # Sub-configurations
    capture: ScreenCaptureConfig = Field(default_factory=ScreenCaptureConfig)
    ocr: OCRConfig = Field(default_factory=OCRConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    ui: UIConfig = Field(default_factory=UIConfig)


# Khởi tạo singleton cấu hình toàn cục
settings = AppConfig()
