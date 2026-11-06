# Tổ chức thực nghiệm theo giả thuyết

Các thực nghiệm được chia theo bốn giả thuyết trong báo cáo. Mã nguồn dùng
chung nằm trong [`dpdp_project/`](../dpdp_project/); dữ liệu Li & Lim dùng chung
nằm trong [`pdp_100/`](../pdp_100/).

```text
experiments/
├── H1_distance_freezing/
│   ├── configs/
│   ├── results/
│   └── analysis/
├── H2_candidate_filter/
│   ├── configs/
│   ├── results/
│   └── analysis/
├── H3_adaptive_weights/
│   ├── configs/
│   ├── results/
│   └── analysis/
└── H4_dynamism/
    ├── configs/
    ├── results/
    └── analysis/
```

## Ánh xạ giả thuyết

| Thư mục | Nội dung kiểm chứng | Chỉ số chính |
|---|---|---|
| `H1_distance_freezing` | ALNS có đóng băng phần lộ trình đã cam kết so với chèn tham lam | Tổng quãng đường và ý nghĩa thống kê |
| `H2_candidate_filter` | Có/không có bộ lọc ứng viên theo độ lệch tuyến và hướng di chuyển | Thời gian mỗi quyết định và chất lượng lời giải |
| `H3_adaptive_weights` | Mức đóng góp của cập nhật trọng số thích nghi theo ngân sách thời gian | Chênh lệch chất lượng giữa cấu hình có/không thích nghi |
| `H4_dynamism` | Hiệu quả tương đối theo tỷ lệ yêu cầu xuất hiện động | Hiệu quả tương đối tại các mức độ động |

Mỗi cấu hình nên ghi rõ seed, instance, số lần lặp, ngân sách thời gian,
baseline và biến thể thuật toán. Kết quả thô lưu ở `results/`, bảng/tóm tắt
phân tích lưu ở `analysis/`.
