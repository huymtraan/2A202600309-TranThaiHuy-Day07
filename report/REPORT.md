# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Trần Thái Huy  
**Nhóm:** C401-E6  
**Ngày:** 10/4

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**  
Hai đoạn text có high cosine similarity khi embedding của chúng gần nhau về hướng trong không gian vector, tức là có nội dung/chủ đề tương đồng.

**Ví dụ HIGH similarity:**  
- Sentence A: "The cat sits on the mat."  
- Sentence B: "A cat is sitting on a mat."  
- Lý do: cùng mô tả một ý, khác cách diễn đạt.

**Ví dụ LOW similarity:**  
- Sentence A: "The cat sits on the mat."  
- Sentence B: "Quantum computers use qubits."  
- Lý do: khác hoàn toàn chủ đề.

**Tại sao cosine similarity thường dùng hơn Euclidean cho text embedding?**  
Cosine tập trung vào hướng (nghĩa) thay vì độ lớn vector, nên phù hợp hơn cho bài toán so sánh ngữ nghĩa.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**  
`num_chunks = ceil((doc_length - overlap) / (chunk_size - overlap))`  
`= ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = 23`

**Nếu overlap tăng lên 100 thì sao?**  
`= ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 25`  
Overlap lớn hơn làm tăng số chunk nhưng giữ được ngữ cảnh tốt hơn ở ranh giới chunk.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Genetic screening / molecular diagnostics / pediatric tumor factsheets

**Tại sao nhóm chọn domain này?**  
Domain có tài liệu dạng factsheet/whitepaper/guide khá rõ cấu trúc, phù hợp để benchmark chunking + retrieval. Nội dung có cả câu hỏi dễ (fact đơn lẻ) và câu hỏi khó hơn (cần tìm đúng section), giúp đánh giá chất lượng RAG rõ ràng.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự (MD) | Metadata đã gán |
|---|--------------|-------|---------------|-----------------|
| 1 | `01_Prenatal_Genome_White_Paper.pdf` | https://prenatalgenome.it/pdf/PrenatalGenome_WhitePaper.pdf | 13,803 | `file_name, category, source, date` + metadata chunk (`doc_id, source_md, chunk_index, chunk_count, category_primary`) |
| 2 | `02_Alpha_Thalassemia_Fact_Sheet_2022.pdf` | https://static1.squarespace.com/static/5a4f825849fc2bd65e00c9f0/t/6263224e3fed9f6913e49734/1650664015220/Alpha+Thalassemia+Fact+Sheet+2022.pdf | 7,504 | như trên |
| 3 | `03_Mendelian_Inheritance_Lecture_2023.pdf` | https://uomus.edu.iq/img/lectures21/MUCLecture_2023_12931719.pdf | 5,718 | như trên |
| 4 | `04_Brain_Tumours_Factsheet_2022.pdf` | https://www.cclg.org.uk/sites/default/files/2025-02/cclg-brain-tumours-factsheet-2022.pdf | 11,238 | như trên |
| 5 | `05_Dx_Insights_Molecular_Diagnostics.pdf` | https://www.epemed.org/online/www/content2/108/469/3172/listdownloads/3175/507/ENG/dxinsights.pdf | 11,375 | như trên |
| 6 | `06_Non_Invasive_Prenatal_Testing_Fact_Sheet.pdf` | https://www.genetics.edu.au/PDF/Non_invasive_prenatal_testing_fact_sheet-CGE.pdf | 4,709 | như trên |
| 7 | `07_Cancer_Screening_Action_Guide.pdf` | https://www.nachc.org/wp-content/uploads/2023/07/Action-Guide_Cancer-Screening.pdf | 6,083 | như trên |

Tổng độ dài corpus markdown: **60,430 ký tự**.

### Metadata Schema (thực tế đang dùng)

