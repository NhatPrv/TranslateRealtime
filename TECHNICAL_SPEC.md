# TÀI LIỆU KỸ THUẬT VÀ KIẾN TRÚC HỆ THỐNG
# Realtime Screen Snipping Translator & Language Assistant

- **Tên dự án**: Realtime Screen Snipping Translator & Language Assistant
- **Vai trò thiết kế**: Principal Software Architect & Senior Python Engineer
- **Phiên bản kiến trúc**: v1.0.0
- **Ngôn ngữ xử lý**: Nguồn: Tiếng Anh (EN), Tiếng Nhật (JA) | Đích: Tiếng Việt (VI)
- **Hệ điều hành mục tiêu**: Windows 11 (x64)

---

## 1. TỔNG QUAN HỆ THỐNG VÀ MỤC TIÊU (System Overview & Objectives)

### 1.1. Mục tiêu hệ thống
Xây dựng một ứng dụng trợ lý ngôn ngữ và dịch màn hình thời gian thực dạng overlay/HUD, cho phép người dùng khoanh vùng bất kỳ khu vực nào trên màn hình (game, manga/visual novel, tài liệu PDF, trang web, video) và nhận được ngay lập tức:
1. **Phân tích từ vựng & Furigana tức thời (~0ms perceived latency)**: Tách từ (tokenization), trích xuất nguyên thể (lemma), từ loại (Part-of-Speech), và gắn thẻ phiên âm Furigana/IPA cục bộ offline.
2. **Dịch nghĩa ngữ cảnh & giải thích ngữ pháp chuyên sâu**: Sử dụng mô hình ngôn ngữ lớn cục bộ (Local LLM via Ollama - Qwen 2.5) với cấu trúc dữ liệu JSON chuẩn hóa, bảo mật 100% dữ liệu ngoại tuyến mà không phụ thuộc vào kết nối Internet hay chi phí API đám mây.

### 1.2. Cam kết mức dịch vụ về độ trễ (Service Level Agreement - SLA)

| Công đoạn xử lý (Pipeline Stage) | Công nghệ / Engine | SLA Mục tiêu | SLA Ngưỡng tối đa | Cơ chế thực thi |
| :--- | :--- | :--- | :--- | :--- |
| **1. Kích hoạt Overlay & Snipping** | PyQt6 Transparent Window | `<= 15 ms` | `<= 30 ms` | Main UI Thread |
| **2. Chụp khung hình ROI (Capture)** | DXGI Desktop Duplication (`bettercam`) | `<= 5 ms` | `<= 10 ms` | Direct memory copy |
| **3. Tiền xử lý ảnh (Preprocessing)** | OpenCV (`cv2`) | `<= 10 ms` | `<= 25 ms` | CPU Worker Thread |
| **4. Nhận diện chữ (OCR Pipeline)** | RapidOCR ONNX / Manga-OCR | `80 - 150 ms` | `<= 300 ms` | GPU CUDA / ONNX EP |
| **5. Phân tích hình thái (Offline Token)**| `fugashi` + `unidic-lite` + `pykakasi` | `5 - 15 ms` | `<= 30 ms` | CPU In-memory Engine |
| **6. Giao diện hiển thị đợt 1 (Instant HUD)**| PyQt6 Native Signals | `<= 10 ms` | `<= 20 ms` | Hiển thị ngay sau bước 5 |
| **7. Suy luận LLM (Dịch & Ngữ pháp)** | Ollama `qwen2.5:7b-instruct` | `400 - 900 ms` | `<= 1500 ms` | Asynchronous HTTP Worker |
| **Tổng thời gian phản hồi (E2E Latency)**| **Toàn bộ Pipeline** | **~250ms (Offline HUD) / ~1.2s (Hoàn tất LLM)** | Song song hóa hoàn toàn |

---

## 2. RÀNG BUỘC PHẦN CỨNG VÀ MA TRẬN PHÂN BỔ TÀI NGUYÊN (Hardware Constraints & Resource Allocation Matrix)

### 2.1. Cấu hình phần cứng mục tiêu
- **CPU**: Intel Core i9-13900HX (24 cores / 32 threads, gồm 8 Performance-Cores / 16 threads và 16 Efficient-Cores).
- **GPU**: NVIDIA GeForce RTX 4060 Laptop GPU (8GB GDDR6 VRAM, TGP 140W).
- **RAM**: 16GB DDR5 4800/5600 MHz.
- **Lưu trữ**: NVMe PCIe Gen 4 SSD.

