# Specialized_Project — ALNS cho bài toán giao nhận hàng động (DPDP)

Đồ án chuyên ngành: **“Nghiên cứu thuật toán Adaptive Large Neighborhood Search
(ALNS) trong giao vận đô thị – Ứng dụng ALNS cho bài toán giao nhận hàng động”**.

Mục tiêu: khung mô phỏng DES + giải thuật **ALNS-D** (đóng băng cam kết, bộ lọc
ứng viên, thích nghi theo ngân sách thực) để kiểm chứng thực nghiệm 4 giả thuyết
H1–H4 trên dữ liệu Li & Lim và mạng đường TP.HCM.

## Cài đặt

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # hoặc: pip install -e .
```

Mã lõi **chỉ dùng thư viện chuẩn của Python** (≥ 3.10). Các gói phụ
(`scipy` cho kiểm định Wilcoxon, `matplotlib` cho biểu đồ) là tùy chọn.

## Cấu trúc

```text
Specialized_Project/
├── pyproject.toml          # cấu hình gói, entry point `dpdp`
├── src/dpdp/               # MÃ NGUỒN DUY NHẤT
│   ├── instance.py         # đọc/ghi Li & Lim, sinh dữ liệu thử, động hoá (1.3.1)
│   ├── route.py            # lộ trình một xe: chèn/loại, khả thi (2.2.1)
│   ├── solution.py         # lời giải: tập lộ trình + yêu cầu bị từ chối
│   ├── baselines.py        # đối chứng: chèn tham lam, chèn regret-2
│   ├── checker.py          # bộ kiểm tra ĐỘC LẬP tính hợp lệ (2.11)–(2.19)
│   ├── paths.py            # đường dẫn chuẩn: data/, experiments/
│   ├── cli.py              # `python -m dpdp.cli` / lệnh `dpdp`
│   ├── alns/               # engine ALNS-D: toán tử, trọng số, SA, ngân sách
│   │   ├── config.py       #   tham số ALNS (Bảng 2.4)
│   │   ├── operators.py    #   2.1.3–2.1.4 phá huỷ/sửa chữa
│   │   ├── weights.py      #   2.1.5 trọng số thích nghi (2.6), (2.7)
│   │   ├── acceptance.py   #   2.1.6 tiêu chuẩn chấp nhận SA (2.8), (2.9)
│   │   └── engine.py       #   2.2.5 vòng lặp theo ngân sách thời gian
│   ├── adaptations/        # (giai đoạn 4) đóng băng, bộ lọc ứng viên
│   ├── des/                # (giai đoạn 4) khung mô phỏng sự kiện rời rạc
│   └── evaluation/         # (giai đoạn 6) chỉ số mục 1.4, kiểm định Wilcoxon
├── tests/                  # kiểm thử (pytest hoặc chạy trực tiếp)
├── data/
│   ├── lilim/              # bộ dữ liệu Li & Lim (56 file)
│   └── hcm/                # mạng lười đường TP.HCM (mục 1.3.3) — chưa có
├── experiments/            # MỘT thư mục cho mỗi giả thuyết H1–H4
│   └── H?_.../
│       ├── configs/        # cấu hình YAML: instance, seed, ngân sách, biến thể
│       ├── scripts/        # driver gọi API chung của src/dpdp
│       ├── results/raw/    # kết quả thô: mỗi lần chạy một file CSV
│       └── analysis/       # bảng tổng hợp, kiểm định thống kê
├── docs/                   # báo cáo, đề cương, ghi chú
└── legacy/                 # kết quả cũ (không dùng để báo cáo) — bị git-ignore
```

## Nguyên tắc tổ chức

1. **Một nguồn mã**: toàn bộ thuật toán nằm trong `src/dpdp/`. Thư mục
   `experiments/*/scripts/` chỉ là *driver* mỏng đọc cấu hình YAML và gọi API —
   **không** sao chép mã thuật toán theo từng giả thuyết.
2. **Một nơi lưu kết quả**: `experiments/<giả thuyết>/results/raw/`, mỗi lần chạy
   một file CSV có kèm `commit` + `timestamp` để tái lập được.
3. **Biến thể bằng cấu hình, không bằng fork mã**: các cờ `use_freezing`,
   `use_filter`, `adaptive_weights`, ngân sách `B` nằm trong cấu hình ALNS.
   Nhờ vậy H1–H4 so sánh được *theo cặp* (paired test) trên cùng tập seed.
4. **Dữ liệu**: `data/lilim/` chứa bộ Li & Lim gốc (đã tải về từ SINTEF);
   `data/hcm/` dành cho mạng đường TP.HCM.

## Chạy thử

```bash
# kiểm thử
python tests/test_core.py

# hai thuật toán đối chứng trên một file Li & Lim
python -m dpdp.cli --instance data/lilim/lc101.txt
python -m dpdp.cli --instance lrc101.txt --vehicles 15 --late-max 10

# dữ liệu giả — CHỈ để gỡ lỗi, không dùng để báo cáo
python -m dpdp.cli --synthetic 100 --seed 2
```

Kết quả được ghi vào `experiments/H1_distance_freezing/results/raw/` (CSV + bảng
Terminal) kèm mã commit và thời điểm chạy.

## Ánh xạ với báo cáo

| Mục báo cáo | Mã nguồn | Thực nghiệm |
|---|---|---|
| 1.3.1 động hoá dữ liệu Li & Lim | `instance.py` (`dynamize`, `degree_of_dynamism`, `effective_dynamism`) | H4 |
| 1.4 tiêu chí đánh giá (5 nhóm) | `evaluation/metrics.py` | tất cả |
| 2.1.3–2.1.6 toán tử, trọng số, chấp nhận | `alns/` | H3 |
| 2.2.1 mô hình & ràng buộc (2.11)–(2.19) | `route.py`, `checker.py` | — |
| 2.2.2 DES + tái tối ưu theo chu kỳ (Thuật toán 2.2) | `des/` | H4 |
| 2.2.3 đóng băng phần lộ trình (2.20) | `adaptations/freezing.py` | H1 |
| 2.2.4 bộ lọc ứng viên (2.21)–(2.23) | `adaptations/filter.py` | H2 |
| 2.2.5 ngân sách thời gian (2.24)–(2.26) | `alns/engine.py` | H3 |

## Kết quả tham chiếu

ALNS-D (ngân sách 2 s/chu kỳ, seed 1) trên nhóm Solomon C1xx của bộ Li & Lim
(10 xe, khung thời gian cứng ở điểm lấy):

| Thể hiện | greedy | ALNS-D | Giảm |
|---|---|---|---|
| lc101 | 828,94 | **828,94** | 0 |
| lc102 | 904,54 | **828,94** | −8,4 % |
| lc103 | 1125,81 | **827,86** | −26,5 % |
| lc104 | 1276,11 | **1133,44** | −11,2 % |
| lc105 | 828,94 | **828,94** | 0 |
| lc106 | 1111,64 | **828,94** | −25,5 % |
| lc107 | 852,95 | **828,94** | −2,8 % |
| lc108 | 855,74 | **826,44** | −3,4 % |
| lc109 | 1159,19 | **827,82** | −28,6 % |

ALNS-D đạt 828,94 — giá trị tối ưu chung của nhóm C1xx — trên lc101, lc102,
lc105, lc106, lc107; ở lc106 còn giảm số xe dùng từ 11 xuống 10.

## Tình trạng

| Phần | Trạng thái |
|---|---|
| Đọc Li & Lim, lộ trình, chèn/loại, checker | ✅ xong (10/10 kiểm thử) |
| Đối chứng greedy / regret-2 | ✅ xong |
| ALNS (toán tử, trọng số, SA) | ✅ xong (14/14 kiểm thử) |
| Đóng băng, bộ lọc ứng viên | ⬜ giai đoạn 4 |
| Khung DES | ⬜ giai đoạn 4 |
| Chỉ số + kiểm định Wilcoxon | ⬜ giai đoạn 6 |
| Mạng đường TP.HCM | ⬜ mục 1.3.3 |

Xem `docs/README_dpdp_project.md` cho ghi chú chi tiết về mã lõi và các quyết
định thiết kế cần đối chiếu với báo cáo.