| Trường metadata | Kiểu | Ví dụ giá trị | Vai trò trong retrieval |
|----------------|------|---------------|--------------------------|
| `category` | string | `NIPT;diagnostics;molecular` | Cho phép lọc theo nhóm chủ đề |
| `category_primary` | string | `NIPT` | Lọc nhanh 1 nhãn chính |
| `source` | string (URL) | `https://...` | Trace nguồn tài liệu |
| `date` | string | `2022`, `none` | Phân biệt theo mốc thời gian |
| `doc_id` | string | `01_Prenatal_Genome_White_Paper` | Gắn chunk về đúng document |
| `source_md` | string | `domain_md/01_...md` | Debug truy vết chunk |
| `chunk_index` | int | `18` | Thứ tự chunk trong document |
| `chunk_count` | int | `31` | Tổng chunk của document |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis (đã chạy comparator, `chunk_size=500`)

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| `01_Prenatal_Genome_White_Paper.md` | FixedSizeChunker (`fixed_size`) | 31 | 493.65 | Trung bình |
| `01_Prenatal_Genome_White_Paper.md` | SentenceChunker (`by_sentences`) | 26 | 524.00 | Cao với câu hoàn chỉnh, nhưng phụ thuộc sentence split |
| `01_Prenatal_Genome_White_Paper.md` | RecursiveChunker (`recursive`) | 35 | 392.51 | Khá tốt vì ưu tiên split theo ngữ cảnh |
| `04_Brain_Tumours_Factsheet_2022.md` | FixedSizeChunker | 25 | 497.52 | Trung bình |
| `04_Brain_Tumours_Factsheet_2022.md` | SentenceChunker | 25 | 441.92 | Khá tốt |
| `04_Brain_Tumours_Factsheet_2022.md` | RecursiveChunker | 30 | 372.67 | Tốt |
| `07_Cancer_Screening_Action_Guide.md` | FixedSizeChunker | 14 | 480.93 | Trung bình |
| `07_Cancer_Screening_Action_Guide.md` | SentenceChunker | 12 | 497.83 | Khá tốt |
| `07_Cancer_Screening_Action_Guide.md` | RecursiveChunker | 16 | 378.25 | Tốt |

### Strategy Của Tôi

**Loại:** Sentence chunking (`SentenceChunker`, `max_sentences_per_chunk=3`).

**Mô tả cách hoạt động:**  
Text được tách theo đơn vị câu (có xử lý markdown cơ bản) và gom theo tối đa 3 câu/chunk. Cách này giúp chunk dễ đọc và giữ mạch ý theo câu hơn so với cắt cứng theo ký tự.

**Tại sao tôi chọn tạm strategy này?**  
Theo thống nhất của nhóm, mỗi thành viên nộp 1 kết quả chunking duy nhất; mình chọn sentence chunking để giữ consistency với pipeline nhóm và dễ giải thích trong demo.

### So Sánh: Strategy của tôi vs Baseline (toàn corpus 7 file)

| Strategy | Chunk Count | Avg Length | Doc-hit@3 trên 5 query |
|----------|-------------|------------|-------------------------|
| FixedSize (`chunk_size=500, overlap=50`) | 137 | 488.54 | **4/5** |
| Recursive (`chunk_size=500`) | 157 | 382.99 | 2/5 |
| Sentence (`max_sentences_per_chunk=3`) | 250 | 237.03 | 3/5 |

**Kết luận tạm thời:**  
Với embedding mock hiện tại, `FixedSizeChunker` đang cho kết quả ổn định và doc-hit@3 cao nhất. Cần chạy lại bằng embedding thật (OpenAI/local model) để kết luận cuối cùng.

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Trần Thái Huy | SentenceChunker | 7 | Dễ cài đặt, chunk theo câu dễ đọc | Tạo nhiều chunk hơn, dễ miss ý ở câu hỏi cần ngữ cảnh dài |
| Không Mạnh Tuấn | fixed_size | 8 | Ổn định, dễ kiểm soát chunk | Query 4/5 vẫn lệch tài liệu kỳ vọng; câu hỏi phức tạp chọn đúng tài liệu và score cao nhưng câu trả lời chưa chính xác (model local) |
| Lâm Hoàng Hải | sentence | 7 | Dễ cài đặt | Chỉ đúng 1/5 query; trả lời tốt câu đơn giản nhưng fail câu phức tạp cần tương đồng/ngữ cảnh; tốn nhiều chunk hơn phương pháp khác |
| Nguyễn Hoàng Long | RecursiveChunker (`chunk_size=500`) | 8 | Giữ ngữ cảnh theo paragraph, phù hợp tài liệu y khoa có cấu trúc | Chunk có thể quá lớn với factsheet câu ngắn |
| Thuận | RecursiveChunker | 8 | Fallback thông minh, tôn trọng cấu trúc tự nhiên tài liệu, linh hoạt | Không xử lý tốt bảng biểu, không có overlap |

---

## 4. My Approach — Cá nhân (10 điểm)

### Chunking Functions

**`SentenceChunker.chunk`**  
Đã triển khai tách câu có xử lý markdown-aware: tách heading/bullet thành đơn vị riêng, gom line-wrap hợp lý, rồi chunk theo `max_sentences_per_chunk`.

**`RecursiveChunker.chunk` / `_split`**  
Đã triển khai recursive split theo ưu tiên separator (`\n\n`, `\n`, `. `, ` `, fallback cắt cứng).

### EmbeddingStore

**`add_documents` + `search`**  
Đã embed và lưu record cho từng chunk; `search()` tính điểm bằng dot product và trả top-k theo score giảm dần.

**`search_with_filter` + `delete_document`**  
Đã hỗ trợ filter metadata trước khi ranking; đã hỗ trợ xóa toàn bộ chunk theo `doc_id`.