### 2.2. Chiến lược phân bổ tải CPU & GPU
1. **CPU Thread Affinity & Core Allocation**:
   - **P-Cores (Performance Cores)**: Dành riêng cho các tác vụ nhạy cảm về độ trễ: Event loop giao diện người dùng (PyQt6 Main Thread), vòng lặp chụp màn hình DXGI capture, và xử lý ma trận ảnh OpenCV.
   - **E-Cores (Efficient Cores)**: Dành cho các tác vụ tính toán nền: Tokenizer offline (`fugashi`/`MeCab`), `asyncio` event loop xử lý mạng HTTP nội bộ tới Ollama daemon, tiến trình IPC shared memory, và Garbage Collection (GC) quét bộ nhớ định kỳ.
2. **GPU VRAM Budget (Ngân sách VRAM nghiêm ngặt: 4.5 GB - 6.0 GB tổng thể)**:
   - Hệ thống đảm bảo **không bao giờ vượt quá 6.0 GB VRAM**, luôn để lại tối thiểu **2.0 GB - 2.5 GB VRAM** trống cho hệ điều hành Windows Desktop Window Manager (DWM) và các tựa game/ứng dụng 3D đang chạy ngầm của người dùng.
3. **RAM Optimization (Bộ nhớ hệ thống 16GB)**:
   - Triệt tiêu hoàn toàn rò rỉ bộ nhớ (zero memory leak): Dữ liệu numpy array từ ảnh chụp màn hình được giải phóng bằng context manager ngay sau khi nạp vào engine OCR.
   - Cache từ vựng trong RAM sử dụng giải thuật LRU Cache với kích thước giới hạn tối đa 500 items (~5MB footprint). Tổng mức chiếm dụng RAM của tiến trình Python không vượt quá **550 MB**.

### 2.3. Ma trận phân bổ tài nguyên chi tiết

| Tác vụ / Module | Thành phần phần cứng | Phân bổ Core / Thiết bị | Ngân sách VRAM | Ngân sách RAM | Ưu tiên CPU (Priority) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PyQt6 GUI & HUD Overlay** | CPU | 1 P-Core (Thread 0) | 0 MB (Direct2D UI) | ~120 MB | `HIGH_PRIORITY_CLASS` |
| **DXGI Screen Capture** | CPU + GPU D3D11 | P-Core + Desktop Surface| ~50 MB | ~40 MB | `HIGH_PRIORITY_CLASS` |
| **Image Preprocessing** | CPU (SIMD AVX2) | 2 P-Cores | 0 MB | ~30 MB (Buffer) | `ABOVE_NORMAL` |
| **RapidOCR (Paddle ONNX)** | GPU (CUDA / TensorRT) | GPU Tensor Cores | ~350 MB - 500 MB | ~150 MB | `NORMAL` |
| **Manga-OCR (ViT PyTorch FP16)**| GPU (CUDA) | GPU CUDA Cores | ~750 MB - 900 MB | ~250 MB | `NORMAL` |
| **MeCab / fugashi / pykakasi**| CPU (Single-threaded) | 1 E-Core | 0 MB | ~80 MB (Dictionary) | `NORMAL` |
| **Ollama Server (Qwen 2.5 7B Q4_K_M)**| GPU (CUDA Offload) | GPU Layers Offloaded | ~4.500 MB - 4.800 MB | ~300 MB (Context) | `BELOW_NORMAL` |
| **Async HTTP Bridge (`httpx`)** | CPU (Asyncio loop) | E-Cores Pool | 0 MB | ~25 MB | `NORMAL` |
| **TỔNG CỘNG HỆ THỐNG** | **CPU + GPU** | **Tối ưu P/E hybrid** | **~5.6 GB VRAM Max** | **~1.0 GB RAM Tổng** | **An toàn tuyệt đối** |

---

## 3. KIẾN TRÚC HỆ THỐNG VÀ SƠ ĐỒ LUỒNG DỮ LIỆU (Architecture & Data Flow Diagram)

Hệ thống được thiết kế theo mô hình **Producer-Consumer** phi đồng bộ đa tầng, kết hợp giữa `multiprocessing` (tiến trình độc lập cho các tác vụ nặng tránh GIL) và `asyncio` (kết nối I/O không khóa cho Ollama Service).

