-- Công thức pha chế: mỗi ly dùng bao nhiêu nguyên liệu -> dùng để TRỪ tồn kho khi lập đơn.
-- Chạy file này 1 lần trong Workbench (chạy lại cũng không sao, không bị trùng).
-- Đơn vị lấy theo bảng nguyen_lieu: kg / lít / gói / lon.
-- Số lượng bên dưới là con số ví dụ, bạn sửa lại cho đúng thực tế của quán.
USE Cafe;

CREATE TABLE IF NOT EXISTS cong_thuc_san_pham (
    MaSP    VARCHAR(10)   NOT NULL,
    MaNL    VARCHAR(10)   NOT NULL,
    SoLuong DECIMAL(12,3) NOT NULL,            -- lượng nguyên liệu dùng cho 1 ly
    PRIMARY KEY (MaSP, MaNL),
    CONSTRAINT chk_ctsp_so_luong CHECK (SoLuong > 0),
    CONSTRAINT fk_ctsp_nguyen_lieu FOREIGN KEY (MaNL)
        REFERENCES nguyen_lieu(MaNL) ON UPDATE CASCADE
) ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS cong_thuc_topping (
    TenTP   VARCHAR(100)  NOT NULL,            -- trùng với menu_topping.TenTP
    MaNL    VARCHAR(10)   NOT NULL,
    SoLuong DECIMAL(12,3) NOT NULL,            -- lượng nguyên liệu dùng cho 1 phần topping
    PRIMARY KEY (TenTP, MaNL),
    CONSTRAINT chk_cttp_so_luong CHECK (SoLuong > 0),
    CONSTRAINT fk_cttp_nguyen_lieu FOREIGN KEY (MaNL)
        REFERENCES nguyen_lieu(MaNL) ON UPDATE CASCADE
) ENGINE = InnoDB;

INSERT INTO cong_thuc_san_pham (MaSP, MaNL, SoLuong) VALUES
('SP01', 'NL01', 0.020),   -- Cà phê đen: cà phê hạt
('SP01', 'NL03', 0.010),   --             đường
('SP02', 'NL01', 0.020),   -- Cà phê sữa: cà phê hạt
('SP02', 'NL08', 0.050),   --              sữa đặc (lon)
('SP02', 'NL03', 0.005),   --              đường
('SP03', 'NL04', 0.010),   -- Trà sữa trân châu: trà đen
('SP03', 'NL07', 0.030),   --                    bột sữa béo
('SP03', 'NL03', 0.010),   --                    đường
('SP03', 'NL05', 0.100),   --                    trân châu đen (gói)
('SP04', 'NL04', 0.010),   -- Trà đào cam sả: trà đen
('SP04', 'NL03', 0.020),   --                  đường
('SP05', 'NL02', 0.150),   -- Matcha latte: sữa tươi (lít)
('SP05', 'NL07', 0.020),   --               bột sữa béo
('SP05', 'NL03', 0.010)    --               đường
AS moi
ON DUPLICATE KEY UPDATE SoLuong = moi.SoLuong;

INSERT INTO cong_thuc_topping (TenTP, MaNL, SoLuong) VALUES
('Trân châu đen',       'NL05', 0.100),
('Trân châu hoàng kim', 'NL06', 0.100),
('Thạch trái cây',      'NL09', 0.100),
('Pudding trứng',       'NL10', 0.100)
AS moi
ON DUPLICATE KEY UPDATE SoLuong = moi.SoLuong;

SELECT * FROM cong_thuc_san_pham;
SELECT * FROM cong_thuc_topping;