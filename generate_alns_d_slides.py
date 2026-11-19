from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.chart.data import ChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION


OUT = r"E:\Specialized_Project\Bao_cao_do_an_ALNS-D_DPDP.pptx"

NAVY = RGBColor(18, 35, 58)
BLUE = RGBColor(40, 103, 178)
CYAN = RGBColor(56, 189, 199)
ORANGE = RGBColor(244, 162, 97)
GREEN = RGBColor(88, 166, 126)
RED = RGBColor(210, 86, 86)
WHITE = RGBColor(255, 255, 255)
LIGHT = RGBColor(244, 247, 250)
MID = RGBColor(209, 218, 227)
DARK = RGBColor(38, 49, 61)
GRAY = RGBColor(112, 126, 140)


prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)


def add_text(slide, text, x, y, w, h, size=24, color=DARK, bold=False,
             align=PP_ALIGN.LEFT, font="Aptos", valign=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.02)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = align
    p.font.name = font
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    return box


def add_rich_text(slide, runs, x, y, w, h, size=22, align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    for text, bold, color in runs:
        r = p.add_run()
        r.text = text
        r.font.name = "Aptos"
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color
    return box


def rect(slide, x, y, w, h, fill, radius=False, line=None):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = line if line else fill
    if radius:
        shape.adjustments[0] = 0.12
    return shape


def title(slide, text, kicker=None):
    rect(slide, 0, 0, 13.333, 0.12, CYAN)
    if kicker:
        add_text(slide, kicker.upper(), 0.65, 0.38, 12.0, 0.28, 10, BLUE, True)
        add_text(slide, text, 0.65, 0.72, 12.0, 0.58, 28, NAVY, True)
    else:
        add_text(slide, text, 0.65, 0.42, 12.0, 0.72, 28, NAVY, True)


def footer(slide, number, source=None):
    add_text(slide, "Đồ án chuyên ngành • ALNS-D cho giao nhận hàng động",
             0.65, 7.12, 8.8, 0.18, 8, GRAY)
    if source:
        add_text(slide, source, 7.5, 7.12, 4.75, 0.18, 8, GRAY, align=PP_ALIGN.RIGHT)
    add_text(slide, f"{number:02d}", 12.55, 7.08, 0.35, 0.22, 9, BLUE, True, PP_ALIGN.RIGHT)


def bullet_list(slide, bullets, x, y, w, h, size=20, color=DARK, accent=CYAN):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.03)
    for i, bullet in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = "• " + bullet
        p.level = 0
        p.font.name = "Aptos"
        p.font.size = Pt(size)
        p.font.color.rgb = color
        p.space_after = Pt(10)
    return box


def card(slide, x, y, w, h, heading, value, note="", accent=BLUE):
    rect(slide, x, y, w, h, WHITE, True, MID)
    rect(slide, x, y, 0.10, h, accent, True, accent)
    add_text(slide, heading, x + 0.28, y + 0.24, w - 0.50, 0.38, 13, GRAY, True)
    add_text(slide, value, x + 0.28, y + 0.66, w - 0.50, 0.64, 30, NAVY, True)
    if note:
        add_text(slide, note, x + 0.28, y + 1.38, w - 0.50, h - 1.58, 12, DARK)


def metric_pill(slide, x, y, w, label, value, accent):
    rect(slide, x, y, w, 0.82, WHITE, True, MID)
    rect(slide, x, y, 0.08, 0.82, accent, True, accent)
    add_text(slide, label, x + 0.22, y + 0.14, w - 0.40, 0.22, 10, GRAY, True)
    add_text(slide, value, x + 0.22, y + 0.38, w - 0.40, 0.32, 18, NAVY, True)


def add_line_chart(slide, categories, series, x, y, w, h, colors,
                   y_axis_title="", legend=True):
    chart_data = ChartData()
    chart_data.categories = categories
    for name, values in series:
        chart_data.add_series(name, values)
    chart = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(x), Inches(y),
                                   Inches(w), Inches(h), chart_data).chart
    chart.has_title = False
    chart.has_legend = legend
    if legend:
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False
        chart.legend.font.size = Pt(10)
    chart.value_axis.has_major_gridlines = True
    chart.value_axis.major_gridlines.format.line.color.rgb = MID
    chart.category_axis.tick_labels.font.size = Pt(10)
    chart.value_axis.tick_labels.font.size = Pt(10)
    if y_axis_title:
        chart.value_axis.axis_title.text_frame.text = y_axis_title
    for i, s in enumerate(chart.series):
        s.format.line.color.rgb = colors[i]
        s.format.line.width = Pt(2.5)
        s.marker.style = 2
        s.marker.size = 7
        s.marker.format.fill.solid()
        s.marker.format.fill.fore_color.rgb = colors[i]
        s.marker.format.line.color.rgb = colors[i]