```
   +---------------------------------------------------------------------------------+
   |                                 USER INTERFACE LAYER                            |
   |                                                                                 |
   |  [ Global Hotkey Listener ] ---> ( pynput Thread )                              |
   |             |                                                                   |
   |             v (Qt Signal: Trigger Snipping)                                     |
   |  [ Snipping Overlay Window ] -> ROI Coordinates: (x, y, w, h)                   |
   |             |                                                                   |
   |             +-----------------------+                                           |
   +-------------------------------------|-------------------------------------------+
                                         |
                                         v
   +---------------------------------------------------------------------------------+
   |                             PRODUCER: CAPTURE & OCR                             |
   |                                                                                 |
   |  [ Screen Capture Engine ]                                                      |
   |        |--> DXGI Desktop Duplication (bettercam) -> Raw BGRA Frame              |
   |        +--> Fallback: QScreen::grabWindow                                       |
   |             |                                                                   |
   |  [ CV Preprocessing Engine ]                                                    |
   |        |--> Crop ROI -> Grayscale -> Auto-Contrast -> Noise Reduction           |
   |             |                                                                   |
   |  [ OCR Pipeline Router ]                                                        |
   |        |-- (Language == JA && Manga/Vertical) ----> [ Manga-OCR Engine (CUDA) ] |
   |        +-- (Language == EN || Standard Text) ------> [ RapidOCR ONNX (CUDA)   ] |
   |             |                                                                   |
   |             v OCR Result: Raw Text + BBoxes + Confidence                        |
   +-------------------------------------+-------------------------------------------+
                                         |
                +------------------------+------------------------+
                |                                                 |
                v (Instant Path: ~10ms)                           v (Async Path: ~800ms)
   +------------------------------------+   +----------------------------------------+
   |   OFFLINE LEXICAL ENGINE (CPU)     |   |       LLM TRANSLATION AGENT (GPU)      |
   |                                    |   |                                        |
   |  [ fugashi / MeCab Engine ]        |   |  [ Async HTTP Worker (`httpx`) ]       |
   |    - Unidic Tokenization           |   |    - Check In-Memory LRU Cache         |
   |    - Lemma & POS Tagging           |   |    - Hit: Return Cached Response       |
   |                                    |   |    - Miss: Call Ollama `/api/generate` |
   |  [ pykakasi Kana/Furigana Engine ] |   |                                        |
   |    - Kanji to Hiragana/Katakana    |   |  [ Ollama Server (Qwen 2.5 7B Q4_K_M) ]|
   |    - Generate HTML <ruby> tags     |   |    - System Prompt (Strict JSON Schema)|
   |                                    |   |    - Sentence Translation              |
   |  [ EN Engine (SpaCy / CMUdict) ]   |   |    - Deep Grammar Explanations         |
   |    - Lemmatization & IPA           |   |    - Contextual Vocabulary Nuances     |
   +-----------------+------------------+   +--------------------+-------------------+
                     |                                           |
                     | Tokenized Data Signal                     | LLM Result Signal
                     v                                           v
   +---------------------------------------------------------------------------------+
   |                           CONSUMER: POPUP HUD WINDOW                            |
   |                                                                                 |
   |  [ Stage 1 Display (Instant ~200ms) ]:                                          |
   |    - Show Raw Text with Ruby Furigana instantly                                 |
   |    - Interactive Clickable Tokens with POS badges                               |
   |    - Skeleton Shimmer Effect on Translation & Grammar sections                  |
   |                                                                                 |
   |  [ Stage 2 Display (Complete ~1.0s) ]:                                          |
   |    - Populate Vietnamese Translation smoothly (Fade-in / Stream)                |
   |    - Render Grammar Points breakdown cards with examples                        |
   |    - Actions: Pin/Unpin, Copy Markdown/Text, Audio TTS (Optional)               |
   +---------------------------------------------------------------------------------+
```

---

## 4. ĐẶC TẢ CHI TIẾT CÁC MODULE (Detailed Module Specifications)

### 4.1. Module 1: Global Input & Snipping Tool (`modules/snipping/`)
- **Mục tiêu**: Bắt tổ hợp phím tắt trên toàn hệ điều hành mà không làm đơ ứng dụng khác; kích hoạt lớp phủ màn hình (Overlay) mượt mà không nhấp nháy.
- **Thành phần & Nguyên lý**:
  - `GlobalHotkeyListener`: Chạy trên luồng riêng (`pynput.keyboard`), lắng nghe tổ hợp phím tùy biến (mặc định: `Ctrl + Alt + S` hoặc `Alt + Q`). Khi được kích hoạt, phát tín hiệu `PyQtSignal` tới UI Thread.
  - `SnippingOverlayWidget`: Kế thừa `QWidget`, cờ cửa sổ:
    ```python
    Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool
    ```
  - Thiết lập thuộc tính `Qt.WidgetAttribute.WA_TranslucentBackground` để làm mờ nền màn hình với độ mờ 30% (`#0000004D`).
  - Hỗ trợ màn hình đa độ phân giải (Per-Monitor DPI Aware via `ctypes.windll.shcore.SetProcessDpiAwareness(2)`).
  - Cho phép người dùng kéo thả chuột (Rubber-Band Selection) để xác định vùng hình chữ nhật $ROI = (x, y, w, h)$.
  - Phím tắt thoát tức thời: `Esc` hủy thao tác chụp và ẩn overlay ngay lập tức.

