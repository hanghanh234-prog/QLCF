import sys
import os
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import (
    QMessageBox, QTableWidgetItem, QHBoxLayout, QWidget,
    QPushButton, QHeaderView
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
import pymysql

# ===================== CỠ CHỮ (px) =====================
CO_CHU_BANG = 12      # đơn vị pt, cỡ chữ TIÊU ĐỀ cột
CO_CHU_O = 10         # đơn vị pt, cỡ chữ các dòng dữ liệu (nhỏ hơn tiêu đề 1-2 cỡ)
CO_CHU_NUT = 12       # cỡ chữ 2 nút Tìm kiếm / Làm mới
CAO_DONG_BANG = 56
# ========================================================

# ============ TÊN WIDGET TRONG FILE .UI (objectName) ============
UI_FILE = "tim_kiem_don_hang.ui"        
W_MA_DON = "txtMaDonHang"         
W_TEN_KH = "txtTenKhachHang"      
W_NHAN_VIEN = "cboNhanVien"       
W_TRANG_THAI = "cboTrangThai"     
W_TU_NGAY = "dateTuNgay"          
W_DEN_NGAY = "dateDenNgay"        
W_BTN_TIM = "btnTimKiem"          
W_BTN_LAM_MOI = "btnLamMoi"       
W_BANG = "tableDonHang"          
# ================================================================

# ============ CẤU HÌNH QUERY SQL CHUẨN DÀNH CHO CSDL CAFE ============
SQL_TIM_KIEM = """
    SELECT p.MaPN AS MaDH, 
           p.NgayNhap, 
           ncc.TenNCC AS KhachHang, 
           nv.HoTen AS NhanVien,
           p.TongTien, 
           'Hoàn thành' AS TrangThai
    FROM phieu_nhap p
    LEFT JOIN nha_cung_cap ncc ON p.MaNCC = ncc.MaNCC
    LEFT JOIN nhan_vien nv ON p.MaNV = nv.MaNV
    WHERE 1 = 1
"""

SQL_CHI_TIET = """
    SELECT nl.TenNL AS TenSP, 
           ct.SoLuong, 
           ct.DonGiaNhap AS DonGia
    FROM chi_tiet_phieu_nhap ct
    JOIN nguyen_lieu nl ON ct.MaNL = nl.MaNL
    WHERE ct.MaPN = %s
"""
# =========================================================================

def them_style(widget, qss):
    cu = widget.styleSheet().strip()
    if cu and "{" not in cu:
        cu = "* { " + cu + " }"
    widget.setStyleSheet(cu + "\n" + qss)

def dinh_dang_tien(so):
    return f"{float(so or 0):,.0f}".replace(",", ".")

def dinh_dang_so(so):
    """5.000 -> 5, 2.500 -> 2.5 (bỏ số 0 thừa của DECIMAL(12,3))."""
    return f"{float(so or 0):.3f}".rstrip("0").rstrip(".")

class TimKiemDonHangWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(base_dir)  
        uic.loadUi(os.path.join(base_dir, UI_FILE), self)

        self.txt_ma = self.lay_widget(W_MA_DON)
        self.txt_ten_kh = self.lay_widget(W_TEN_KH)
        self.cb_nv = self.lay_widget(W_NHAN_VIEN)
        self.cb_tt = self.lay_widget(W_TRANG_THAI)
        self.date_tu = self.lay_widget(W_TU_NGAY)
        self.date_den = self.lay_widget(W_DEN_NGAY)
        self.btn_tim = self.lay_widget(W_BTN_TIM)
        self.btn_lam_moi = self.lay_widget(W_BTN_LAM_MOI)
        self.bang = self.lay_widget(W_BANG)

        self.cau_hinh_nut()
        self.cau_hinh_bang()

        self.date_tu.setCalendarPopup(True)
        self.date_den.setCalendarPopup(True)
        self.date_tu.setDisplayFormat("dd/MM/yyyy")
        self.date_den.setDisplayFormat("dd/MM/yyyy")

        self.btn_tim.clicked.connect(self.tim_kiem)
        self.btn_lam_moi.clicked.connect(self.lam_moi)

        self.txt_ma.returnPressed.connect(self.tim_kiem)
        self.txt_ten_kh.returnPressed.connect(self.tim_kiem)

        # Xử lý sự kiện chuyển về màn hình Nhập nguyên liệu qua menu bên trái
        for btn in self.findChildren(QPushButton):
            text = btn.text().strip().lower()
            if text in ("nguyên liệu", "nhập nguyên liệu"):
                btn.clicked.connect(self.mo_nhap_nguyen_lieu)
            elif text in ("đơn hàng", "lập đơn hàng"): 
                btn.clicked.connect(self.mo_lap_don_hang)
            elif text == "báo cáo":
                btn.clicked.connect(self.mo_bao_cao)

        self.load_combobox_data()
        self.dat_ngay_mac_dinh()
        self.tim_kiem()  

    def lay_widget(self, ten):
        w = self.findChild(QtWidgets.QWidget, ten)
        if w is None:
            raise RuntimeError(f"Không tìm thấy widget '{ten}' trong {UI_FILE}.")
        return w

    def connect_db(self):
        try:
            return pymysql.connect(
                host='localhost', port=3306, user='root', password='123456789',
                database='Cafe', charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
        except Exception as e:
            QMessageBox.critical(self, "Lỗi kết nối", f"Không thể kết nối CSDL:\n{e}")
            return None

    def cau_hinh_nut(self):
        """Sửa lỗi 2 nút bị cắt chữ (maximumWidth trong .ui nhỏ hơn minimumWidth)."""
        for b in (self.btn_tim, self.btn_lam_moi):
            b.setMaximumWidth(16777215)
            b.setMinimumSize(150, 44)
            f = b.font()
            f.setPointSize(CO_CHU_NUT)
            f.setBold(True)
            b.setFont(f)

    def cau_hinh_bang(self):
        self.bang.setColumnCount(7)
        self.bang.setHorizontalHeaderLabels([
            "Mã đơn", "Ngày lập", "Khách hàng/NCC", "Nhân viên",
            "Tổng tiền", "Trạng thái", "Thao tác"
        ])
        self.bang.verticalHeader().setVisible(False)
        self.bang.setAlternatingRowColors(True)
        self.bang.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.bang.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.bang.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.bang.setWordWrap(False)

        them_style(self.bang, f"""
            QTableWidget {{ font-size: {CO_CHU_O}pt; }}
            QHeaderView::section {{ font-size: {CO_CHU_BANG}pt; }}
            QTableWidget::item {{ padding: 5px; font-size: {CO_CHU_O}pt; }}
        """)
        font_bang = QFont(self.bang.font())
        font_bang.setPointSize(CO_CHU_O)
        self.bang.setFont(font_bang)
        font_dau = QFont(font_bang)
        font_dau.setPointSize(CO_CHU_BANG)
        font_dau.setBold(True)
        self.bang.horizontalHeader().setFont(font_dau)

        h = self.bang.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        h.setSectionResizeMode(3, QHeaderView.Stretch)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.Fixed)
        h.resizeSection(6, 170)

    def load_combobox_data(self):
        conn = self.connect_db()
        if not conn: return
        try:
            with conn.cursor() as cur:
                self.cb_nv.clear()
                self.cb_nv.addItem("Tất cả", None)
                cur.execute("SELECT MaNV, HoTen FROM nhan_vien")
                for nv in cur.fetchall():
                    self.cb_nv.addItem(nv['HoTen'], nv['MaNV'])
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi tải danh mục:\n{e}")
        finally:
            conn.close()

    def dat_ngay_mac_dinh(self):
        self.date_tu.setDate(QDate(2000, 1, 1))
        self.date_den.setDate(QDate.currentDate())

    def tim_kiem(self):
        tu = self.date_tu.date()
        den = self.date_den.date()
        if tu > den:
            QMessageBox.warning(self, "Cảnh báo", "'Từ ngày' không được lớn hơn 'Đến ngày'!")
            return

        sql = SQL_TIM_KIEM
        params = []

        ma = self.txt_ma.text().strip()
        if ma:
            sql += " AND p.MaPN LIKE %s"
            params.append(f"%{ma}%")

        ten = self.txt_ten_kh.text().strip()
        if ten:
            sql += " AND ncc.TenNCC LIKE %s"
            params.append(f"%{ten}%")

        ma_nv = self.cb_nv.currentData()
        if ma_nv is not None:
            sql += " AND p.MaNV = %s"
            params.append(ma_nv)

        sql += " AND DATE(p.NgayNhap) BETWEEN %s AND %s"
        params += [tu.toString("yyyy-MM-dd"), den.toString("yyyy-MM-dd")]
        sql += " ORDER BY p.NgayNhap DESC, p.MaPN DESC"

        conn = self.connect_db()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                self.do_du_lieu(cur.fetchall())
        except Exception as e:
            QMessageBox.critical(self, "Lỗi Database", f"Lỗi khi tìm kiếm:\n{e}")
        finally:
            conn.close()

    def do_du_lieu(self, rows):
        self.bang.setRowCount(0)
        font_o = QFont(self.bang.font())
        font_o.setPointSize(CO_CHU_O)
        for r, d in enumerate(rows):
            self.bang.insertRow(r)
            self.bang.setRowHeight(r, CAO_DONG_BANG)

            ngay = d['NgayNhap']
            ngay_str = ngay.strftime("%d/%m/%Y") if hasattr(ngay, "strftime") else str(ngay or "")

            gia_tri = [
                str(d['MaDH']), ngay_str, d['KhachHang'] or "",
                d['NhanVien'] or "", dinh_dang_tien(d['TongTien']),
                str(d['TrangThai'] or "")
            ]

            for c, text in enumerate(gia_tri):
                item = QTableWidgetItem(text)
                item.setFont(font_o)
                if c == 4: item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                elif c in (0, 1, 5): item.setTextAlignment(Qt.AlignCenter)
                else: item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.bang.setItem(r, c, item)

            khung = QWidget()
            lay = QHBoxLayout(khung)
            lay.setContentsMargins(4, 4, 4, 4)
            btn = QPushButton("Xem chi tiết")
            btn.setStyleSheet(f"""
                QPushButton {{ 
                    background-color: #EADBC9; color: #604936;
                    border: none; border-radius: 6px; padding: 6px 10px;
                    font-size: {CO_CHU_O}pt; 
                }}
                QPushButton:hover {{ background-color: #DCC4AA; }}
            """)
            ma_dh = d['MaDH']
            btn.clicked.connect(lambda _, m=ma_dh: self.xem_chi_tiet(m))
            lay.addWidget(btn)
            self.bang.setCellWidget(r, 6, khung)

    def xem_chi_tiet(self, ma_dh):
        conn = self.connect_db()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute(SQL_CHI_TIET, (ma_dh,))
                ds = cur.fetchall()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi Database", f"Lỗi lấy chi tiết:\n{e}")
            return
        finally:
            conn.close()

        if not ds:
            QMessageBox.information(self, f"Mã phiếu {ma_dh}", "Không có thông tin chi tiết.")
            return

        dong = []
        tong = 0
        for x in ds:
            tt = float(x['SoLuong']) * float(x['DonGia'])
            tong += tt
            dong.append(f"• {x['TenSP']}   x{dinh_dang_so(x['SoLuong'])}  =  {dinh_dang_tien(tt)} VNĐ")

        dong.append("")
        dong.append(f"Tổng cộng: {dinh_dang_tien(tong)} VNĐ")
        QMessageBox.information(self, f"Chi tiết phiếu {ma_dh}", "\n".join(dong))

    def mo_nhap_nguyen_lieu(self):
        from main import NhapNguyenLieuWindow
        self.cua_so = NhapNguyenLieuWindow()
        self.cua_so.show()
        self.close()

    def mo_lap_don_hang(self):
        """Mở màn hình Lập đơn hàng và đồng bộ kích thước cửa sổ."""
        from lap_don_hang import LapDonHangWindow
        self.cua_so = LapDonHangWindow()
        self.cua_so.setGeometry(self.geometry())
        self.cua_so.show()
        self.close()

    def mo_bao_cao(self):
        from bao_cao_ton_hang import BaoCaoTonHangWindow
        self.cua_so = BaoCaoTonHangWindow()
        self.cua_so.setGeometry(self.geometry())
        self.cua_so.show()
        self.close()

    def lam_moi(self):
        self.txt_ma.clear()
        self.txt_ten_kh.clear()
        self.cb_nv.setCurrentIndex(0)
        self.cb_tt.setCurrentIndex(0)
        self.dat_ngay_mac_dinh()
        self.tim_kiem()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = TimKiemDonHangWindow()
    window.show()
    sys.exit(app.exec_())