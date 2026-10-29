
USE Cafe;

INSERT INTO nha_cung_cap (MaNCC, TenNCC, SoDienThoai, DiaChi, Email) VALUES
('NCC01', 'Công ty TNHH Cà phê Visty', '0243883399', 'Ba Đình, Hà Nội', 'contact@visty.vn'),
('NCC02', 'Công ty Cổ phần Cà phê Trung Nguyên Legend', '0243934335', 'Cầu Giấy, Hà Nội', 'contact@trungnguyen.vn'),
('NCC03', 'Công ty TNHH Đồ uống Việt', '0243232121', 'Thanh Xuân, Hà Nội', 'contact@douongviet.vn'),
('NCC04', 'Công ty TNHH Toàn Global', '0243232132', 'Cầu Giấy, Hà Nội', 'contact@toanglobal.vn'),
('NCC05', 'Baker''s Mart Nhất Hương', '0246287385', 'Hà Đông, Hà Nội', 'contact@nhathuong.vn')
ON DUPLICATE KEY UPDATE
    TenNCC      = VALUES(TenNCC),
    SoDienThoai = VALUES(SoDienThoai),
    DiaChi      = VALUES(DiaChi),
    Email       = VALUES(Email);


INSERT INTO nhan_vien (MaNV, HoTen, GioiTinh, NgaySinh, SoDienThoai, DiaChi, ChucVu, Luong) VALUES
('NV01', 'Trần Hải Ly',           'Nữ', '2004-05-12', '0901234567', 'Hà Nội', 'Nhân viên kho', 7000000),
('NV02', 'Nguyễn Thị Quỳnh Nga',  'Nữ', '2005-08-20', '0907654321', 'Hà Nội', 'Thu ngân',      6500000),
('NV03', 'Hoàng Thị Minh Ngọc',   'Nữ', '2003-11-02', '0912345678', 'Hà Nội', 'Pha chế',       7500000),
('NV04', 'Đỗ Thị Phương Thúy',    'Nữ', '2004-02-18', '0933456789', 'Hà Nội', 'Phục vụ',       6000000),
('NV05', 'Nguyễn Quỳnh Trang',    'Nữ', '2006-03-02', '0972874726', 'Hà Nội', 'Pha chế',       7500000)
AS moi
ON DUPLICATE KEY UPDATE
    HoTen       = moi.HoTen,
    GioiTinh    = moi.GioiTinh,
    NgaySinh    = moi.NgaySinh,
    SoDienThoai = moi.SoDienThoai,
    DiaChi      = moi.DiaChi,
    ChucVu      = moi.ChucVu,
    Luong       = moi.Luong;

INSERT INTO nguyen_lieu (MaNL, TenNL, DonViTinh, SoLuongTon, DonGia) VALUES
('NL01', 'Cà phê hạt',          'kg',  0, 120000),
('NL02', 'Sữa tươi',            'lít', 0, 35000),
('NL03', 'Đường',               'kg',  0, 22000),
('NL04', 'Trà đen',             'kg',  0, 150000),
('NL05', 'Trân châu đen',       'gói', 0, 45000),
('NL06', 'Trân châu hoàng kim', 'gói', 0, 50000),
('NL07', 'Bột sữa béo',         'kg',  0, 65000),
('NL08', 'Sữa đặc',             'lon', 0, 28000),
('NL09', 'Thạch trái cây',      'gói', 0, 40000),
('NL10', 'Pudding trứng',       'gói', 0, 55000)
AS moi
ON DUPLICATE KEY UPDATE
    TenNL     = moi.TenNL,
    DonViTinh = moi.DonViTinh,
    DonGia    = moi.DonGia;

SELECT * FROM nha_cung_cap;
SELECT * FROM nhan_vien;
SELECT * FROM nguyen_lieu;