### 4.2. Module 2: Screen Capture & Preprocessing (`modules/capture/`)
- **Mục tiêu**: Lấy dữ liệu điểm ảnh vùng ROI với độ trễ thấp nhất có thể ($< 10ms$) và chuẩn hóa ma trận ảnh cho OCR.
- **Kỹ thuật chụp màn hình**:
  - **Chính (Primary)**: Sử dụng thư viện `bettercam` (DXGI Desktop Duplication API của DirectX 11). Dữ liệu được trích xuất trực tiếp từ VRAM của Desktop Window Manager về bộ nhớ RAM dưới dạng mảng `numpy.ndarray` (BGR) chỉ trong 2-4ms.
  - **Dự phòng (Fallback)**: `QScreen.grabWindow(0, x, y, w, h)` khi ứng dụng chạy trên môi trường không hỗ trợ DXGI.
- **Pipeline tiền xử lý ảnh (`ImagePreprocessor`)**:
  1. **Crop**: Cắt ma trận ảnh theo tọa độ chính xác của ROI sau khi bù tỉ lệ DPI scaling.
  2. **Kích thước tối thiểu**: Nếu chiều rộng hoặc cao $< 32px$, tự động phóng to nội suy `cv2.INTER_CUBIC` để tránh mất nét chữ.
  3. **Grayscale & Adaptive Binarization**:
     - Áp dụng `cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)`.
     - Áp dụng thuật toán Otsu thresholding hoặc CLAHE (Contrast Limited Adaptive Histogram Equalization) khi ảnh có độ tương phản thấp.
  4. **Border Padding**: Thêm đệm viền trắng/đen 10px (`cv2.copyMakeBorder`) xung quanh giúp mô hình OCR không bị cắt xén biên ký tự.

### 4.3. Module 3: OCR Engine Pipeline (`modules/ocr/`)
- **Mục tiêu**: Nhận diện ký tự chính xác cao trên cả văn bản in ngang (game/web) và văn bản in dọc (Manga/Light Novel).
- **Chiến lược Dual-Engine**:
  - **Engine A: RapidOCR (PaddleOCR ONNX Runtime)**:
    - *Ứng dụng*: Chữ tiếng Anh và chữ tiếng Nhật in ngang tiêu chuẩn.
    - *Runtime*: `onnxruntime-gpu` với `CUDAExecutionProvider` hoặc `DirectMLExecutionProvider`.
    - *Độ trễ*: ~60 - 120ms.
  - **Engine B: Manga-OCR**:
    - *Ứng dụng*: Chữ tiếng Nhật in dọc, phông chữ viết tay, phông cách điệu trong manga/visual novel.
    - *Kiến trúc*: Vision Transformer (ViT) fine-tuned, chạy ở chế độ FP16 (Half Precision) trên CUDA.
    - *Độ trễ*: ~150 - 250ms.
- **Router Logic**:
  - Cho phép người dùng chọn cấu hình ưu tiên trên HUD hoặc tự động phân luồng dựa trên tỉ lệ khung hình (Khung hình cao gấp đôi rộng $\rightarrow$ ưu tiên text dọc với Manga-OCR).

### 4.4. Module 4: Morphological & Lexical Analysis (`modules/lexical/`)
- **Mục tiêu**: Phân tích từ loại và tạo Furigana hoàn toàn ngoại tuyến với độ trễ $< 15ms$, hiển thị ngay lập tức lên UI trước khi LLM hoàn tất.
- **Tiếng Nhật (Japanese Engine)**:
  - **Bộ tách từ (Morphological Analyzer)**: Sử dụng `fugashi` (Python wrapper tối ưu của MeCab viết bằng C++) kết hợp từ điển thu nhỏ `unidic-lite`.
  - **Trích xuất thông tin**:
    - `surface`: Từ gốc trong văn bản.
    - `lemma`: Dạng nguyên thể tra từ điển (ví dụ: 食べました $\rightarrow$ 食べる).
    - `pos`: Từ loại (Danh từ, Động từ, Tính từ, Trợ từ...).
    - `pronunciation / reading`: Âm đọc Katakana chuẩn từ UniDic.
  - **Tạo Furigana tự động (`pykakasi`)**:
    - Tự động so khớp Kanji và âm Hiragana tương ứng, sinh chuỗi HTML Ruby format:
      `<ruby>私<rt>わたし</rt></ruby>は<ruby>日本語<rt>にほんご</rt></ruby>を<ruby>勉強<rt>べんきょう</rt></ruby>する`
- **Tiếng Anh (English Engine)**:
  - Tách từ, trích xuất Lemma và POS thông qua SpaCy offline model (`en_core_web_sm`).
  - Tra cứu ký âm quốc tế IPA (International Phonetic Alphabet) qua từ điển offline CMUdict.