# 1 - Cover
slide = prs.slides.add_slide(prs.slide_layouts[6])
rect(slide, 0, 0, 13.333, 7.5, NAVY)
rect(slide, 0, 0, 13.333, 0.14, CYAN)
rect(slide, 9.2, 0.14, 4.133, 7.36, RGBColor(24, 48, 78))
add_text(slide, "ĐỒ ÁN CHUYÊN NGÀNH", 0.78, 0.72, 7.8, 0.38, 12, CYAN, True)
add_text(slide, "Nghiên cứu thuật toán\nAdaptive Large Neighborhood Search",
         0.78, 1.32, 8.15, 1.55, 34, WHITE, True)
add_text(slide, "Ứng dụng ALNS cho bài toán giao nhận hàng động",
         0.78, 3.12, 7.85, 0.92, 22, RGBColor(210, 225, 238), True)
rect(slide, 0.78, 4.48, 6.85, 0.06, ORANGE)
add_text(slide, "Đỗ Trọng Tín  •  Nguyễn Phạm Hiếu Thiện",
         0.78, 4.82, 7.3, 0.42, 16, WHITE, True)
add_text(slide, "GVHD: TS. Phan Tấn Quốc", 0.78, 5.34, 5.8, 0.32, 14, RGBColor(210, 225, 238))
add_text(slide, "2026", 10.08, 6.28, 2.2, 0.72, 28, WHITE, True, PP_ALIGN.RIGHT)

# 2 - Agenda
slide = prs.slides.add_slide(prs.slide_layouts[6])
rect(slide, 0, 0, 13.333, 7.5, LIGHT)
title(slide, "Cấu trúc thuyết trình")
sections = [
    ("01", "Bối cảnh", "PDP • PDPTW • DPDP"),
    ("02", "Phương pháp", "ALNS-D • DES • mô hình hóa"),
    ("03", "Thực nghiệm", "Thiết kế • dữ liệu • giả thuyết"),
    ("04", "Kết quả", "H1–H4 • so sánh baseline"),
    ("05", "Kết luận", "Đóng góp • hạn chế • hướng phát triển"),
]
for i, (n, h, d) in enumerate(sections):
    y = 1.56 + i * 1.02
    rect(slide, 0.75, y, 11.83, 0.78, WHITE, True, MID)
    rect(slide, 0.75, y, 0.78, 0.78, BLUE if i < 4 else ORANGE, True)
    add_text(slide, n, 0.75, y + 0.21, 0.78, 0.32, 14, WHITE, True, PP_ALIGN.CENTER)
    add_text(slide, h, 1.78, y + 0.16, 2.0, 0.38, 18, NAVY, True)
    add_text(slide, d, 4.10, y + 0.19, 7.85, 0.30, 15, DARK)
footer(slide, 2)

# 3 - Motivation
slide = prs.slides.add_slide(prs.slide_layouts[6])
rect(slide, 0, 0, 13.333, 7.5, WHITE)
title(slide, "Vì sao bài toán giao nhận vận tải đô thị cần giải pháp động?", "01 • Bối cảnh")
card(slide, 0.75, 1.55, 3.72, 2.05, "Đơn phát sinh", "Trong ngày", "Địa chỉ, khối lượng và khung thời gian chưa biết trước", BLUE)
card(slide, 4.80, 1.55, 3.72, 2.05, "Bão hòa mạng", "Biến động", "Tắc đường làm thay đổi thời gian và chi phí di chuyển", ORANGE)
card(slide, 8.85, 1.55, 3.72, 2.05, "Yêu cầu quyết định", "Thời gian thực", "Cập nhật lộ trình liên tục trước hạn và ngân sách tính toán", GREEN)
add_text(slide, "Khoảng cách giữa mô hình tĩnh và vận hành thực tế", 0.75, 4.16, 11.7, 0.44, 20, NAVY, True)
rect(slide, 0.75, 4.78, 3.38, 1.28, LIGHT, True, MID)
add_text(slide, "MÔ HÌNH TĨNH", 1.05, 5.04, 2.78, 0.26, 11, GRAY, True)
add_text(slide, "Toàn bộ yêu cầu đã biết", 1.05, 5.38, 2.78, 0.30, 16, NAVY, True)
rect(slide, 4.98, 5.15, 1.25, 0.16, ORANGE)
add_text(slide, "→", 4.62, 4.98, 0.42, 0.44, 20, ORANGE, True, PP_ALIGN.CENTER)
rect(slide, 6.75, 4.78, 5.82, 1.28, LIGHT, True, MID)
add_text(slide, "BÀI TOÁN ĐỘNG", 7.05, 5.04, 2.78, 0.26, 11, GRAY, True)
add_text(slide, "Cập nhật quyết định theo sự kiện", 7.05, 5.38, 4.90, 0.30, 16, NAVY, True)
footer(slide, 3)

