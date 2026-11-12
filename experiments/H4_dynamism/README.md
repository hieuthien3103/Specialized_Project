# H4 — Mức độ động

Kiểm tra hiệu quả tương đối của ALNS-D khi tỷ lệ yêu cầu xuất hiện động tăng.
Mỗi mức rho dùng đúng cùng seed và release scenario cho bốn thuật toán.

```bash
python experiments/H1_distance_freezing/scripts/run_h1.py \
  --instances lc101.txt lr101.txt lrc101.txt \
  --rhos 0.25 0.5 0.75 1.0 --seeds 0 1 2 3 4 5 6 7 8 9 \
  --fleet-level tight \
  --selected-config experiments/H1_distance_freezing/configs/selected_alns.json \
  --release-root data/dynamic \
  --output experiments/H4_dynamism/results/raw/h4_event_model.csv
python -m experiments.H4_dynamism.analysis.analyze_h4 \
  --input experiments/H4_dynamism/results/raw/h4_event_model.csv \
  --output experiments/H4_dynamism/analysis/tables/h4_event_summary.csv
```

Bảng `h4_event_summary.csv` báo cáo trung bình, chênh lệch trung bình/trung vị và
Wilcoxon hai phía cho từng rho. Chỉ diễn giải xu hướng sau khi mọi cấu hình
đạt `valid=True`. Kết quả được lưu riêng để không ghi đè các số liệu được tạo
bằng mô hình mô phỏng trước đây.
