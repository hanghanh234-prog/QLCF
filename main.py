import sys
import json
import os
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import (
    QMessageBox, QComboBox, QTableWidgetItem, QHBoxLayout,
    QWidget, QPushButton, QLineEdit, QHeaderView, QLabel
)
from PyQt5.QtCore import Qt, QDate, QSize, QTimer
from PyQt5.QtGui import QFont, QFontMetrics
import re
import traceback
from PyQt5.QtCore import qInstallMessageHandler

def _qt_message(mode, context, message):
    """In cảnh báo của Qt; riêng lỗi 'Point size' thì in thêm dòng code Python gây ra nó."""
    print(message)
    if "Point size" in message:
        traceback.print_stack()

qInstallMessageHandler(_qt_message)
import pymysql

# ===================== CỠ CHỮ =====================
# Dùng đơn vị pt (giống lap_don_hang.ui) để chữ tự phóng theo độ phân giải màn hình
CO_CHU_THUONG = 10      # pt - ô nhập, nút, combobox
CO_CHU_NHAN = 11        # pt - nhãn (Mã phiếu nhập, Ngày nhập...), in đậm
CO_CHU_TIEU_DE = 36     # cỡ chữ tiêu đề "Nhập nguyên liệu / Phiếu nhập" (tính theo pixel màn hình)
CO_CHU_MENU = 12        # pt - menu bên trái
CO_CHU_NUT = 12         # pt - nút Thêm dòng / Xóa dòng / Làm mới / Lưu phiếu nhập
CO_CHU_TIEU_DE_BANG = 12  # pt - tiêu đề cột của bảng
CO_CHU_BANG = 12        # pt - chữ trong bảng
CAO_DONG_BANG = 60

# ===================== ĐỊNH DẠNG MÃ PHIẾU NHẬP =====================
TIEN_TO_MA_PN = "PN"   # tiền tố
SO_CHU_SO_MA_PN = 3    # số chữ số -> PN001, PN002, ...
# ========================================================

def them_style(widget, qss):
    """Nối thêm style, không ghi đè style gốc trong file .ui."""
    cu = widget.styleSheet().strip()
    if cu and "{" not in cu:
        cu = "* { " + cu + " }"
    widget.setStyleSheet(cu + "\n" + qss)

class NhapNguyenLieuWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # Lấy đường dẫn tuyệt đối của thư mục chứa file main.py hiện tại
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.ui_path = os.path.join(base_dir, "cafe.ui")
        self.draft_path = os.path.join(base_dir, "draft.json")
        
        # Đưa thư mục làm việc về đúng thư mục chứa script để load ảnh/icon trong UI
        os.chdir(base_dir)
        uic.loadUi(self.ui_path, self)
        
        # Đồng bộ giao diện
        self.chinh_giao_dien()
        
        # Cấu hình bảng 6 cột
        self.tableChiTiet.setColumnCount(6)
        self.tableChiTiet.setHorizontalHeaderLabels([
            "STT", "Nguyên liệu", "Số lượng",
            "Đơn giá nhập", "Thành tiền", "Thao tác"
        ])
        self.tableChiTiet.verticalHeader().setVisible(False)
        self.tableChiTiet.setAlternatingRowColors(True)
        self.tableChiTiet.setShowGrid(True)
        self.tableChiTiet.setWordWrap(False)
        self.tableChiTiet.setMinimumHeight(300)
        
        them_style(self.tableChiTiet, f"""
            QTableWidget {{
                background-color: #FFFFFF; alternate-background-color: #F7F2EB;
                color: #30251E; gridline-color: #E5D9CC; border: 1px solid #D8C8B8;
                border-radius: 5px; font-size: {CO_CHU_BANG}pt;
                selection-background-color: #D8C0AA; selection-color: #30251E;
            }}
            QTableWidget::item {{ padding: 5px; }}
        """)
        # Tiêu đề cột: đặt thẳng lên header để chắc chắn ăn cỡ chữ
        self.tableChiTiet.horizontalHeader().setStyleSheet(f"""
            QHeaderView::section {{
                background-color: #EDE1D4; color: #493020; padding: 8px; border: none;
                border-right: 1px solid #D8C8B8; border-bottom: 1px solid #D8C8B8;
                font-size: {CO_CHU_TIEU_DE_BANG}pt; font-weight: bold;
            }}
        """)
        self.tableChiTiet.horizontalHeader().setMinimumHeight(52)
        self.cau_hinh_do_rong_cot()
        
        # Gắn sự kiện cho các nút chức năng
        self.btnThemDong.clicked.connect(self.them_dong_moi)
        self.btnLamMoi.clicked.connect(self.lam_moi_form)
        self.btnLuuPhieuNhap.clicked.connect(self.luu_phieu_nhap)
        
        # Gắn sự kiện mở màn hình Tìm kiếm đơn hàng từ menu bên trái
        for btn in self.findChildren(QPushButton):
            text = btn.text().strip().lower()
            if text in ("tìm kiếm", "tìm kiếm đơn hàng"):
                btn.clicked.connect(self.mo_tim_kiem)
            elif text in ("đơn hàng", "lập đơn hàng"):
                btn.clicked.connect(self.mo_lap_don_hang)
            elif text == "báo cáo":
                btn.clicked.connect(self.mo_bao_cao)

        # Lắng nghe sự kiện để tự động lưu nháp
        self.txtMaPhieuNhap.textChanged.connect(self.save_draft)
        self.dateNgayNhap.dateChanged.connect(self.save_draft)
        self.cbNhaCungCap.currentIndexChanged.connect(self.save_draft)
        self.cbNhanVienNhap.currentIndexChanged.connect(self.save_draft)

        self.txtMaPhieuNhap.setReadOnly(True)   # mã tự tăng, không gõ tay

        # Load dữ liệu danh mục từ database
        self.load_combobox_data()
        self.danh_sach_nguyen_lieu = self.lay_danh_sach_nguyen_lieu()

        # Khôi phục lại bản nháp cũ nếu có, rồi gán mã phiếu tự tăng
        self.load_draft()
        self.tao_ma_phieu_moi()

    def mo_tim_kiem(self):
        """Mở màn Tìm kiếm đơn hàng và đóng màn hình nhập nguyên liệu hiện tại."""
        from tim_kiem_don_hang import TimKiemDonHangWindow
        self.cua_so = TimKiemDonHangWindow()
        self.cua_so.show()
        self.close()

    def mo_bao_cao(self):
        from bao_cao_ton_hang import BaoCaoTonHangWindow
        self.cua_so = BaoCaoTonHangWindow()
        self.cua_so.setGeometry(self.geometry())
        self.cua_so.show()
        self.close()

    def mo_lap_don_hang(self):
        """Mở màn hình Lập đơn hàng và đồng bộ kích thước cửa sổ."""
        from lap_don_hang import LapDonHangWindow
        self.cua_so = LapDonHangWindow()
        self.cua_so.setGeometry(self.geometry())
        self.cua_so.show()
        self.close()
    def chinh_giao_dien(self):
        """Đồng bộ giao diện (màu + cỡ chữ) theo tim_kiem_don_hang / lap_don_hang."""
        # Nền sidebar nâu đậm giống các màn hình kia
        them_style(self.frame, "QFrame#frame { background-color: #493020; border: none; }")

        them_style(self, f"""
            QMainWindow {{ background-color: #F7F3EC; }}
            QMainWindow, QWidget {{
                font-family: "Segoe UI";
                color: #30251E;
            }}
            QLabel {{
                color: #493020;
                font-size: {CO_CHU_NHAN}pt;
                font-weight: bold;
                background-color: transparent;
            }}
            QLineEdit, QComboBox, QDateEdit, QSpinBox {{
                background-color: #FFFFFF;
                color: #30251E;
                border: 1px solid #D8C8B8;
                border-radius: 5px;
                padding: 6px 9px;
                min-height: 28px;
                font-size: {CO_CHU_THUONG}pt;
            }}
            QLineEdit:focus {{ border: 1px solid #805B46; }}
            QComboBox:hover, QDateEdit:hover {{ border: 1px solid #805B46; }}
            QPushButton {{
                background-color: #EDE1D4;
                color: #493020;
                border: 1px solid #D8C8B8;
                border-radius: 6px;
                padding: 8px 18px;
                min-height: 28px;
                font-size: {CO_CHU_NUT}pt;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #D8C0AA; }}
        """)

        for label in self.findChildren(QLabel):
            text = label.text().strip().lower()
            if text == "nhập nguyên liệu / phiếu nhập":
                # Đổi px -> pt theo DPI máy để toàn bộ style dùng chung 1 đơn vị (tránh cảnh báo Point size)
                pt_tieu_de = CO_CHU_TIEU_DE * 72 / self.logicalDpiY()
                them_style(label, f"QLabel {{ font-size: {pt_tieu_de:.1f}pt; font-weight: 700; color: #493020; }}")
                # Nhãn tiêu đề đặt tọa độ cố định trong .ui -> nới rộng cho vừa chữ, tránh bị cắt
                f_td = QFont("Segoe UI"); f_td.setPointSizeF(pt_tieu_de); f_td.setBold(True)
                cao = int(CO_CHU_TIEU_DE * 1.6)
                label.setFixedSize(QFontMetrics(f_td).horizontalAdvance(label.text()) + 40, cao)
                self.frame_3.setMinimumHeight(cao + 6)

        for button in self.findChildren(QPushButton):
            text = button.text().strip().lower()
            if text in ("lưu phiếu nhập", "lưu"):
                them_style(button, f"""
                    QPushButton {{ background-color: #805B46; color: #FFFFFF; border: none; border-radius: 6px;
                                   padding: 8px 18px; font-size: {CO_CHU_NUT}pt; font-weight: bold; }}
                    QPushButton:hover {{ background-color: #67442F; }}
                    QPushButton:pressed {{ background-color: #493020; }}""")
            elif text in ("xóa dòng", "xóa"):
                them_style(button, f"""
                    QPushButton {{ background-color: #F9E3E0; color: #A33C35; border: 1px solid #EBC5C0;
                                   border-radius: 6px; padding: 8px 18px; font-size: {CO_CHU_NUT}pt; font-weight: bold; }}
                    QPushButton:hover {{ background-color: #F2CFCA; }}""")
            elif text in ("thêm dòng", "làm mới"):
                them_style(button, f"""
                    QPushButton {{ background-color: #EDE1D4; color: #493020; border: 1px solid #D8C8B8;
                                   border-radius: 6px; padding: 8px 18px; font-size: {CO_CHU_NUT}pt; font-weight: bold; }}
                    QPushButton:hover {{ background-color: #D8C0AA; }}""")
            elif text in ("đơn hàng", "nguyên liệu", "tìm kiếm", "tìm kiếm đơn hàng", "báo cáo", "doanh thu"):
                button.setMinimumHeight(46)
                # Menu trái: giống hệt tim_kiem_don_hang.ui (chữ kem #FFF7ED trên nền nâu)
                them_style(button, f"""
                    QPushButton {{ background-color: transparent; color: #FFF7ED; border: none; border-radius: 6px;
                                   padding: 20px; text-align: left; font-size: {CO_CHU_MENU}pt; font-weight: normal; }}
                    QPushButton:hover {{ background-color: #67442F; }}
                    QPushButton:pressed {{ background-color: #805B46; }}""")

    def cau_hinh_do_rong_cot(self):
        """Các cột kéo được; độ rộng tự chia lại theo cửa sổ (xem tinh_do_rong_cot)."""
        header = self.tableChiTiet.horizontalHeader()
        header.setStretchLastSection(False)
        for i in range(6):
            header.setSectionResizeMode(i, QHeaderView.Interactive)
        self.tinh_do_rong_cot()

    def tinh_do_rong_cot(self):
        """Mỗi cột có độ rộng tối thiểu đủ chứa chữ (đo theo cỡ chữ thật),
        phần còn dư được chia theo tỉ lệ để các cột cân đối."""
        bang = self.tableChiTiet
        header = bang.horizontalHeader()

        f_head = QFont("Segoe UI"); f_head.setPointSize(CO_CHU_TIEU_DE_BANG); f_head.setBold(True)
        f_cell = QFont("Segoe UI"); f_cell.setPointSize(CO_CHU_BANG)
        fm_head = QFontMetrics(f_head)
        cw = QFontMetrics(f_cell).horizontalAdvance("0")   # bề rộng 1 chữ số

        def rong_tieu_de(text):
            return fm_head.horizontalAdvance(text) + 44    # + padding & lề của header

        mins = [
            max(rong_tieu_de("STT"), 4 * cw + 24),               # STT
            max(rong_tieu_de("Nguyên liệu"), 11 * cw),           # Nguyên liệu (combobox)
            max(rong_tieu_de("Số lượng"), 11 * cw + 60),         # Số lượng + đơn vị
            max(rong_tieu_de("Đơn giá nhập"), 9 * cw + 30),      # Đơn giá nhập
            max(rong_tieu_de("Thành tiền"), 9 * cw + 24),        # Thành tiền
            max(rong_tieu_de("Thao tác"), 9 * cw + 70),          # nút Sửa / Xóa
        ]
        trong_so = [0, 3, 2, 2, 2, 2]   # tỉ lệ chia phần dư (STT giữ nguyên)

        tong_rong = bang.viewport().width()
        du = max(0, tong_rong - sum(mins))
        tong_ts = sum(trong_so)
        for i in range(6):
            header.resizeSection(i, int(mins[i] + du * trong_so[i] / tong_ts))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self.tinh_do_rong_cot)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self.tinh_do_rong_cot)

    def tao_ma_phieu_moi(self):
        """Mã phiếu tự tăng theo định dạng cố định: TIEN_TO_MA_PN + SO_CHU_SO_MA_PN chữ số
        (PN001, PN002, ...). Chỉ tính các mã đúng định dạng này; mã lạ (vd '01') bị bỏ qua."""
        lon_nhat = 0
        mau = re.compile(rf"^{re.escape(TIEN_TO_MA_PN)}(\d+)$")
        conn = self.connect_db()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT MaPN FROM phieu_nhap")
                    for r in cur.fetchall():
                        m = mau.match(str(r["MaPN"]).strip())
                        if m:
                            lon_nhat = max(lon_nhat, int(m.group(1)))
            except Exception as e:
                print("Lỗi tạo mã phiếu:", e)
            finally:
                conn.close()
        self.txtMaPhieuNhap.setText(f"{TIEN_TO_MA_PN}{lon_nhat + 1:0{SO_CHU_SO_MA_PN}d}")

    def connect_db(self):
        try:
            return pymysql.connect(
                host='localhost', port=3306, user='root', password='123456789',
                database='Cafe', charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
        except Exception as e:
            QMessageBox.critical(self, "Lỗi kết nối", f"Không thể kết nối đến cơ sở dữ liệu:\n{e}")
            return None

    def load_combobox_data(self):
        conn = self.connect_db()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT MaNCC, TenNCC FROM nha_cung_cap")
                self.cbNhaCungCap.blockSignals(True)
                self.cbNhaCungCap.clear()
                self.cbNhaCungCap.addItem("-- Chọn nhà cung cấp --", None)
                for ncc in cur.fetchall():
                    self.cbNhaCungCap.addItem(ncc['TenNCC'], ncc['MaNCC'])
                self.cbNhaCungCap.blockSignals(False)

                cur.execute("SELECT MaNV, HoTen FROM nhan_vien")
                self.cbNhanVienNhap.blockSignals(True)
                self.cbNhanVienNhap.clear()
                self.cbNhanVienNhap.addItem("-- Chọn nhân viên nhập --", None)
                for nv in cur.fetchall():
                    self.cbNhanVienNhap.addItem(nv['HoTen'], nv['MaNV'])
                self.cbNhanVienNhap.blockSignals(False)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi tải dữ liệu danh mục:\n{e}")
        finally:
            conn.close()

    def lay_danh_sach_nguyen_lieu(self):
        conn = self.connect_db()
        if not conn: return []
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT MaNL, TenNL, DonViTinh FROM nguyen_lieu")
                return cur.fetchall()
        except Exception:
            return []
        finally:
            conn.close()

    def cap_nhat_stt(self):
        for row in range(self.tableChiTiet.rowCount()):
            item_stt = QTableWidgetItem(f"{row + 1:02d}")
            item_stt.setTextAlignment(Qt.AlignCenter)
            item_stt.setFlags(item_stt.flags() ^ Qt.ItemIsEditable)
            self.tableChiTiet.setItem(row, 0, item_stt)

    def tao_o_so_luong(self, dong):
        khung = QWidget()
        layout = QHBoxLayout(khung)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(5)

        o_so_luong = QLineEdit()
        o_so_luong.setPlaceholderText("Số lượng")
        o_so_luong.setAlignment(Qt.AlignCenter)
        o_so_luong.setStyleSheet(f"QLineEdit {{ font-size: {CO_CHU_BANG}pt; }}")
        o_so_luong.textChanged.connect(lambda _, r=dong: self.tinh_thanh_tien_row(r))
        o_so_luong.textChanged.connect(self.save_draft)

        cb_don_vi = QComboBox()
        cb_don_vi.addItems(["kg", "g", "lít", "gói", "chai"])
        cb_don_vi.setStyleSheet(f"QComboBox {{ font-size: {CO_CHU_BANG}pt; }}")
        cb_don_vi.currentIndexChanged.connect(self.save_draft)

        layout.addWidget(o_so_luong, 2)
        layout.addWidget(cb_don_vi, 1)
        self.tableChiTiet.setCellWidget(dong, 2, khung)

    def chon_nguyen_lieu_change(self, row, combo):
        data = combo.currentData()
        if data:
            _, don_vi = data
            widget_sl = self.tableChiTiet.cellWidget(row, 2)
            if widget_sl:
                cb_don_vi = widget_sl.layout().itemAt(1).widget()
                index = cb_don_vi.findText(don_vi)
                if index >= 0:
                    cb_don_vi.setCurrentIndex(index)
        self.save_draft()

    def tinh_thanh_tien_row(self, row):
        try:
            widget_sl = self.tableChiTiet.cellWidget(row, 2)
            txt_dongia = self.tableChiTiet.cellWidget(row, 3)
            if widget_sl and txt_dongia:
                o_so_luong = widget_sl.layout().itemAt(0).widget()
                sl_val = float(o_so_luong.text().strip()) if o_so_luong.text().strip() else 0
                dg_val = float(txt_dongia.text().strip()) if txt_dongia.text().strip() else 0
                thanh_tien = sl_val * dg_val
                thanh_tien_str = f"{thanh_tien:,.0f}".replace(",", ".")
                item_tt = self.tableChiTiet.item(row, 4)
                if not item_tt:
                    item_tt = QTableWidgetItem(thanh_tien_str)
                    self.tableChiTiet.setItem(row, 4, item_tt)
                else:
                    item_tt.setText(thanh_tien_str)
        except ValueError:
            pass

    def them_dong_moi(self):
        row = self.tableChiTiet.rowCount()
        self.tableChiTiet.insertRow(row)
        self.tableChiTiet.setRowHeight(row, CAO_DONG_BANG)
        
        self.cap_nhat_stt()
        
        combo_nl = QComboBox()
        combo_nl.setStyleSheet(f"QComboBox {{ font-size: {CO_CHU_BANG}pt; }}")
        combo_nl.addItem("-- Chọn nguyên liệu --", None)
        for nl in self.danh_sach_nguyen_lieu:
            combo_nl.addItem(nl['TenNL'], (nl['MaNL'], nl['DonViTinh']))
        combo_nl.currentIndexChanged.connect(lambda _, r=row, cb=combo_nl: self.chon_nguyen_lieu_change(r, cb))
        self.tableChiTiet.setCellWidget(row, 1, combo_nl)
        
        self.tao_o_so_luong(row)
        
        txt_dongia = QLineEdit()
        txt_dongia.setPlaceholderText("Đơn giá")
        txt_dongia.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        txt_dongia.setStyleSheet(f"QLineEdit {{ font-size: {CO_CHU_BANG}pt; }}")
        txt_dongia.textChanged.connect(lambda _, r=row: self.tinh_thanh_tien_row(r))
        txt_dongia.textChanged.connect(self.save_draft)
        self.tableChiTiet.setCellWidget(row, 3, txt_dongia)
        
        item_tt = QTableWidgetItem("0")
        item_tt.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        item_tt.setFlags(item_tt.flags() ^ Qt.ItemIsEditable)
        self.tableChiTiet.setItem(row, 4, item_tt)
        
        khung_nut = QWidget()
        layout_nut = QHBoxLayout(khung_nut)
        layout_nut.setContentsMargins(3, 3, 3, 3)
        layout_nut.setSpacing(5)
        btn_sua = QPushButton("Sửa")
        btn_xoa = QPushButton("Xóa")
        btn_sua.setStyleSheet(f"QPushButton {{ background-color: #EDE1D4; color: #493020; border: none; border-radius: 5px; padding: 6px; font-size: {CO_CHU_BANG}pt; font-weight: bold; }}")
        btn_xoa.setStyleSheet(f"QPushButton {{ background-color: #F9E3E0; color: #A33C35; border: none; border-radius: 5px; padding: 6px; font-size: {CO_CHU_BANG}pt; font-weight: bold; }}")

        btn_sua.clicked.connect(lambda _, r=row: self.sua_dong(r))
        btn_xoa.clicked.connect(lambda _, r=row: self.xoa_dong(r))

        layout_nut.addWidget(btn_sua)
        layout_nut.addWidget(btn_xoa)
        self.tableChiTiet.setCellWidget(row, 5, khung_nut)
        self.save_draft()

    def sua_dong(self, row):
        QMessageBox.information(self, "Thông báo", f"Đang thao tác chỉnh sửa dòng {row + 1}")

    def xoa_dong(self, row):
        self.tableChiTiet.removeRow(row)
        self.cap_nhat_stt()
        self.save_draft()

    def lam_moi_form(self):
        self.dateNgayNhap.setDate(QDate.currentDate())
        if self.cbNhaCungCap.count() > 0: self.cbNhaCungCap.setCurrentIndex(0)
        if self.cbNhanVienNhap.count() > 0: self.cbNhanVienNhap.setCurrentIndex(0)
        self.tableChiTiet.setRowCount(0)
        if os.path.exists(self.draft_path):
            try: os.remove(self.draft_path)
            except Exception: pass
        self.tao_ma_phieu_moi()

    def save_draft(self):
        try:
            draft_data = {
                "ma_phieu": self.txtMaPhieuNhap.text(),
                "ngay_nhap": self.dateNgayNhap.date().toString("yyyy-MM-dd"),
                "ncc_index": self.cbNhaCungCap.currentIndex(),
                "nv_index": self.cbNhanVienNhap.currentIndex(),
                "rows": []
            }
            for row in range(self.tableChiTiet.rowCount()):
                combo_nl = self.tableChiTiet.cellWidget(row, 1)
                nl_index = combo_nl.currentIndex() if combo_nl else 0
                widget_sl = self.tableChiTiet.cellWidget(row, 2)
                soluong, donvi_index = "", 0
                if widget_sl:
                    soluong = widget_sl.layout().itemAt(0).widget().text()
                    donvi_index = widget_sl.layout().itemAt(1).widget().currentIndex()
                txt_dg = self.tableChiTiet.cellWidget(row, 3)
                dongia = txt_dg.text() if txt_dg else ""
                draft_data["rows"].append({"nl_index": nl_index, "soluong": soluong, "donvi_index": donvi_index, "dongia": dongia})
            with open(self.draft_path, "w", encoding="utf-8") as f:
                json.dump(draft_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print("Lỗi lưu nháp:", e)

    def closeEvent(self, event):
        self.save_draft()
        event.accept()

    def load_draft(self):
        if not os.path.exists(self.draft_path): return
        try:
            with open(self.draft_path, "r", encoding="utf-8") as f:
                draft_data = json.load(f)
            ngay_str = draft_data.get("ngay_nhap", "")
            if ngay_str: self.dateNgayNhap.setDate(QDate.fromString(ngay_str, "yyyy-MM-dd"))
            if self.cbNhaCungCap.count() > draft_data.get("ncc_index", 0):
                self.cbNhaCungCap.setCurrentIndex(draft_data.get("ncc_index", 0))
            if self.cbNhanVienNhap.count() > draft_data.get("nv_index", 0):
                self.cbNhanVienNhap.setCurrentIndex(draft_data.get("nv_index", 0))
            for row_data in draft_data.get("rows", []):
                self.them_dong_moi()
                row = self.tableChiTiet.rowCount() - 1
                combo_nl = self.tableChiTiet.cellWidget(row, 1)
                if combo_nl and combo_nl.count() > row_data.get("nl_index", 0):
                    combo_nl.setCurrentIndex(row_data.get("nl_index", 0))
                widget_sl = self.tableChiTiet.cellWidget(row, 2)
                if widget_sl:
                    widget_sl.layout().itemAt(0).widget().setText(row_data.get("soluong", ""))
                    cb_dv = widget_sl.layout().itemAt(1).widget()
                    if cb_dv.count() > row_data.get("donvi_index", 0):
                        cb_dv.setCurrentIndex(row_data.get("donvi_index", 0))
                txt_dg = self.tableChiTiet.cellWidget(row, 3)
                if txt_dg: txt_dg.setText(row_data.get("dongia", ""))
        except Exception as e:
            print("Lỗi load nháp:", e)

    def luu_phieu_nhap(self):
        ma_phieu = self.txtMaPhieuNhap.text().strip()
        ngay_nhap = self.dateNgayNhap.date().toString("yyyy-MM-dd")
        ma_ncc = self.cbNhaCungCap.currentData()
        ma_nv = self.cbNhanVienNhap.currentData()

        if not ma_phieu:
            QMessageBox.warning(self, "Cảnh báo", "Mã phiếu nhập không được để trống!")
            self.txtMaPhieuNhap.setFocus()
            return
        if not ma_ncc:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn Nhà cung cấp hợp lệ!")
            self.cbNhaCungCap.setFocus()
            return
        if not ma_nv:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn Nhân viên nhập hợp lệ!")
            self.cbNhanVienNhap.setFocus()
            return

        row_count = self.tableChiTiet.rowCount()
        if row_count == 0:
            QMessageBox.warning(self, "Cảnh báo", "Phiếu nhập phải có ít nhất một dòng nguyên liệu chi tiết!")
            return

        chi_tiet_list = []
        tong_tien_phieu = 0

        for row in range(row_count):
            combo_nl = self.tableChiTiet.cellWidget(row, 1)
            ma_nl_data = combo_nl.currentData() if combo_nl else None
            ma_nl = ma_nl_data[0] if ma_nl_data else None
            widget_sl = self.tableChiTiet.cellWidget(row, 2)
            o_so_luong = widget_sl.layout().itemAt(0).widget() if widget_sl else None
            txt_dongia = self.tableChiTiet.cellWidget(row, 3)

            if not ma_nl:
                QMessageBox.warning(self, "Cảnh báo", f"Dòng {row + 1}: Vui lòng chọn nguyên liệu!")
                return
            if not o_so_luong or not o_so_luong.text().strip():
                QMessageBox.warning(self, "Cảnh báo", f"Dòng {row + 1}: Số lượng không được để trống!")
                return
            if not txt_dongia or not txt_dongia.text().strip():
                QMessageBox.warning(self, "Cảnh báo", f"Dòng {row + 1}: Đơn giá nhập không được để trống!")
                return

            try:
                so_luong = float(o_so_luong.text().strip())
                don_gia = float(txt_dongia.text().strip())
                if so_luong <= 0 or don_gia < 0:
                    QMessageBox.warning(self, "Cảnh báo", f"Dòng {row + 1}: Số lượng phải > 0 và đơn giá không được âm!")
                    return
            except ValueError:
                QMessageBox.warning(self, "Cảnh báo", f"Dòng {row + 1}: Định dạng số không hợp lệ!")
                return

            tong_tien_phieu += so_luong * don_gia
            chi_tiet_list.append({"MaNL": ma_nl, "SoLuong": so_luong, "DonGiaNhap": don_gia})

        connection = self.connect_db()
        if not connection: return

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT MaPN FROM phieu_nhap WHERE MaPN = %s", (ma_phieu,))
                if cursor.fetchone():
                    QMessageBox.warning(self, "Cảnh báo", f"Mã phiếu nhập '{ma_phieu}' đã tồn tại trong hệ thống!")
                    return

                sql_phieu = "INSERT INTO phieu_nhap (MaPN, NgayNhap, MaNCC, MaNV, TongTien, GhiChu) VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.execute(sql_phieu, (ma_phieu, ngay_nhap, ma_ncc, ma_nv, tong_tien_phieu, "Nhập kho nguyên liệu"))

                sql_ct = "INSERT INTO chi_tiet_phieu_nhap (MaPN, MaNL, SoLuong, DonGiaNhap) VALUES (%s, %s, %s, %s)"
                for ct in chi_tiet_list:
                    cursor.execute(sql_ct, (ma_phieu, ct['MaNL'], ct['SoLuong'], ct['DonGiaNhap']))
                    cursor.execute("UPDATE nguyen_lieu SET SoLuongTon = SoLuongTon + %s, DonGia = %s WHERE MaNL = %s", 
                                   (ct['SoLuong'], ct['DonGiaNhap'], ct['MaNL']))

            connection.commit()

            # Đếm lại ngay trong DB để xác nhận phiếu đã nằm trong MySQL (và đang nói chuyện với server nào)
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) AS n, @@port AS p FROM phieu_nhap")
                kq = cursor.fetchone()

            # Giữ nguyên nội dung đã điền (bảng, NCC, nhân viên, ngày) và vẫn lưu nháp vào draft.json;
            # chỉ nhảy sang mã phiếu kế tiếp. Muốn xóa sạch thì bấm "Làm mới".
            self.tao_ma_phieu_moi()
            self.save_draft()
            QMessageBox.information(
                self, "Thành công",
                f"Đã lưu phiếu nhập [{ma_phieu}] thành công vào CSDL!\n\n"
                f"(MySQL cổng {kq['p']} - bảng phieu_nhap hiện có {kq['n']} phiếu)"
            )
        except Exception as e:
            connection.rollback()
            QMessageBox.critical(self, "Lỗi Database", f"Đã xảy ra lỗi khi lưu:\n{str(e)}")
        finally:
            connection.close()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = NhapNguyenLieuWindow()
    window.show()
    sys.exit(app.exec_())