# 4 - Problem
slide = prs.slides.add_slide(prs.slide_layouts[6])
rect(slide, 0, 0, 13.333, 7.5, WHITE)
title(slide, "Từ PDP đến Dynamic Pickup and Delivery Problem", "01 • Bài toán")
levels = [
    ("PDP", "Ghép tuyến lấy – giao", "Cặp điểm pickup–delivery"), 
    ("PDPTW", "Thêm khung thời gian", "Soft / hard time window"),
    ("DPDP", "Yêu cầu phát sinh theo thời gian", "Tái tối ưu và quyết định online"),
]
for i, (a, b, c) in enumerate(levels):
    x = 0.75 + i * 4.05
    rect(slide, x, 1.54, 3.72, 2.20, [LIGHT, RGBColor(232, 241, 250), RGBColor(229, 248, 247)][i], True, MID)
    add_text(slide, a, x + 0.30, 1.82, 3.12, 0.38, 18, [BLUE, BLUE, GREEN][i], True)
    add_text(slide, b, x + 0.30, 2.38, 3.12, 0.58, 15, NAVY, True)
    add_text(slide, c, x + 0.30, 3.10, 3.12, 0.40, 12, DARK)
add_text(slide, "Mục tiêu đa tiêu chí", 0.75, 4.30, 3.2, 0.38, 18, NAVY, True)
metric_pill(slide, 0.75, 4.90, 3.72, "CHI PHÍ", "Tổng quãng đường", BLUE)
metric_pill(slide, 4.80, 4.90, 3.72, "CHẤT LƯỢNG", "Tỷ lệ đơn được phục vụ", GREEN)
metric_pill(slide, 8.85, 4.90, 3.72, "ĐỘ TRỄ", "Lệch khung thời gian mềm", ORANGE)
footer(slide, 4)

# 5 - Scenario
slide = prs.slides.add_slide(prs.slide_layouts[6])
rect(slide, 0, 0, 13.333, 7.5, LIGHT)
title(slide, "Ví dụ vận hành: quyết định theo thời gian thực", "01 • Bối cảnh")
rect(slide, 0.75, 1.55, 11.83, 4.90, WHITE, True, MID)
# depot and stops
nodes = [(1.35, 3.28), (3.10, 2.10), (5.30, 3.76), (7.45, 2.05), (9.48, 3.62), (11.35, 2.18)]
labels = ["Kho", "Lấy A", "Giao A", "Lấy B", "Giao B", "Cần xe"]
for i, ((x, y), lab) in enumerate(zip(nodes, labels)):
    color = NAVY if i == 0 else (ORANGE if i in (1, 3) else (GREEN if i in (2, 4) else BLUE))
    shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(0.46), Inches(0.46))
    shape.fill.solid(); shape.fill.fore_color.rgb = color; shape.line.color.rgb = color
    add_text(slide, str(i), x, y + 0.11, 0.46, 0.18, 9, WHITE, True, PP_ALIGN.CENTER)
    add_text(slide, lab, x - 0.48, y + 0.58, 1.42, 0.28, 9, DARK, True, PP_ALIGN.CENTER)
for i in range(len(nodes)-1):
    x1, y1 = nodes[i][0]+0.46, nodes[i][1]+0.23
    x2, y2 = nodes[i+1][0], nodes[i+1][1]+0.23
    line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    line.line.color.rgb = MID
    line.line.width = Pt(2)
add_text(slide, "t₀", 1.05, 1.90, 0.35, 0.24, 11, BLUE, True)
add_text(slide, "Đơn B xuất hiện ngoài kế hoạch", 3.40, 1.90, 3.30, 0.26, 13, ORANGE, True)
add_text(slide, "Cơ chế lộ trình", 0.75, 5.86, 2.0, 0.28, 12, GRAY, True)
add_text(slide, "Đóng băng phần cam kết", 2.65, 5.80, 2.55, 0.36, 16, NAVY, True)
add_text(slide, "→", 5.22, 5.82, 0.50, 0.28, 16, ORANGE, True)
add_text(slide, "Chèn đơn mới an toàn", 5.85, 5.80, 2.45, 0.36, 16, NAVY, True)
add_text(slide, "→", 8.35, 5.82, 0.50, 0.28, 16, ORANGE, True)
add_text(slide, "Tái tối ưu theo chu kỳ", 8.95, 5.80, 2.85, 0.36, 16, NAVY, True)
footer(slide, 5)

