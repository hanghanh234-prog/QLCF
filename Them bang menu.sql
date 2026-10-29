-- File này chỉ TẠO BẢNG MỚI với tên riêng (menu_...), nên không đụng vào
-- bảng san_pham / topping bạn đã dùng cho chỗ khác.
USE Cafe;

CREATE TABLE IF NOT EXISTS menu_san_pham (
    MaSP  VARCHAR(10) PRIMARY KEY,
    TenSP VARCHAR(100) NOT NULL,
    Gia   INT NOT NULL            -- giá cơ bản (size nhỏ, chưa topping)
);

CREATE TABLE IF NOT EXISTS menu_kich_co (
    MaKC   VARCHAR(10) PRIMARY KEY,
    TenKC  VARCHAR(50) NOT NULL,
    PhuThu INT NOT NULL DEFAULT 0  -- tiền cộng thêm theo size
);

CREATE TABLE IF NOT EXISTS menu_topping (
    MaTP  VARCHAR(10) PRIMARY KEY,
    TenTP VARCHAR(100) NOT NULL,
    Gia   INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS don_hang (
    MaDH         VARCHAR(10) PRIMARY KEY,   -- DH001, DH002, ...
    NgayDat      DATE NOT NULL,
    SDTKhach     VARCHAR(20),
    MaNV         VARCHAR(10),
    TongTien     INT NOT NULL,
    KhuyenMai    DECIMAL(5,2) NOT NULL DEFAULT 0,  -- phần trăm giảm
    ThanhTien    INT NOT NULL,
    PTThanhToan  VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS chi_tiet_don_hang (
    Id        INT AUTO_INCREMENT PRIMARY KEY,
    MaDH      VARCHAR(10) NOT NULL,
    TenSP     VARCHAR(100) NOT NULL,
    KichCo    VARCHAR(50),
    Topping   VARCHAR(100),
    SoLuong   INT NOT NULL,
    DonGia    INT NOT NULL,
    ThanhTien INT NOT NULL,
    FOREIGN KEY (MaDH) REFERENCES don_hang(MaDH) ON DELETE CASCADE
);

INSERT INTO menu_san_pham (MaSP, TenSP, Gia) VALUES
('SP01', 'Cà phê đen',        20000),
('SP02', 'Cà phê sữa',        25000),
('SP03', 'Trà sữa trân châu', 35000),
('SP04', 'Trà đào cam sả',    30000),
('SP05', 'Matcha latte',      40000)
AS moi
ON DUPLICATE KEY UPDATE TenSP = moi.TenSP, Gia = moi.Gia;

INSERT INTO menu_kich_co (MaKC, TenKC, PhuThu) VALUES
('KC01', 'S', 0),
('KC02', 'M', 5000),
('KC03', 'L', 10000)
AS moi
ON DUPLICATE KEY UPDATE TenKC = moi.TenKC, PhuThu = moi.PhuThu;

INSERT INTO menu_topping (MaTP, TenTP, Gia) VALUES
('TP00', 'Không',               0),
('TP01', 'Trân châu đen',       5000),
('TP02', 'Trân châu hoàng kim', 7000),
('TP03', 'Thạch trái cây',      5000),
('TP04', 'Pudding trứng',       7000)
AS moi
ON DUPLICATE KEY UPDATE TenTP = moi.TenTP, Gia = moi.Gia;

SELECT * FROM menu_san_pham;
SELECT * FROM menu_kich_co;
SELECT * FROM menu_topping;