### 4.5. Module 5: LLM Translation & Grammar Agent (`modules/llm/`)
- **Mục tiêu**: Cung cấp bản dịch tự nhiên sang Tiếng Việt và phân tích ngữ pháp theo ngữ cảnh.
- **Cấu hình Ollama Local Server**:
  - **Model khuyến nghị**: `qwen2.5:7b-instruct` (chất lượng dịch Nhật - Việt và Anh - Việt vượt trội) hoặc `qwen2.5:3b-instruct` (cho chế độ siêu nhẹ tiết kiệm VRAM).
  - **Tham số vận hành**:
    - `keep_alive: "15m"`: Giữ mô hình trong VRAM sau mỗi lần gọi để loại bỏ thời gian tải mô hình (~3 giây).
    - `num_ctx: 2048`: Giới hạn ngữ cảnh 2K tokens đủ cho đoạn văn bản chụp màn hình, tiết kiệm đáng kể KV Cache VRAM (~300MB).
    - `temperature: 0.2`: Giảm độ ngẫu nhiên, đảm bảo đầu ra nhất quán, chính xác.
- **Strict JSON Output & Async HTTP Worker**:
  - Sử dụng `httpx.AsyncClient` kết nối tới `POST http://127.0.0.1:11434/api/generate` với tham số `"format": "json"`.
  - Ép kiểu định dạng trả về qua Pydantic schema nghiêm ngặt.
- **Bộ nhớ đệm thông minh (In-Memory LRU Cache)**:
  - Khóa cache: `MD5(raw_text.strip() + "_" + source_lang)`.
  - Nếu người dùng khoanh lại đoạn text cũ hoặc di chuyển qua lại trong game, kết quả trả về ngay trong $0ms$.

### 4.6. Module 6: Popup Display UI HUD (`modules/ui/`)
- **Mục tiêu**: Hiển thị kết quả trực quan, hiện đại, nổi trên cửa sổ game/ứng dụng mà không làm mất focus.
- **Thiết kế giao diện (Dark Glassmorphism Theme)**:
  - Nền mờ kính tối màu: `rgba(22, 27, 34, 0.92)` với viền cong nhẹ $12px$, đổ bóng tinh tế.
  - Cờ cửa sổ: `Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.SubWindow`.
- **Cấu trúc phân vùng hiển thị**:
  1. **Header Bar**: Hiển thị ngôn ngữ phát hiện, nút Ghim ghim cửa sổ (Pin/Unpin), nút Đóng, nút Sao chép toàn bộ kết quả.
  2. **Section 1 - Văn bản gốc & Phiên âm (Original & Ruby View)**:
     - Dùng `QTextBrowser` hỗ trợ HTML tags `<ruby>` để hiển thị Furigana chuẩn xác trên đầu chữ Hán.
     - Cho phép click vào từng token từ vựng để xem nhanh nghĩa và từ loại.
  3. **Section 2 - Bản dịch tiếng Việt (Translation Card)**:
     - Hiệu ứng Skeleton Loading lúc chờ Ollama.
     - Cập nhật mượt mà khi nhận được tín hiệu hoàn thành từ luồng Async.
  4. **Section 3 - Phân tích ngữ pháp (Grammar Breakdown)**:
     - Danh sách thẻ (Cards) giải thích cấu trúc ngữ pháp quan trọng trong câu, ý nghĩa và ví dụ tương tự.

---

## 5. ĐẶC TẢ DỮ LIỆU & SCHEMAS (Data Contracts / Schemas)

### 5.1. Dữ liệu trung gian giữa OCR và Phân tích hình thái (`OCRResult`)
```python
from pydantic import BaseModel, Field
from typing import List, Tuple, Optional

class OCRBoundingBox(BaseModel):
    x: int
    y: int
    w: int
    h: int

class OCRTextLine(BaseModel):
    text: str
    confidence: float
    bbox: OCRBoundingBox

class OCRResult(BaseModel):
    raw_text: str = Field(..., description="Văn bản ghép hoàn chỉnh")
    lines: List[OCRTextLine]
    source_lang: str = Field("ja", description="'ja' hoặc 'en'")
    orientation: str = Field("horizontal", description="'horizontal' hoặc 'vertical'")
```

### 5.2. Dữ liệu phân tích từ vựng Offline (`TokenItem` & `LexicalAnalysisResult`)
```python
class TokenItem(BaseModel):
    surface: str = Field(..., description="Từ gốc trong câu")
    lemma: str = Field(..., description="Nguyên thể tra từ điển")
    pos: str = Field(..., description="Từ loại (Danh từ, Động từ...)")
    reading_kana: Optional[str] = Field(None, description="Cách đọc Hiragana/Katakana")
    romaji_or_ipa: Optional[str] = Field(None, description="Phiên âm Romaji hoặc IPA")
    furigana_html: Optional[str] = Field(None, description="Chuỗi định dạng <ruby> HTML")

class LexicalAnalysisResult(BaseModel):
    formatted_html_text: str
    tokens: List[TokenItem]
```