# 6 - Objectives
slide = prs.slides.add_slide(prs.slide_layouts[6])
rect(slide, 0, 0, 13.333, 7.5, WHITE)
title(slide, "Mục tiêu và phạm vi đồ án", "01 • Bối cảnh")
left = [
    "Xây dựng mô hình DPDP đa mục tiêu",
    "Thiết kế ALNS-D: 3 cơ chế thích ứng",
    "Tích hợp mô phỏng sự kiện rời rạc (DES)",
]
right = [
    "Động hóa Li & Lim PDPTW",
    "So sánh ALNS-D với baseline",
    "Kiểm chứng H1–H4 bằng 30/10 seed",
]
rect(slide, 0.75, 1.55, 5.85, 3.95, LIGHT, True, MID)
rect(slide, 6.78, 1.55, 5.80, 3.95, RGBColor(232, 241, 250), True, MID)
add_text(slide, "TRỌNG TÂM", 1.08, 1.84, 2.2, 0.28, 12, BLUE, True)
bullet_list(slide, left, 1.08, 2.38, 5.10, 2.72, 17)
add_text(slide, "ĐỐI CHỨNG", 7.12, 1.84, 2.2, 0.28, 12, BLUE, True)
bullet_list(slide, right, 7.12, 2.38, 5.10, 2.72, 17)
rect(slide, 0.75, 5.82, 11.83, 0.70, NAVY, True, NAVY)
add_text(slide, "Câu hỏi nghiên cứu: Ba cơ chế thích ứng nào giúp ALNS-D bền vững nhất theo mức độ động?", 
         1.05, 6.02, 11.23, 0.30, 16, WHITE, True, PP_ALIGN.CENTER)
footer(slide, 6)

# 7 - Theory
slide = prs.slides.add_slide(prs.slide_layouts[6])
rect(slide, 0, 0, 13.333, 7.5, WHITE)
title(slide, "Cơ sở: Adaptive Large Neighborhood Search", "02 • Phương pháp")
steps = [
    ("1", "Nghiệm ban đầu", "Greedy / regret-2"),
    ("2", "Phá vỡ", "Destroy: loại một cụm yêu cầu"),
    ("3", "Xây lại", "Repair: chèn lại theo chi phí"),
    ("4", "Chấp nhận", "Simulated annealing"),
    ("5", "Thích nghi", "Cập nhật trọng số toán tử"),
]
for i, (n, h, d) in enumerate(steps):
    x = 0.72 + i * 2.50
    rect(slide, x, 1.58, 2.12, 2.30, LIGHT, True, MID)
    rect(slide, x + 0.62, 1.82, 0.88, 0.88, BLUE if i != 4 else ORANGE, True)
    add_text(slide, n, x + 0.62, 2.08, 0.88, 0.26, 16, WHITE, True, PP_ALIGN.CENTER)
    add_text(slide, h, x + 0.18, 2.88, 1.76, 0.36, 13, NAVY, True, PP_ALIGN.CENTER)
    add_text(slide, d, x + 0.18, 3.36, 1.76, 0.36, 10, DARK, False, PP_ALIGN.CENTER)
    if i < 4:
        add_text(slide, "→", x + 2.18, 2.48, 0.30, 0.30, 16, ORANGE, True)
rect(slide, 0.75, 4.52, 11.83, 1.55, NAVY, True, NAVY)
add_text(slide, "Điểm khác biệt ALNS-D", 1.10, 4.82, 2.70, 0.32, 13, CYAN, True)
add_text(slide, "Không tối ưu offline một lần — thích ứng liên tục trong từng chu kỳ mô phỏng.",
         1.10, 5.24, 10.90, 0.42, 17, WHITE, True)
footer(slide, 7)

