# Dữ liệu

## Li & Lim

- Nguồn: bộ benchmark pickup-and-delivery Li & Lim, lưu tại `lilim/`. Ghi chú
  hiện có của dự án cho biết bộ này được lấy từ SINTEF; URL tải trực tiếp không
  được lưu lại.
- Ngày tải: chưa được ghi nhận trong metadata hiện có.
- SHA-256 tổng hợp của 56 file `.txt` trong `lilim/`, tính từ danh sách checksum
  từng file theo thứ tự tên file:
  `fa24df326ddfd1f7841f8f76c8ad5008cc17d34125d79245669c27675d648216`
- Tính lại trên Linux bằng: `LC_ALL=C sha256sum lilim/*.txt | sha256sum`

`lilim/` là bản gốc, chỉ đọc. Không chỉnh sửa file nguồn; dữ liệu biến đổi theo
thời điểm phát hành lưu trong `dynamic/`. Dữ liệu TP.HCM lưu riêng trong
`hcm/raw/` và `hcm/processed/`; không có dữ liệu HCM được thêm trong lần tổ chức
thư mục này.