### 5.3. Schema bắt buộc cho LLM Ollama (`LLMResponseContract`)
```python
class LLMVocabItem(BaseModel):
    word: str = Field(..., description="Từ vựng cần chú ý")
    reading: str = Field(..., description="Cách phát âm/phiên âm")
    vietnamese_meaning: str = Field(..., description="Nghĩa trong ngữ cảnh câu")
    nuance: Optional[str] = Field(None, description="Sắc thái ngữ nghĩa đặc biệt")

class LLMGrammarItem(BaseModel):
    pattern: str = Field(..., description="Mẫu ngữ pháp (ví dụ: ～てたまらない)")
    explanation: str = Field(..., description="Giải thích ý nghĩa và cách dùng trong câu")
    example: Optional[str] = Field(None, description="Một ví dụ minh họa tương đương")

class LLMResponseContract(BaseModel):
    vietnamese_translation: str = Field(..., description="Bản dịch tiếng Việt tự nhiên và chuẩn xác")
    vocabulary: List[LLMVocabItem] = Field(default_factory=list)
    grammar_points: List[LLMGrammarItem] = Field(default_factory=list)
    context_notes: Optional[str] = Field(None, description="Ghi chú thêm về bối cảnh văn hóa/xưng hô")
```

### 5.4. System Prompt cấu hình cho Qwen 2.5
```text
Bạn là chuyên gia ngôn ngữ học Nhật - Việt và Anh - Việt cao cấp. 
Nhiệm vụ của bạn là nhận văn bản trích xuất từ màn hình, dịch chính xác sang tiếng Việt và phân tích ngữ pháp, từ vựng chuyên sâu.

QUY TẮC BẮT BUỘC:
1. Chỉ phản hồi DUY NHẤT một đối tượng JSON hợp lệ tuân thủ Schema sau. Tuyệt đối không thêm lời mở đầu hay kết luận.
2. Bản dịch tiếng Việt phải mượt mà, đúng ngữ cảnh (đặc biệt trong game, manga, hội thoại).
3. Nếu là tiếng Nhật, phân tích rõ trợ từ, thể động từ và kính ngữ/thân mật.

JSON Schema:
{
  "vietnamese_translation": "string",
  "vocabulary": [
    {"word": "string", "reading": "string", "vietnamese_meaning": "string", "nuance": "string"}
  ],
  "grammar_points": [
    {"pattern": "string", "explanation": "string", "example": "string"}
  ],
  "context_notes": "string hoặc null"
}
```

---

## 6. CẤU TRÚC DỰ ÁN MÃ NGUỒN (Project Clean Architecture)

```
TranslateRealtime/
├── .gitignore
├── README.md
├── TECHNICAL_SPEC.md
├── requirements.txt
├── config/
│   ├── __init__.py
│   ├── app_config.yaml           # Cấu hình phím tắt, cổng Ollama, ngưỡng VRAM
│   └── settings.py               # Pydantic BaseSettings quản lý cấu hình tập trung
├── src/
│   ├── __init__.py
│   ├── main.py                   # Điểm khởi chạy ứng dụng (Entrypoint)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── app_context.py        # Quản lý trạng thái chia sẻ (State Management)
│   │   ├── event_bus.py          # Event-driven pub/sub điều phối tín hiệu
│   │   └── thread_manager.py     # Quản lý QThreadPool và Multiprocessing Pool
│   ├── engines/
│   │   ├── __init__.py
│   │   ├── capture/
│   │   │   ├── __init__.py
│   │   │   ├── dxgi_capture.py   # Bettercam DXGI Screen grabber
│   │   │   └── preprocessor.py   # OpenCV binarization, contrast, padding
│   │   ├── ocr/
│   │   │   ├── __init__.py
│   │   │   ├── base_ocr.py       # Abstract Base Class cho OCR engines
│   │   │   ├── rapid_ocr.py      # RapidOCR CUDA / DirectML engine
│   │   │   └── manga_ocr.py      # Manga-OCR Vision Transformer engine
│   │   ├── lexical/
│   │   │   ├── __init__.py
│   │   │   ├── ja_analyzer.py    # fugashi + unidic + pykakasi Furigana
│   │   │   └── en_analyzer.py    # SpaCy + CMUdict IPA
│   │   └── llm/
│   │       ├── __init__.py
│   │       ├── ollama_client.py  # Async HTTP client giao tiếp Ollama API
│   │       ├── prompt_builder.py # Quản lý templates & JSON Schemas
│   │       └── response_cache.py # In-Memory LRU Cache
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schemas.py            # Pydantic schemas (Contracts)
│   │   └── dtos.py               # Data Transfer Objects nội bộ PyQt
│   └── ui/
│       ├── __init__.py
│       ├── styles/
│       │   └── theme.qss         # StyleSheet Dark Glassmorphism chuẩn
│       ├── hotkey/
│       │   └── listener.py       # pynput keyboard hook worker
│       ├── overlay/
│       │   └── snipping_tool.py  # Lớp phủ chụp màn hình trong suốt
│       └── hud/
│           ├── result_window.py  # Cửa sổ Popup HUD chính
│           ├── components/
│           │   ├── ruby_viewer.py# Widget render HTML <ruby> tags
│           │   ├── vocab_card.py # Thẻ hiển thị từ vựng tương tác
│           │   └── shimmer.py    # Hiệu ứng Skeleton loader khi đợi LLM
└── tests/
    ├── test_capture.py           # Benchmark tốc độ chụp DXGI
    ├── test_ocr.py               # Benchmark độ chính xác & độ trễ OCR
    ├── test_lexical.py           # Kiểm thử độ trễ bộ phân tích MeCab/fugashi
    └── test_llm_json.py          # Kiểm thử tính hợp lệ JSON từ Ollama
```