# 8 - Architecture
slide = prs.slides.add_slide(prs.slide_layouts[6])
rect(slide, 0, 0, 13.333, 7.5, LIGHT)
title(slide, "Kiến trúc ALNS-D", "02 • Giải pháp đề xuất")
rect(slide, 0.75, 1.52, 11.83, 4.88, WHITE, True, MID)
boxes = [
    (1.10, 2.16, 2.22, "Trạng thái\nthời gian thực", BLUE),
    (3.85, 2.16, 2.22, "Bộ lọc ứng viên", CYAN),
    (6.60, 2.16, 2.22, "ALNS thích nghi", ORANGE),
    (9.35, 2.16, 2.22, "Lộ trình cam kết", GREEN),
]
for x, y, w, htxt, c in boxes:
    rect(slide, x, y, w, 1.12, c, True, c)
    add_text(slide, htxt, x + 0.12, y + 0.30, w - 0.24, 0.52, 15, WHITE, True, PP_ALIGN.CENTER)
for x1, x2 in [(3.32, 3.85), (6.07, 6.60), (8.82, 9.35)]:
    add_text(slide, "→", x1, 2.55, 0.53, 0.28, 16, ORANGE, True, PP_ALIGN.CENTER)
rect(slide, 1.10, 4.18, 10.47, 1.30, RGBColor(246, 249, 252), True, MID)
add_text(slide, "Đóng băng + ngân sách", 1.42, 4.48, 2.55, 0.30, 13, NAVY, True)
add_text(slide, "Bảo toàn phần lộ trình đã xác nhận", 4.15, 4.42, 3.55, 0.32, 14, DARK)
add_text(slide, "Giới hạn thời gian mỗi chu kỳ", 7.75, 4.42, 3.20, 0.32, 14, DARK)
add_text(slide, "DES", 1.42, 5.12, 0.55, 0.20, 9, GRAY, True)
add_text(slide, "release time • next event • reoptimization", 2.05, 5.08, 5.00, 0.24, 11, GRAY)
footer(slide, 8)

# 9 - Three mechanisms
slide = prs.slides.add_slide(prs.slide_layouts[6])
rect(slide, 0, 0, 13.333, 7.5, WHITE)
title(slide, "Ba thành phần thích ứng cốt lõi", "02 • Giải pháp đề xuất")
cards = [
    ("01", "Đóng băng lộ trình", "Giữ các hành trình đã cam kết; tránh tái tối ưu làm thay đổi đột ngột.", BLUE),
    ("02", "Bộ lọc ứng viên", "Ưu tiên vùng lệch tuyến và hướng di chuyển; rút ngắn không gian tìm kiếm.", CYAN),
    ("03", "Ngân sách theo thời gian", "Tự thích nghi trọng số; dừng trước khi vượt ngưỡng B tính toán.", ORANGE),
]
for i, (n, h, d, c) in enumerate(cards):
    x = 0.75 + i * 4.05
    rect(slide, x, 1.58, 3.72, 4.20, LIGHT, True, MID)
    rect(slide, x + 0.28, 1.88, 0.72, 0.72, c, True, c)
    add_text(slide, n, x + 0.28, 2.10, 0.72, 0.24, 13, WHITE, True, PP_ALIGN.CENTER)
    add_text(slide, h, x + 0.28, 2.92, 3.16, 0.54, 17, NAVY, True)
    add_text(slide, d, x + 0.28, 3.68, 3.16, 1.32, 13, DARK)
footer(slide, 9)

# 10 - Experimental design
slide = prs.slides.add_slide(prs.slide_layouts[6])
rect(slide, 0, 0, 13.333, 7.5, LIGHT)
title(slide, "Thiết kế thực nghiệm", "03 • Thực nghiệm")
metric_pill(slide, 0.75, 1.52, 2.78, "DỮ LIỆU", "6 instance", BLUE)
metric_pill(slide, 3.75, 1.52, 2.78, "MỨC ĐỘ ĐỘNG", "ρ = 0.1–0.9", ORANGE)
metric_pill(slide, 6.75, 1.52, 2.78, "SEED", "30 / 10", GREEN)
metric_pill(slide, 9.75, 1.52, 2.83, "KIỂM ĐỊNH", "Wilcoxon", CYAN)
rect(slide, 0.75, 2.72, 11.83, 3.42, WHITE, True, MID)
add_text(slide, "lc101  •  lc201  •  lr101  •  lr201  •  lrc101  •  lrc201",
         1.08, 3.08, 11.18, 0.38, 18, NAVY, True, PP_ALIGN.CENTER)