### KnowledgeBaseAgent

**`answer`**  
Đã triển khai retrieve top-k, dựng context block có score/source, và gọi `llm_fn` sinh câu trả lời.

### Test Results

```text
============================== 42 passed in 0.06s ==============================
```

**Số tests pass:** **42 / 42**

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | In NIPT, what is the role of paternal DNA information? | Children’s Cancer and Leukaemia Group (CCLG) ... Brain tumours are rare and more research is needed ... | high | 0.410024 | Không |
| 2 | What genetic factor determines the subtype (severity category) of alpha-thalassemia? | If this subtype is identified before birth ... high risk of infant death ... | high | 0.301230 | Có (một phần) |
| 3 | What is the basic human chromosome makeup (autosomes and sex chromosomes)? | About 400 children in the UK develop brain tumours each year ... | high | 0.348617 | Không |
| 4 | What is the most common malignant brain tumour in children? | The platform identifies de novo and inherited variants ... prenatal care ... | high | 0.424329 | Không |
| 5 | Why can brain tumours cause headaches and seizures? | Prenatal screening measures ... CVS ... | high | 0.466774 | Không |

**Nhận xét:**  
Điểm similarity top-1 có thể cao nhưng vẫn sai nội dung cần tìm. Với sentence chunking + mock embedding hiện tại, score chưa phản ánh tốt relevance thật theo gold answer. Cặp 5 là trường hợp rõ nhất: score cao nhất nhưng chunk trả về lệch hoàn toàn domain.

---

## 6. Results — Cá nhân (10 điểm)

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | In NIPT, what is the role of paternal DNA information? | Paternal-inherited SNPs in cfDNA are analyzed to estimate fetal fraction and confirm fetal DNA detection. |
| 2 | What genetic factor determines the subtype (severity category) of alpha-thalassemia? | The number of damaged or missing alpha-globin genes (HBA1/HBA2 copies) determines the subtype. |
| 3 | What is the basic human chromosome makeup (autosomes and sex chromosomes)? | Humans have 46 chromosomes: 22 pairs of autosomes plus 2 sex chromosomes; females are XX and males are XY. |
| 4 | What is the most common malignant brain tumour in children? | Medulloblastoma. |
| 5 | Why can brain tumours cause headaches and seizures? | Tumour growth can raise pressure inside the head by pushing brain tissue or blocking fluid flow, which can trigger symptoms like headaches and seizures. |

### Kết Quả Của Tôi (sentence chunking benchmark hiện tại)

Nguồn: `data/benchmark_results_sentence.json`

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Paternal DNA in NIPT | Top-1 trả về chunk brain tumor guideline, lệch domain | 0.4100 | Không | Chưa chạy (benchmark retrieval-only) |
| 2 | Alpha-thal subtype factor | Top-1 thuộc đúng tài liệu alpha-thalassemia | 0.3012 | Có (một phần) | Chưa chạy |
| 3 | Human chromosome makeup | Top-1 trả về brain tumor, không đúng intent | 0.3486 | Không | Chưa chạy |
| 4 | Most common malignant brain tumour in children | Top-1 trả về prenatal genome, chunk đúng ở rank thấp hơn | 0.4243 | Không | Chưa chạy |
| 5 | Why headaches/seizures in brain tumour | Top-1 trả về alpha-thalassemia, lệch domain | 0.4668 | Không | Chưa chạy |

**Doc-hit@3 (source match):** **3 / 5**  
**Top-1 đúng ý chính:** **1 / 5**

**Nhận xét:**  
Kết quả sentence chunking hiện khá yếu trên bộ query này khi dùng mock embedding; mạnh ở câu đơn giản nhưng hụt câu cần ngữ cảnh chính xác. Cần chạy lại với embedding thật để kết luận chất lượng cuối.

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**  
Một lỗi sai có thể không nằm ở bước chạy pipeline, mà nằm ở cách thiết kế bộ query/gold answer chưa phù hợp để test đúng năng lực của RAG + chunking.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**  
Khi benchmark retrieval, cần ưu tiên các câu hỏi có “anchor” rõ trong tài liệu (thực thể, định nghĩa, guideline cụ thể), để đánh giá khách quan hơn thay vì chỉ dựa vào câu paraphrase quá mở.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**  
Ưu tiên làm sạch markdown kỹ hơn theo cấu trúc bảng/list trước khi chunking, và chạy benchmark với embedding thật sớm hơn để tránh tối ưu sai theo mock embedding.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 10 / 10 |
| Chunking strategy | Nhóm | 15 / 15 |
| My approach | Cá nhân | 8 / 10 |
| Similarity predictions | Cá nhân | 2 / 5 |
| Results | Cá nhân | 7 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 (42/42 tests pass) |
| Demo | Nhóm | 5 / 5 |
| **Tổng** | | **82 / 100** |
