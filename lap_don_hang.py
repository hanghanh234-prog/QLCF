import sys
import os
from datetime import datetime
from decimal import Decimal
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import (
    QMessageBox, QComboBox, QTableWidgetItem, QWidget,
    QPushButton, QHeaderView, QLabel, QLineEdit, QTableWidget, QAbstractItemView
)
from PyQt5.QtCore import Qt, QDate
import pymysql

# ===================== KẾT NỐI MYSQL (SỬA CHỖ NÀY) =====================
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123456789",
    "database": "Cafe",
    "charset": "utf8mb4",
}
# =======================================================================

# ===================== TÊN WIDGET TRONG FILE .UI =======================
# Mở lap_don_hang.ui bằng Qt Designer, bấm vào từng ô, xem "objectName"
# ở bảng Property Editor rồi sửa cho khớp. Đặt DEBUG_TEN = True để in
# ra tất cả tên widget đang có khi chạy.
DEBUG_TEN = False
TEN = {
    "ma_dh":       "txtMaDonHang",         # ô Mã đơn hàng (QLineEdit)
    "khach_hang":  "txtKhachHang",    # ô Khách hàng (QLineEdit, nhập SĐT)
    "ngay_dat":    "dateNgayDat",     # ô Ngày đặt (QDateEdit)
    "nhan_vien":   "cboNhanVien",     # Nhân viên (QComboBox)
    "san_pham":    "cboSanPham",      # Sản phẩm (QComboBox)
    "kich_co":     "cboKichCo",       # Kích cỡ (QComboBox)
    "topping":     "cboTopping",      # Topping (QComboBox)
    "so_luong":    "spnSoLuong",      # Số lượng (QSpinBox)
    "bang":        "tableChiTiet",      # Bảng sản phẩm (QTableWidget)
    "btn_them":    "btnThemSanPham",  # nút Thêm sản phẩm
    "btn_xoa":     "btnXoaSanPham",   # nút Xóa sản phẩm
    "tong_tien":   "txtTongTien",     # Tổng tiền (QLineEdit)
    "khuyen_mai":  "txtKhuyenMai",    # Khuyến mãi (QLineEdit, nhập % giảm)
    "thanh_tien":  "txtThanhTien",    # Thành tiền (QLineEdit)
    "pttt":        "cboPhuongThucTT",   # Phương thức thanh toán (QComboBox)
    "btn_lam_moi": "btnLamMoi",       # nút Làm mới
    "btn_luu":     "btnLuuDon",   # nút Lưu đơn hàng
}

# ===================== CỠ CHỮ (px) =====================
CO_CHU_THUONG = 15
CO_CHU_TIEU_DE = 28
CO_CHU_MENU = 16
CO_CHU_BANG = 15
CAO_DONG_BANG = 48
# ========================================================

UI_FILE = "lap_don_hang.ui"
TIEN_TO_MA = "DH"   # mã đơn hàng: DH001, DH002, ...


class TonKhoKhongDu(Exception):
    """Không đủ nguyên liệu để pha các món trong đơn."""
    def __init__(self, danh_sach):
        super().__init__("Không đủ nguyên liệu")
        self.danh_sach = danh_sach


def dinh_dang_so(so):
    return f"{float(so):.3f}".rstrip("0").rstrip(".") or "0"


def them_style(widget, qss):
    cu = widget.styleSheet().strip()
    if cu and "{" not in cu:
        cu = "* { " + cu + " }"
    widget.setStyleSheet(cu + "\n" + qss)


def ket_noi():
    return pymysql.connect(**DB_CONFIG)


def dinh_dang_tien(so):
    return f"{int(so):,}".replace(",", ".")


class LapDonHangWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(base_dir)
        uic.loadUi(os.path.join(base_dir, UI_FILE), self)

        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)

        if DEBUG_TEN:
            for w in self.findChildren(QWidget):
                if w.objectName():
                    print(type(w).__name__, "->", w.objectName())

        # Danh sách sản phẩm của đơn đang lập (chưa lưu)
        self.ds = []   # mỗi phần tử: dict(ten_sp, kich_co, topping, so_luong, don_gia, thanh_tien)

        self.chinh_giao_dien()
        self.lay_widget()
        self.cai_dat_bang()

        try:
            self.nap_du_lieu_combo()
        except Exception as e:
            QMessageBox.critical(
                self, "Lỗi kết nối MySQL",
                f"Không kết nối được database.\nKiểm tra lại DB_CONFIG và đã chạy file them_bang_don_hang.sql chưa.\n\nChi tiết: {e}"
            )

        self.lam_moi()

        # Nối nút bấm
        self.btn_them.clicked.connect(self.them_san_pham)
        self.btn_xoa.clicked.connect(self.xoa_san_pham)
        self.btn_lam_moi.clicked.connect(self.lam_moi)
        self.btn_luu.clicked.connect(self.luu_don_hang)
        self.txt_khuyen_mai.textChanged.connect(self.tinh_tien)

        # Menu bên trái
        for btn in self.findChildren(QPushButton):
            text = btn.text().strip().lower()
            if text in ("nguyên liệu", "nhập nguyên liệu"):
                btn.clicked.connect(self.mo_nhap_nguyen_lieu)
            elif text in ("tìm kiếm", "tìm kiếm đơn hàng"):
                btn.clicked.connect(self.mo_tim_kiem)
            elif text == "báo cáo":
                btn.clicked.connect(self.mo_bao_cao)

    def lay_widget(self):
        def w(khoa):
            ten = TEN[khoa]
            obj = self.findChild(QWidget, ten)
            if obj is None:
                raise RuntimeError(
                    f"Không tìm thấy widget tên '{ten}' trong {UI_FILE}.\n"
                    f"Sửa lại mục '{khoa}' trong dict TEN ở đầu file."
                )
            return obj

        self.txt_ma_dh = w("ma_dh")
        self.txt_khach = w("khach_hang")
        self.date_ngay = w("ngay_dat")
        self.cbo_nv = w("nhan_vien")
        self.cbo_sp = w("san_pham")
        self.cbo_kc = w("kich_co")
        self.cbo_tp = w("topping")
        self.spn_sl = w("so_luong")
        self.bang = w("bang")
        self.btn_them = w("btn_them")
        self.btn_xoa = w("btn_xoa")
        self.txt_tong = w("tong_tien")
        self.txt_khuyen_mai = w("khuyen_mai")
        self.txt_thanh_tien = w("thanh_tien")
        self.cbo_pttt = w("pttt")
        self.btn_lam_moi = w("btn_lam_moi")
        self.btn_luu = w("btn_luu")

        # Các ô tự tính / tự sinh thì chỉ cho xem, không cho gõ
        for o in (self.txt_ma_dh, self.txt_tong, self.txt_thanh_tien):
            o.setReadOnly(True)

        # Ô Khuyến mãi trong file .ui đang bị khóa (readOnly) -> mở ra để gõ % giảm
        self.txt_khuyen_mai.setReadOnly(False)

        self.spn_sl.setMinimum(1)
        self.txt_khuyen_mai.setPlaceholderText("% giảm, ví dụ 10")
        self.txt_khach.setPlaceholderText("Số điện thoại (không bắt buộc, khách thân thiết mới cần)")

    def cai_dat_bang(self):
        tieu_de = ["STT", "Sản phẩm", "Kích cỡ", "Topping", "Số lượng", "Đơn giá", "Thành tiền"]
        self.bang.setColumnCount(len(tieu_de))
        self.bang.setHorizontalHeaderLabels(tieu_de)
        self.bang.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.bang.verticalHeader().setDefaultSectionSize(CAO_DONG_BANG)
        self.bang.verticalHeader().setVisible(False)
        self.bang.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.bang.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.bang.setSelectionMode(QAbstractItemView.SingleSelection)

    # ĐỌC DỮ LIỆU TỪ MYSQL
    def nap_du_lieu_combo(self):
        conn = ket_noi()
        try:
            with conn.cursor() as cur:
                # Nhân viên: hiện tên, ngầm giữ mã
                self.cbo_nv.clear()
                cur.execute("SELECT MaNV, HoTen FROM nhan_vien ORDER BY HoTen")
                for ma, ten in cur.fetchall():
                    self.cbo_nv.addItem(ten, ma)

                # Sản phẩm: ngầm giữ giá
                self.cbo_sp.clear()
                cur.execute("SELECT MaSP, TenSP, Gia FROM menu_san_pham ORDER BY TenSP")
                for ma, ten, gia in cur.fetchall():
                    self.cbo_sp.addItem(ten, (ma, gia))

                # Kích cỡ: ngầm giữ phụ thu
                self.cbo_kc.clear()
                cur.execute("SELECT TenKC, PhuThu FROM menu_kich_co ORDER BY PhuThu")
                for ten, phu_thu in cur.fetchall():
                    self.cbo_kc.addItem(ten, phu_thu)

                # Topping: ngầm giữ giá
                self.cbo_tp.clear()
                cur.execute("SELECT TenTP, Gia FROM menu_topping ORDER BY Gia")
                for ten, gia in cur.fetchall():
                    self.cbo_tp.addItem(ten, gia)
        finally:
            conn.close()

        # Phương thức thanh toán
        self.cbo_pttt.clear()
        self.cbo_pttt.addItems(["Tiền mặt", "Chuyển khoản", "Thẻ", "Ví điện tử"])

    def tao_ma_moi(self):
        """Lấy số lớn nhất trong DB rồi +1 -> DH001, DH002, ..."""
        conn = ket_noi()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT MAX(CAST(SUBSTRING(MaDH, %s) AS UNSIGNED)) FROM don_hang",
                    (len(TIEN_TO_MA) + 1,)
                )
                so = cur.fetchone()[0] or 0
        finally:
            conn.close()
        return f"{TIEN_TO_MA}{so + 1:03d}"

    # ------------------------------------------------------------------
    # XỬ LÝ SẢN PHẨM TRONG ĐƠN
    def them_san_pham(self):
        if self.cbo_sp.count() == 0:
            QMessageBox.warning(self, "Thiếu dữ liệu", "Chưa có sản phẩm trong database.")
            return
        so_luong = self.spn_sl.value()
        if so_luong <= 0:
            QMessageBox.warning(self, "Số lượng", "Số lượng phải lớn hơn 0.")
            return

        ma_sp, gia_sp = self.cbo_sp.currentData() or (None, 0)
        phu_thu = self.cbo_kc.currentData() or 0
        gia_tp = self.cbo_tp.currentData() or 0
        don_gia = gia_sp + phu_thu + gia_tp

        self.ds.append({
            "ma_sp": ma_sp,
            "ten_sp": self.cbo_sp.currentText(),
            "kich_co": self.cbo_kc.currentText(),
            "topping": self.cbo_tp.currentText(),
            "so_luong": so_luong,
            "don_gia": don_gia,
            "thanh_tien": don_gia * so_luong,
        })
        self.ve_bang()
        self.tinh_tien()
        self.spn_sl.setValue(1)

    def xoa_san_pham(self):
        dong = self.bang.currentRow()
        if dong < 0:
            QMessageBox.information(self, "Xóa sản phẩm", "Hãy bấm chọn một dòng trong bảng trước.")
            return
        del self.ds[dong]
        self.ve_bang()
        self.tinh_tien()

    def ve_bang(self):
        self.bang.setRowCount(len(self.ds))
        for i, sp in enumerate(self.ds):
            gia_tri = [
                str(i + 1), sp["ten_sp"], sp["kich_co"], sp["topping"],
                str(sp["so_luong"]), dinh_dang_tien(sp["don_gia"]),
                dinh_dang_tien(sp["thanh_tien"]),
            ]
            for c, text in enumerate(gia_tri):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                self.bang.setItem(i, c, item)

    def tinh_tien(self):
        tong = sum(sp["thanh_tien"] for sp in self.ds)
        try:
            km = float(self.txt_khuyen_mai.text().strip().replace(",", ".") or 0)
        except ValueError:
            km = 0
        km = max(0, min(km, 100))
        thanh_tien = round(tong * (100 - km) / 100)
        self.txt_tong.setText(dinh_dang_tien(tong))
        self.txt_thanh_tien.setText(dinh_dang_tien(thanh_tien))

    # LƯU / LÀM MỚI
    def lam_moi(self):
        self.ds = []
        self.ve_bang()
        self.txt_khuyen_mai.clear()
        self.txt_khach.clear()
        self.spn_sl.setValue(1)
        self.date_ngay.setDate(QDate.currentDate())
        try:
            self.txt_ma_dh.setText(self.tao_ma_moi())
        except Exception:
            self.txt_ma_dh.setText("")
        self.tinh_tien()

    def tru_ton_kho(self, cur):
        """Tính nguyên liệu đã dùng cho cả đơn rồi TRỪ vào nguyen_lieu.SoLuongTon.
        Không đủ hàng -> ném TonKhoKhongDu (đơn sẽ bị hủy, không lưu gì cả)."""
        cur.execute("SELECT MaSP, MaNL, SoLuong FROM cong_thuc_san_pham")
        ct_sp = {}
        for ma_sp, ma_nl, sl in cur.fetchall():
            ct_sp.setdefault(ma_sp, []).append((ma_nl, Decimal(str(sl))))
        cur.execute("SELECT TenTP, MaNL, SoLuong FROM cong_thuc_topping")
        ct_tp = {}
        for ten_tp, ma_nl, sl in cur.fetchall():
            ct_tp.setdefault(ten_tp, []).append((ma_nl, Decimal(str(sl))))

        can = {}   # MaNL -> tổng lượng cần cho cả đơn
        for sp in self.ds:
            for ma_nl, sl in ct_sp.get(sp["ma_sp"], []) + ct_tp.get(sp["topping"], []):
                can[ma_nl] = can.get(ma_nl, Decimal(0)) + sl * sp["so_luong"]
        if not can:
            return

        # Khóa các dòng nguyên liệu lại để 2 đơn cùng lúc không trừ chồng nhau
        ds_ma = list(can)
        cur.execute(
            "SELECT MaNL, TenNL, DonViTinh, SoLuongTon FROM nguyen_lieu "
            "WHERE MaNL IN (%s) FOR UPDATE" % ",".join(["%s"] * len(ds_ma)),
            ds_ma
        )
        thieu = []
        for ma_nl, ten, dv, ton in cur.fetchall():
            if Decimal(str(ton)) < can[ma_nl]:
                thieu.append(
                    f"• {ten}: cần {dinh_dang_so(can[ma_nl])} {dv}, trong kho còn {dinh_dang_so(ton)} {dv}"
                )
        if thieu:
            raise TonKhoKhongDu(thieu)

        for ma_nl, luong in can.items():
            cur.execute(
                "UPDATE nguyen_lieu SET SoLuongTon = SoLuongTon - %s WHERE MaNL = %s",
                (luong, ma_nl)
            )

    def luu_don_hang(self):
        if not self.ds:
            QMessageBox.warning(self, "Chưa có sản phẩm", "Hãy thêm ít nhất 1 sản phẩm vào đơn.")
            return
        if self.cbo_nv.currentIndex() < 0:
            QMessageBox.warning(self, "Thiếu nhân viên", "Hãy chọn nhân viên lập đơn.")
            return

        tong = sum(sp["thanh_tien"] for sp in self.ds)
        try:
            km = float(self.txt_khuyen_mai.text().strip().replace(",", ".") or 0)
        except ValueError:
            QMessageBox.warning(self, "Khuyến mãi", "Khuyến mãi phải là số (% giảm).")
            return
        km = max(0, min(km, 100))
        thanh_tien = round(tong * (100 - km) / 100)

        # SĐT không bắt buộc: bỏ trống = khách vãng lai, không lưu thông tin khách
        sdt = self.txt_khach.text().strip()
        if sdt and not (sdt.isdigit() and len(sdt) == 10):
            QMessageBox.warning(
                self, "Số điện thoại",
                "Số điện thoại phải gồm đúng 10 chữ số.\nNếu khách không đọc số thì để trống ô này."
            )
            return

        conn = None
        try:
            ma_dh = self.tao_ma_moi()   # lấy lại lần nữa cho chắc không trùng
            conn = ket_noi()
            with conn.cursor() as cur:
                # Khách thân thiết: có SĐT -> tìm khách cũ, chưa có thì tạo mới
                ma_kh = None
                if sdt:
                    cur.execute("SELECT MaKH FROM khach_hang WHERE SoDienThoai = %s", (sdt,))
                    row = cur.fetchone()
                    if row:
                        ma_kh = row[0]
                    else:
                        cur.execute(
                            "SELECT MAX(CAST(SUBSTRING(MaKH, 3) AS UNSIGNED)) FROM khach_hang"
                        )
                        so = cur.fetchone()[0] or 0
                        ma_kh = f"KH{so + 1:03d}"
                        cur.execute(
                            "INSERT INTO khach_hang (MaKH, HoTen, SoDienThoai, DiemTichLuy) "
                            "VALUES (%s, %s, %s, 0)",
                            (ma_kh, f"Khách {sdt}", sdt)
                        )

                # Đảm bảo sản phẩm trong menu đã có ở bảng san_pham (để khóa ngoại không lỗi)
                cur.execute(
                    "INSERT IGNORE INTO san_pham (MaSP, TenSP, LoaiSP, GiaBan) "
                    "SELECT MaSP, TenSP, 'Đồ uống', Gia FROM menu_san_pham"
                )

                ngay_gio = (self.date_ngay.date().toString("yyyy-MM-dd")
                            + " " + datetime.now().strftime("%H:%M:%S"))
                cur.execute(
                    """INSERT INTO don_hang
                       (MaDH, NgayDat, MaKH, MaNV, PhuongThucThanhToan, TongTien, KhuyenMai, ThanhTien)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (ma_dh, ngay_gio, ma_kh, self.cbo_nv.currentData(),
                     self.cbo_pttt.currentText(), tong, tong - thanh_tien, thanh_tien)
                )
                for stt, sp in enumerate(self.ds, start=1):
                    cur.execute(
                        """INSERT INTO chi_tiet_don_hang
                           (MaDH, STT, MaSP, SoLuong, DonGia, KichCo, Topping)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (ma_dh, stt, sp["ma_sp"], sp["so_luong"], sp["don_gia"],
                         sp["kich_co"], sp["topping"])
                    )
                # Trừ nguyên liệu đã dùng khỏi tồn kho
                self.tru_ton_kho(cur)
            conn.commit()   # đến đây dữ liệu mới thật sự nằm trong MySQL
        except TonKhoKhongDu as e:
            if conn:
                conn.rollback()
            QMessageBox.warning(
                self, "Không đủ nguyên liệu",
                "Đơn này chưa lưu vì kho không đủ nguyên liệu:\n\n" + "\n".join(e.danh_sach)
                + "\n\nHãy nhập thêm nguyên liệu (màn hình Nguyên Liệu) hoặc giảm số lượng."
            )
            return
        except Exception as e:
            if conn:
                conn.rollback()
            if "cong_thuc" in str(e) and "doesn't exist" in str(e):
                QMessageBox.critical(
                    self, "Thiếu bảng công thức",
                    "Chưa có bảng công thức pha chế.\nHãy chạy file Them_cong_thuc.sql trong MySQL Workbench một lần rồi lưu lại."
                )
            else:
                QMessageBox.critical(self, "Lỗi lưu đơn hàng", str(e))
            return
        finally:
            if conn:
                conn.close()

        QMessageBox.information(self, "Thành công", f"Đã lưu đơn hàng {ma_dh}.")
        self.lam_moi()

    # ------------------------------------------------------------------
    def chinh_giao_dien(self):
        them_style(self, f"""
            QMainWindow, QWidget {{
                font-family: "Segoe UI";
                color: #49372B;
            }}
            QMainWindow {{ background-color: #F7F3ED; }}
            QLabel {{ color: #604936; font-size: {CO_CHU_THUONG}px; }}
            QLineEdit, QComboBox, QDateEdit, QSpinBox {{
                background-color: #FFFEFC;
                border: 1px solid #DFD2C3;
                border-radius: 7px;
                padding: 6px 9px;
                min-height: 28px;
                font-size: {CO_CHU_THUONG}px;
            }}
            QPushButton {{
                background-color: #F0E6D9;
                color: #604936;
                border: none;
                border-radius: 7px;
                padding: 8px 12px;
                min-height: 28px;
                font-size: {CO_CHU_THUONG}px;
            }}
            QPushButton:hover {{ background-color: #E4D3C0; }}
            QTableWidget {{ font-size: {CO_CHU_BANG}px; }}
        """)

        # Sidebar + tiêu đề dùng đúng style trong file .ui (giống trang Tìm kiếm đơn hàng)

    def mo_nhap_nguyen_lieu(self):
        from main import NhapNguyenLieuWindow
        self.cua_so = NhapNguyenLieuWindow()
        self.cua_so.setGeometry(self.geometry())
        self.cua_so.show()
        self.close()

    def mo_bao_cao(self):
        from bao_cao_ton_hang import BaoCaoTonHangWindow
        self.cua_so = BaoCaoTonHangWindow()
        self.cua_so.setGeometry(self.geometry())
        self.cua_so.show()
        self.close()

    def mo_tim_kiem(self):
        from tim_kiem_don_hang import TimKiemDonHangWindow
        self.cua_so = TimKiemDonHangWindow()
        self.cua_so.setGeometry(self.geometry())
        self.cua_so.show()
        self.close()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = LapDonHangWindow()
    window.show()
    sys.exit(app.exec_())