add_text(slide, "H1–H2", 1.18, 3.82, 1.55, 0.28, 13, BLUE, True)
add_text(slide, "30 seed • kiểm định theo cặp", 2.68, 3.78, 3.40, 0.34, 14, DARK)
add_text(slide, "H3–H4", 6.78, 3.82, 1.55, 0.28, 13, BLUE, True)
add_text(slide, "10 seed • phân tích ngân sách / mức động", 8.28, 3.78, 3.72, 0.34, 14, DARK)
rect(slide, 1.18, 4.62, 10.84, 0.82, RGBColor(246, 249, 252), True, MID)
add_text(slide, "Baseline: Greedy / Regret-2  •  Đối tượng: hiệu quả quãng đường, tỷ lệ phục vụ, CPU",
         1.48, 4.88, 10.24, 0.28, 13, NAVY, True, PP_ALIGN.CENTER)
footer(slide, 10)

# 11 - H1
slide = prs.slides.add_slide(prs.slide_layouts[6])
rect(slide, 0, 0, 13.333, 7.5, WHITE)
title(slide, "H1 — Đóng băng phần lộ trình cam kết", "04 • Kết quả")
card(slide, 0.75, 1.55, 3.45, 2.08, "Giảm quãng đường", "−50.72", "đơn vị trung bình theo kết quả pooled", BLUE)
card(slide, 4.94, 1.55, 3.45, 2.08, "Tốt nhất", "−214.91", "lrc201", GREEN)
card(slide, 9.13, 1.55, 3.45, 2.08, "Kiểm định", "p ≈ 1.65e−4", "r_rb ≈ 0.3138", ORANGE)
rect(slide, 0.75, 4.20, 11.83, 1.62, LIGHT, True, MID)
add_text(slide, "Ý nghĩa", 1.08, 4.50, 1.15, 0.28, 12, GRAY, True)
add_text(slide, "Đóng băng giúp ALNS-D ổn định hơn và giảm chi phí đường đi.",
         2.28, 4.42, 9.72, 0.42, 18, NAVY, True)
add_text(slide, "Cơ chế bảo toàn quyết định đã cam kết trước khi tái tối ưu.", 2.28, 5.02, 9.72, 0.30, 12, DARK)
footer(slide, 11, "Nguồn: H1 pooled, 30 seed")

# 12 - H2
slide = prs.slides.add_slide(prs.slide_layouts[6])
rect(slide, 0, 0, 13.333, 7.5, WHITE)
title(slide, "H2 — Bộ lọc ứng viên rút ngắn không gian tìm kiếm", "04 • Kết quả")
add_text(slide, "Thời gian quyết định", 0.75, 1.48, 4.0, 0.38, 16, NAVY, True)
# bar chart
rect(slide, 0.75, 2.05, 5.55, 3.64, LIGHT, True, MID)
add_text(slide, "Không lọc", 1.12, 2.50, 1.20, 0.28, 12, GRAY, True)
rect(slide, 2.42, 2.50, 3.16, 0.64, MID, True)
add_text(slide, "12.50 ms", 4.60, 2.69, 0.85, 0.20, 12, NAVY, True, PP_ALIGN.RIGHT)
add_text(slide, "Có lọc", 1.12, 3.58, 1.20, 0.28, 12, GRAY, True)
rect(slide, 2.42, 3.58, 1.01, 0.64, CYAN, True)
add_text(slide, "4.00 ms", 2.95, 3.77, 0.85, 0.20, 12, NAVY, True, PP_ALIGN.RIGHT)
add_text(slide, "Tiết kiệm 68% thời gian CPU", 1.12, 4.70, 4.74, 0.38, 16, GREEN, True, PP_ALIGN.CENTER)
card(slide, 6.66, 2.05, 2.96, 3.64, "Tăng tốc", "3.13×", "thời gian quyết định", ORANGE)
card(slide, 9.92, 2.05, 2.66, 3.64, "Tỷ lệ phục vụ", "92.87%", "tăng từ 83.45%", GREEN)
footer(slide, 12)

# 13 - H3
slide = prs.slides.add_slide(prs.slide_layouts[6])
rect(slide, 0, 0, 13.333, 7.5, LIGHT)
title(slide, "H3 — Thích nghi suy giảm khi ngân sách bị rút ngắn", "04 • Kết quả")
add_text(slide, "Cải thiện quãng đường trung bình", 0.75, 1.48, 5.3, 0.36, 16, NAVY, True)
categories = ["B = 1.00 s", "B = 0.50 s", "B = 0.10 s", "B = 0.05 s"]
add_line_chart(
    slide, categories,
    [("Cải thiện (đơn vị)", [6.09, 3.50, 1.75, 0.85])],
    0.75, 2.05, 7.50, 4.22, [BLUE], "đơn vị quãng đường", False
)
rect(slide, 8.62, 2.05, 3.96, 4.22, WHITE, True, MID)
add_text(slide, "B = 1.00 s", 9.02, 2.48, 3.15, 0.26, 12, GRAY, True)
add_text(slide, "6.09", 9.02, 2.90, 3.15, 0.72, 34, BLUE, True)
add_text(slide, "B = 0.05 s", 9.02, 4.10, 3.15, 0.26, 12, GRAY, True)
add_text(slide, "0.85", 9.02, 4.52, 3.15, 0.72, 34, ORANGE, True)
add_text(slide, "Chỉ còn 14% mức cải thiện", 9.02, 5.38, 3.15, 0.38, 12, NAVY, True)
footer(slide, 13)

