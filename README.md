# Realtime Screen Snipping Translator & Language Assistant

Ứng dụng hỗ trợ chụp quét màn hình thời gian thực (Screen Snipping), nhận diện ký tự quang học (OCR đa ngôn ngữ Anh - Nhật), phân tích hình thái học từ vựng (Morphological Analysis, Furigana ~0ms) và dịch nghĩa, giải thích ngữ pháp chuyên sâu thông qua Local LLM (Ollama - Qwen 2.5).

---

## 📌 Tài liệu Kỹ thuật & Kiến trúc (Technical Specification)

Tài liệu thiết kế kiến trúc toàn diện của dự án được lưu trữ chi tiết tại:
👉 **[TECHNICAL_SPEC.md](TECHNICAL_SPEC.md)**

Nội dung tài liệu bao gồm:
1. **System Overview & SLA**: Mục tiêu, phạm vi và bảng chuẩn độ trễ từng công đoạn.
2. **Hardware Constraints & Resource Matrix**: Chiến lược phân bổ tải tối ưu cho cấu hình phần cứng đích:
   - **CPU**: Intel Core i9-13900HX (Phân bổ P-Core & E-Core).
   - **GPU**: NVIDIA GeForce RTX 4060 Laptop 8GB VRAM (Ngân sách VRAM kiểm soát chặt chẽ 4.5GB - 6.0GB).
   - **RAM**: 16GB DDR5 (Chống rò rỉ bộ nhớ, zero memory leak).
3. **Architecture & Data Flow Diagram**: Sơ đồ kiến trúc Producer-Consumer đa tiến trình kết hợp bất đồng bộ (`multiprocessing` + `asyncio`).
4. **Detailed Module Specifications**:
   - Module 1: Global Input & Snipping Tool (PyQt6).
   - Module 2: Screen Capture (DXGI Desktop Duplication / bettercam) & Preprocessing (OpenCV).
   - Module 3: OCR Engine Pipeline (RapidOCR ONNX CUDA/DirectML & Manga-OCR).
   - Module 4: Morphological & Lexical Analysis (MeCab, fugashi, unidic-lite, pykakasi).
   - Module 5: LLM Translation & Grammar Agent (Ollama Local API - Qwen 2.5, Strict JSON Schema, In-Memory LRU Cache).
   - Module 6: Floating HUD Result Display (PyQt6 Glassmorphism, Furigana Ruby render, Skeleton Loader).
5. **Data Contracts & Schemas**: Pydantic models và JSON Schema chuẩn giao tiếp liên module.
6. **Project Structure**: Tổ chức thư mục chuẩn Clean Architecture.
7. **Implementation Roadmap & Benchmarking**: Kế hoạch thực thi 3 pha từ MVP đến đóng gói phân phối.

---

## 🚀 Cài đặt Nhanh (Quick Start)

### 1. Yêu cầu môi trường
- Python 3.10 hoặc 3.11 (64-bit).
- NVIDIA CUDA Toolkit 12.x / cuDNN tương thích với RTX 4060.
- [Ollama](https://ollama.com/) chạy cục bộ với mô hình `qwen2.5:7b-instruct` (hoặc profile `qwen2.5:3b-instruct`).

### 2. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

---

## 📄 Bản quyền
Dự án được phân phối dưới giấy phép MIT License.
