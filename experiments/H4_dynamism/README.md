# H4 — Mức độ động

Kiểm tra hiệu quả tương đối của ALNS-D khi tỷ lệ yêu cầu xuất hiện động tăng.
Mỗi mức rho dùng đúng cùng seed và release scenario cho bốn thuật toán.

```bash
python experiments/H1_distance_freezing/scripts/run_h1.py \
  --instances lc101.txt lr101.txt lrc101.txt \
  --rhos 0.25 0.5 0.75 1.0 --seeds 0 1 2 3 4 5 6 7 8 9 \
  --vehicles 10 --budget 0.2 --release-root data/dynamic \
  --output experiments/H4_dynamism/results/raw/h4_results.csv
python experiments/H4_dynamism/analysis/analyze_h4.py
```

Bảng `h4_by_rho.csv` báo cáo trung bình, chênh lệch trung bình/trung vị và
Wilcoxon hai phía cho từng rho. Chỉ diễn giải xu hướng sau khi mọi cấu hình
đạt `valid=True`.