# 14 - H4
slide = prs.slides.add_slide(prs.slide_layouts[6])
rect(slide, 0, 0, 13.333, 7.5, WHITE)
title(slide, "H4 — Ưu thế ALNS-D tăng khi mức độ động cao", "04 • Kết quả")
categories = ["ρ = 0.1", "ρ = 0.3", "ρ = 0.5", "ρ = 0.7", "ρ = 0.9"]
add_line_chart(
    slide, categories,
    [
        ("Gap_eff", [-3.3, -0.8, 2.1, 6.4, 10.2]),
        ("ΔSR", [-11.1, -4.2, 1.0, 6.1, 10.7]),
    ],
    0.75, 1.56, 7.65, 4.55, [BLUE, ORANGE], "%", True
)
rect(slide, 8.78, 1.56, 3.80, 4.55, NAVY, True, NAVY)
add_text(slide, "TẠI ρ = 0.9", 9.18, 1.96, 3.00, 0.28, 12, CYAN, True)
add_text(slide, "95%", 9.18, 2.48, 1.40, 0.56, 28, WHITE, True)
add_text(slide, "ALNS-D", 10.58, 2.62, 1.30, 0.28, 12, RGBColor(210,225,238), True)
add_text(slide, "84.3%", 9.18, 3.38, 1.40, 0.56, 28, ORANGE, True)
add_text(slide, "Greedy", 10.58, 3.52, 1.30, 0.28, 12, RGBColor(210,225,238), True)
add_text(slide, "+29.8%", 9.18, 4.36, 2.70, 0.46, 24, CYAN, True)
add_text(slide, "ΔSR trên lrc201", 9.18, 4.90, 2.70, 0.28, 12, WHITE, True)
footer(slide, 14)

# 15 - DES
slide = prs.slides.add_slide(prs.slide_layouts[6])
rect(slide, 0, 0, 13.333, 7.5, LIGHT)
title(slide, "Khung mô phỏng DES và quy trình tái tối ưu", "02 • Phương pháp")
steps = [
    ("1", "Sự kiện", "Đơn xuất hiện"),
    ("2", "Cập nhật", "Trạng thái xe"),
    ("3", "Lọc", "Ứng viên"),
    ("4", "Giải", "ALNS-D"),
    ("5", "Chấp nhận", "Tỷ lệ / trễ"),
]
for i, (n, h, d) in enumerate(steps):
    x = 0.75 + i * 2.42
    rect(slide, x, 1.70, 2.10, 2.16, WHITE, True, MID)
    add_text(slide, n, x + 0.18, 1.94, 0.48, 0.48, 14, BLUE, True)
    add_text(slide, h, x + 0.18, 2.58, 1.74, 0.28, 12, NAVY, True)
    add_text(slide, d, x + 0.18, 3.04, 1.74, 0.38, 11, DARK)
    if i < 4:
        add_text(slide, "→", x + 2.12, 2.58, 0.30, 0.28, 15, ORANGE, True)
rect(slide, 0.75, 4.56, 11.83, 1.38, NAVY, True, NAVY)
add_text(slide, "Chu kỳ = khoảng thời gian discrete event", 1.10, 4.90, 4.70, 0.34, 14, CYAN, True)
add_text(slide, "Lặp lại đến khi toàn bộ đơn được phục vụ hoặc kết thúc mô phỏng",
         1.10, 5.30, 10.85, 0.32, 15, WHITE, True)
footer(slide, 15)