---

## 7. LỘ TRÌNH TRIỂN KHAI VÀ BENCHMARK (Implementation Roadmap)

### 7.1. Kế hoạch chia pha phát triển (3 Pha)
- **Pha 1: MVP Core Pipeline (Xây dựng nền móng xử lý)**:
  - Thiết lập môi trường, cấu hình `requirements.txt`.
  - Triển khai Module Capture (DXGI) + RapidOCR + Tokenizer ngoại tuyến (`fugashi`/`pykakasi`).
  - Viết module kết nối Ollama Async kiểm tra tính chuẩn xác của JSON output.
  - Kiểm thử dòng dữ liệu tuần tự End-to-End từ ảnh ra JSON.
- **Pha 2: Tích hợp Giao diện & Trải nghiệm Người dùng (UI/UX Realtime HUD)**:
  - Xây dựng lớp phủ Snipping Tool với cơ chế DPI-aware trên PyQt6.
  - Thiết kế cửa sổ Popup HUD với giao diện kính mờ hiện đại, hiển thị tức thì Furigana HTML.
  - Tích hợp Skeleton loading và streaming kết quả dịch từ Ollama.
  - Tích hợp phím tắt toàn cục và bộ nhớ đệm LRU Cache.
- **Pha 3: Tối ưu Phần cứng Chuyên sâu & Đóng gói (Hardening & Packaging)**:
  - Khóa luồng CPU Affinity (gán P-Cores cho Capture/GUI, E-Cores cho Worker).
  - Benchmark chi tiết mức chiếm dụng VRAM của Ollama + OCR (đảm bảo $\le 6.0 GB$).
  - Đóng gói ứng dụng thành file thực thi độc lập (Standalone `.exe`) bằng **Nuitka** (biên dịch C cho Python nhằm tăng tốc tối đa và bảo vệ mã nguồn).

### 7.2. Tiêu chí kiểm thử Benchmark (Acceptance Criteria)

| Chỉ số kiểm thử | Mức đạt chuẩn (Pass) | Mức tối ưu (Excellent) |
| :--- | :--- | :--- |
| **Tốc độ chụp DXGI** | $\le 10 ms$ | $\le 4 ms$ |
| **Độ trễ OCR RapidOCR** | $\le 180 ms$ | $\le 90 ms$ |
| **Độ trễ sinh Furigana offline**| $\le 20 ms$ | $\le 8 ms$ |
| **Tổng thời gian hiện HUD Stage 1** | $\le 300 ms$ | $\le 180 ms$ |
| **Tổng thời gian xong bản dịch LLM**| $\le 1500 ms$ | $\le 900 ms$ |
| **Mức chiếm dụng VRAM tối đa** | $\le 6.0 GB$ | $\le 5.2 GB$ |
| **Mức chiếm dụng RAM tối đa** | $\le 650 MB$ | $\le 450 MB$ |
| **Tỉ lệ lỗi phân tích JSON từ LLM**| $\le 1\%$ | $0\%$ (nhờ strict schema) |

---

## 8. CODE SKELETON MINH HỌA QUAN TRỌNG

