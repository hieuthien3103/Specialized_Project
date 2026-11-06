# Tổ chức thực nghiệm theo giả thuyết

Báo cáo hiện chỉ có bốn giả thuyết H1–H4. H1 là thực nghiệm chính: so sánh
ALNS có đóng băng với chèn tham lam. H2–H4 là các thực nghiệm mở rộng trên
cùng nền tảng mã nguồn. Mã nguồn dùng chung nằm trong
[`dpdp_project/`](../dpdp_project/); dữ liệu Li & Lim dùng chung nằm trong
[`pdp_100/`](../pdp_100/).

```text
experiments/
├── H1_distance_freezing/
│   ├── configs/
│   ├── scripts/
│   ├── results/
│   │   ├── raw/
│   │   └── summarized/
│   └── analysis/
│       ├── tables/
│       └── figures/
├── H2_candidate_filter/
│   ├── configs/
│   ├── scripts/
│   ├── results/
│   │   ├── raw/
│   │   └── summarized/
│   └── analysis/
│       ├── tables/
│       └── figures/
├── H3_adaptive_weights/
│   ├── configs/
│   ├── scripts/
│   ├── results/
│   │   ├── raw/
│   │   └── summarized/
│   └── analysis/
│       ├── tables/
│       └── figures/
└── H4_dynamism/
    ├── configs/
    ├── scripts/
    ├── results/
    │   ├── raw/
    │   └── summarized/
    └── analysis/
        ├── tables/
        └── figures/
```

## Ánh xạ giả thuyết

| Thư mục | Nội dung kiểm chứng | Chỉ số chính |
|---|---|---|
| `H1_distance_freezing` | **Chính** — ALNS có đóng băng phần lộ trình đã cam kết so với chèn tham lam | Tổng quãng đường và ý nghĩa thống kê |
| `H2_candidate_filter` | Mở rộng — có/không có bộ lọc ứng viên theo độ lệch tuyến và hướng di chuyển | Thời gian mỗi quyết định và chất lượng lời giải |
| `H3_adaptive_weights` | Mở rộng — mức đóng góp của cập nhật trọng số thích nghi theo ngân sách thời gian | Chênh lệch chất lượng giữa cấu hình có/không thích nghi |
| `H4_dynamism` | Mở rộng — hiệu quả tương đối theo tỷ lệ yêu cầu xuất hiện động | Hiệu quả tương đối tại các mức độ động |

Mỗi cấu hình nên ghi rõ seed, instance, số lần lặp, ngân sách thời gian,
baseline và biến thể thuật toán. Kết quả từng lần chạy lưu ở `results/raw/`,
bảng/tóm tắt lưu ở `results/summarized/`, còn bảng và biểu đồ phân tích lưu
ở `analysis/`.