# 16 - Overall comparison
slide = prs.slides.add_slide(prs.slide_layouts[6])
rect(slide, 0, 0, 13.333, 7.5, WHITE)
title(slide, "So sánh tổng hợp H1–H4", "04 • Kết luận thực nghiệm")
rows = [
    ("H1", "Đóng băng", "Giảm quãng đường", "−50.72", GREEN),
    ("H2", "Bộ lọc", "Tăng tốc + phục vụ", "3.13× / +9.42%", CYAN),
    ("H3", "Ngân sách", "Vai trò thích nghi", "6.09 → 0.85", BLUE),
    ("H4", "Mức độ động", "Ưu thế theo ρ", "−3.3% → +10.2%", ORANGE),
]
for i, (h1, h2, h3, h4, c) in enumerate(rows):
    y = 1.58 + i * 1.18
    rect(slide, 0.75, y, 11.83, 0.92, LIGHT, True, MID)
    rect(slide, 0.75, y, 0.82, 0.92, c, True, c)
    add_text(slide, h1, 0.75, y + 0.29, 0.82, 0.26, 14, WHITE, True, PP_ALIGN.CENTER)
    add_text(slide, h2, 1.82, y + 0.25, 2.10, 0.30, 15, NAVY, True)
    add_text(slide, h3, 4.18, y + 0.25, 4.10, 0.30, 13, DARK)
    add_text(slide, h4, 9.05, y + 0.23, 3.10, 0.34, 16, c, True, PP_ALIGN.RIGHT)
add_text(slide, "Thông điệp chính", 0.75, 6.42, 2.20, 0.28, 12, GRAY, True)
add_text(slide, "ALNS-D mạnh nhất ở môi trường động cao — nhưng phụ thuộc ngân sách tính toán.",
         2.90, 6.32, 9.68, 0.40, 16, NAVY, True)
footer(slide, 16)

# 17 - Limitations
slide = prs.slides.add_slide(prs.slide_layouts[6])
rect(slide, 0, 0, 13.333, 7.5, WHITE)
title(slide, "Hạn chế và hướng phát triển", "05 • Đánh giá")
rect(slide, 0.75, 1.52, 5.72, 4.88, LIGHT, True, MID)
rect(slide, 6.86, 1.52, 5.72, 4.88, RGBColor(232, 241, 250), True, MID)
add_text(slide, "HẠN CHẾ", 1.08, 1.86, 2.20, 0.28, 12, RED, True)
bullet_list(slide, [
    "Chưa đánh giá trên mạng TP.HCM quy mô lớn",
    "Giới hạn mô phỏng, chưa triển khai thực tế",
    "Số seed H3–H4 còn thấp hơn H1–H2",
], 1.08, 2.36, 5.02, 3.10, 15)
add_text(slide, "HƯỚNG PHÁT TRIỂN", 7.18, 1.86, 2.80, 0.28, 12, BLUE, True)
bullet_list(slide, [
    "Thử nghiệm trên dữ liệu HCM thực",
    "Đa mục tiêu mềm dẻo và không chắc chắn",
    "Tích hợp học thích nghi / machine learning",
    "Triển khai pilot và đo phản hồi vận hành",
], 7.18, 2.36, 5.02, 3.32, 15)
footer(slide, 17)

# 18 - Conclusion
slide = prs.slides.add_slide(prs.slide_layouts[6])
rect(slide, 0, 0, 13.333, 7.5, NAVY)
rect(slide, 0, 0, 13.333, 0.14, CYAN)
add_text(slide, "KẾT LUẬN", 0.75, 0.70, 3.2, 0.34, 12, CYAN, True)
add_text(slide, "ALNS-D là một hướng tiếp cận khả thi\ncho bài toán giao nhận hàng động",
         0.75, 1.28, 8.70, 1.32, 31, WHITE, True)
conclusions = [
    ("1", "Ổn định lộ trình", "Đóng băng cam kết"),
    ("2", "Quyết định nhanh", "Bộ lọc ứng viên"),
    ("3", "Dựa ngân sách", "Trọng số thích nghi"),
]
for i, (n, h, d) in enumerate(conclusions):
    x = 0.75 + i * 4.05
    rect(slide, x, 3.28, 3.72, 1.76, RGBColor(26, 55, 86), True, RGBColor(55, 82, 110))
    add_text(slide, n, x + 0.28, 3.58, 0.48, 0.28, 14, CYAN, True)
    add_text(slide, h, x + 0.82, 3.52, 2.58, 0.36, 14, WHITE, True)
    add_text(slide, d, x + 0.82, 4.08, 2.58, 0.32, 11, RGBColor(210,225,238))
add_text(slide, "Cảm ơn thầy cô và các bạn đã lắng nghe",
         0.75, 5.72, 11.83, 0.48, 20, WHITE, True, PP_ALIGN.CENTER)
add_text(slide, "Q&A", 0.75, 6.42, 11.83, 0.42, 18, ORANGE, True, PP_ALIGN.CENTER)

prs.save(OUT)
print(OUT)