### 8.1. DXGI Screen Capture với `bettercam` (`dxgi_capture.py`)
```python
import bettercam
import numpy as np
from typing import Optional, Tuple

class DXGIScreenCapture:
    def __init__(self, output_idx: int = 0):
        # Khởi tạo camera bắt màn hình với DXGI Desktop Duplication API
        self.camera = bettercam.create(output_idx=output_idx, output_color="BGR")

    def capture_roi(self, region: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """
        Chụp nhanh vùng ROI = (left, top, right, bottom) với độ trễ ~3ms
        """
        left, top, right, bottom = region
        # bettercam grab trực tiếp frame từ memory surface
        frame = self.camera.grab(region=(left, top, right, bottom))
        if frame is None:
            # Lấy frame mới nhất nếu grab chưa sẵn sàng
            frame = self.camera.get_latest_frame()
            if frame is not None:
                frame = frame[top:bottom, left:right]
        return frame
```

### 8.2. Bộ phân tích Furigana Tiếng Nhật tức thời (`ja_analyzer.py`)
```python
import fugashi
import pykakasi
from typing import List
from models.schemas import TokenItem, LexicalAnalysisResult

class JapaneseLexicalAnalyzer:
    def __init__(self):
        # Khởi tạo fugashi MeCab tagger với unidic-lite
        self.tagger = fugashi.Tagger()
        # Khởi tạo pykakasi để chuyển đổi Kanji sang Kana
        self.kakasi = pykakasi.kakasi()

    def analyze(self, text: str) -> LexicalAnalysisResult:
        tokens: List[TokenItem] = []
        html_parts: List[str] = []

        for word in self.tagger(text):
            surface = word.surface
            feature = word.feature
            lemma = feature.lemma if hasattr(feature, "lemma") and feature.lemma else surface
            pos = feature.pos1 if hasattr(feature, "pos1") else "Unknown"

            # Tra cứu cách đọc và tạo thẻ Ruby nếu từ có chứa Kanji
            conversion = self.kakasi.convert(surface)
            has_kanji = any(item['orig'] != item['kana'] for item in conversion)

            if has_kanji:
                kana_reading = "".join(item['hira'] for item in conversion)
                ruby_html = f"<ruby>{surface}<rt>{kana_reading}</rt></ruby>"
                html_parts.append(ruby_html)
            else:
                kana_reading = surface
                html_parts.append(surface)

            tokens.append(TokenItem(
                surface=surface,
                lemma=lemma,
                pos=pos,
                reading_kana=kana_reading,
                furigana_html=ruby_html if has_kanji else None
            ))

        formatted_html = "".join(html_parts)
        return LexicalAnalysisResult(formatted_html_text=formatted_html, tokens=tokens)
```

### 8.3. Async Ollama Client với JSON Contract (`ollama_client.py`)
```python
import httpx
import json
from typing import Optional
from models.schemas import LLMResponseContract

class OllamaTranslationAgent:
    def __init__(self, base_url: str = "http://127.0.0.1:11434", model_name: str = "qwen2.5:7b-instruct"):
        self.base_url = base_url
        self.model_name = model_name
        self.endpoint = f"{self.base_url}/api/generate"
        self.system_prompt = (
            "Bạn là trợ lý dịch thuật cao cấp. Dịch sang tiếng Việt và phân tích ngữ pháp, từ vựng. "
            "Chỉ xuất duy nhất chuỗi JSON hợp lệ theo schema: "
            '{"vietnamese_translation": "...", "vocabulary": [{"word":"..","reading":"..","vietnamese_meaning":".."}], "grammar_points": [{"pattern":"..","explanation":".."}]}'
        )

    async def translate_and_explain(self, text: str, source_lang: str = "ja") -> Optional[LLMResponseContract]:
        user_prompt = f"Ngôn ngữ nguồn: {source_lang}\nVăn bản: {text}"
        payload = {
            "model": self.model_name,
            "prompt": user_prompt,
            "system": self.system_prompt,
            "stream": False,
            "format": "json",
            "keep_alive": "15m",
            "options": {
                "temperature": 0.2,
                "num_ctx": 2048
            }
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(self.endpoint, json=payload)
            response.raise_for_status()
            data = response.json()
            raw_json_str = data.get("response", "{}")
            parsed_dict = json.loads(raw_json_str)
            return LLMResponseContract.model_validate(parsed_dict)
```

---

## 9. HƯỚNG DẪN CÀI ĐẶT MÔI TRƯỜNG PHÁT TRIỂN (Setup Guide)

### Bước 1: Khởi tạo Virtual Environment
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Bước 2: Cài đặt Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Bước 3: Cài đặt và kéo mô hình Ollama
```bash
# Tải và chạy Ollama trên Windows, sau đó mở Terminal:
ollama pull qwen2.5:7b-instruct

# Kiểm tra GPU offload
ollama run qwen2.5:7b-instruct "Xin chào"
```

---
*Tài liệu này đóng vai trò là kim chỉ nam kỹ thuật (Single Source of Truth) trong suốt vòng đời phát triển dự án.*
