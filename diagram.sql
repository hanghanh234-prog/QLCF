
CREATE DATABASE IF NOT EXISTS Cafe
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE Cafe;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS chi_tiet_don_hang;
DROP TABLE IF EXISTS chi_tiet_phieu_nhap;
DROP TABLE IF EXISTS san_pham_kich_co;
DROP TABLE IF EXISTS san_pham_topping;
DROP TABLE IF EXISTS phan_cong;
DROP TABLE IF EXISTS don_hang;
DROP TABLE IF EXISTS phieu_nhap;
DROP TABLE IF EXISTS nguyen_lieu;
DROP TABLE IF EXISTS san_pham;
DROP TABLE IF EXISTS khach_hang;
DROP TABLE IF EXISTS nha_cung_cap;
DROP TABLE IF EXISTS nhan_vien;

SET FOREIGN_KEY_CHECKS = 1;
CREATE TABLE nhan_vien (
    MaNV VARCHAR(10) PRIMARY KEY,
    HoTen VARCHAR(100) NOT NULL,
    GioiTinh VARCHAR(10),
    NgaySinh DATE,
    SoDienThoai VARCHAR(15),
    DiaChi VARCHAR(255),
    ChucVu VARCHAR(50) NOT NULL,
    Luong DECIMAL(12,2) NOT NULL DEFAULT 0,

    CONSTRAINT chk_nhan_vien_luong
        CHECK (Luong >= 0)
) ENGINE = InnoDB;

CREATE TABLE khach_hang (
    MaKH VARCHAR(10) PRIMARY KEY,
    HoTen VARCHAR(100) NOT NULL DEFAULT 0,
    SoDienThoai VARCHAR(10),
    NgaySinh DATE,
    DiemTichLuy INT NOT NULL DEFAULT 0,

    CONSTRAINT chk_khach_hang_diem
        CHECK (DiemTichLuy >= 0),

    CONSTRAINT uq_khach_hang_sdt
        UNIQUE (SoDienThoai)
) ENGINE = InnoDB;


CREATE TABLE nha_cung_cap (
    MaNCC VARCHAR(10) PRIMARY KEY,
    TenNCC VARCHAR(100) NOT NULL,
    SoDienThoai VARCHAR(10),
    DiaChi VARCHAR(255) NOT NULL,
    Email VARCHAR(100) NOT NULL
) ENGINE = InnoDB;

CREATE TABLE san_pham (
    MaSP VARCHAR(10) PRIMARY KEY,
    TenSP VARCHAR(100) NOT NULL,
    LoaiSP VARCHAR(50) NOT NULL,
    GiaBan DECIMAL(12,2) NOT NULL,
    SoLuongTon INT NOT NULL DEFAULT 0,
    MoTa VARCHAR(255),
    TrangThai VARCHAR(20) NOT NULL DEFAULT 'Dang ban',

    CONSTRAINT chk_san_pham_gia
        CHECK (GiaBan >= 0),

    CONSTRAINT chk_san_pham_ton
        CHECK (SoLuongTon >= 0)
) ENGINE = InnoDB;

CREATE TABLE nguyen_lieu (
    MaNL VARCHAR(10) PRIMARY KEY,
    TenNL VARCHAR(100) NOT NULL,
    DonViTinh VARCHAR(20) NOT NULL,
    SoLuongTon DECIMAL(12,3) NOT NULL DEFAULT 0,
    DonGia DECIMAL(12,2) NOT NULL DEFAULT 0,

    CONSTRAINT chk_nguyen_lieu_ton
        CHECK (SoLuongTon >= 0),

    CONSTRAINT chk_nguyen_lieu_gia
        CHECK (DonGia >= 0)
) ENGINE = InnoDB;

CREATE TABLE san_pham_kich_co (
    MaSP VARCHAR(10) NOT NULL,
    KichCo VARCHAR(10) NOT NULL,
    PhuThu DECIMAL(12,2) NOT NULL DEFAULT 0,

    PRIMARY KEY (MaSP, KichCo),

    CONSTRAINT chk_kich_co_phu_thu
        CHECK (PhuThu >= 0),

    CONSTRAINT fk_kich_co_san_pham
        FOREIGN KEY (MaSP)
        REFERENCES san_pham(MaSP)
        ON UPDATE CASCADE
        ON DELETE CASCADE
) ENGINE = InnoDB;

CREATE TABLE san_pham_topping (
    MaSP VARCHAR(10) NOT NULL,
    Topping VARCHAR(100) NOT NULL,
    GiaTopping DECIMAL(12,2) NOT NULL DEFAULT 0,

    PRIMARY KEY (MaSP, Topping),

    CONSTRAINT chk_topping_gia
        CHECK (GiaTopping >= 0),

    CONSTRAINT fk_topping_san_pham
        FOREIGN KEY (MaSP)
        REFERENCES san_pham(MaSP)
        ON UPDATE CASCADE
        ON DELETE CASCADE
) ENGINE = InnoDB;

CREATE TABLE phan_cong (
    MaNV VARCHAR(10) NOT NULL,
    NgayLam DATE NOT NULL,
    CaLam VARCHAR(20) NOT NULL,
    GhiChu VARCHAR(255),

    PRIMARY KEY (MaNV, NgayLam, CaLam),

    CONSTRAINT fk_phan_cong_nhan_vien
        FOREIGN KEY (MaNV)
        REFERENCES nhan_vien(MaNV)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE = InnoDB;

CREATE TABLE don_hang (
    MaDH VARCHAR(10) PRIMARY KEY,
    NgayDat DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    MaKH VARCHAR(10) NULL,
    MaNV VARCHAR(10) NOT NULL,
    PhuongThucThanhToan VARCHAR(30),
    TongTien DECIMAL(12,2) NOT NULL DEFAULT 0,
    KhuyenMai DECIMAL(12,2) NOT NULL DEFAULT 0,
    ThanhTien DECIMAL(12,2) NOT NULL DEFAULT 0,
    TrangThai VARCHAR(30) NOT NULL DEFAULT 'Hoan thanh',

    CONSTRAINT chk_don_hang_tong_tien
        CHECK (TongTien >= 0),

    CONSTRAINT chk_don_hang_khuyen_mai
        CHECK (KhuyenMai >= 0),

    CONSTRAINT chk_don_hang_thanh_tien
        CHECK (ThanhTien >= 0),

    CONSTRAINT fk_don_hang_khach_hang
        FOREIGN KEY (MaKH)
        REFERENCES khach_hang(MaKH)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_don_hang_nhan_vien
        FOREIGN KEY (MaNV)
        REFERENCES nhan_vien(MaNV)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE = InnoDB;

CREATE TABLE phieu_nhap (
    MaPN VARCHAR(10) PRIMARY KEY,
    NgayNhap DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    MaNCC VARCHAR(10) NOT NULL,
    MaNV VARCHAR(10) NOT NULL,
    TongTien DECIMAL(12,2) NOT NULL DEFAULT 0,
    GhiChu VARCHAR(255),

    CONSTRAINT chk_phieu_nhap_tong_tien
        CHECK (TongTien >= 0),

    CONSTRAINT fk_phieu_nhap_nha_cung_cap
        FOREIGN KEY (MaNCC)
        REFERENCES nha_cung_cap(MaNCC)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_phieu_nhap_nhan_vien
        FOREIGN KEY (MaNV)
        REFERENCES nhan_vien(MaNV)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE = InnoDB;

CREATE TABLE chi_tiet_don_hang (
    MaDH VARCHAR(10) NOT NULL,
    STT INT NOT NULL,
    MaSP VARCHAR(10) NOT NULL,
    SoLuong INT NOT NULL,
    DonGia DECIMAL(12,2) NOT NULL,
    KichCo VARCHAR(10),
    Topping VARCHAR(100),

    PRIMARY KEY (MaDH, STT),

    CONSTRAINT chk_ctdh_so_luong
        CHECK (SoLuong > 0),

    CONSTRAINT chk_ctdh_don_gia
        CHECK (DonGia >= 0),

    CONSTRAINT fk_ctdh_don_hang
        FOREIGN KEY (MaDH)
        REFERENCES don_hang(MaDH)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_ctdh_san_pham
        FOREIGN KEY (MaSP)
        REFERENCES san_pham(MaSP)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE = InnoDB;

CREATE TABLE chi_tiet_phieu_nhap (
    MaPN VARCHAR(10) NOT NULL,
    MaNL VARCHAR(10) NOT NULL,
    SoLuong DECIMAL(12,3) NOT NULL,
    DonGiaNhap DECIMAL(12,2) NOT NULL,

    PRIMARY KEY (MaPN, MaNL),

    CONSTRAINT chk_ctpn_so_luong
        CHECK (SoLuong > 0),

    CONSTRAINT chk_ctpn_don_gia
        CHECK (DonGiaNhap >= 0),

    CONSTRAINT fk_ctpn_phieu_nhap
        FOREIGN KEY (MaPN)
        REFERENCES phieu_nhap(MaPN)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_ctpn_nguyen_lieu
        FOREIGN KEY (MaNL)
        REFERENCES nguyen_lieu(MaNL)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE = InnoDB;

SHOW TABLES;

SHOW CREATE TABLE don_hang;

SELECT
    TABLE_NAME,
    COLUMN_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = DATABASE()
  AND REFERENCED_TABLE_NAME IS NOT NULL
ORDER BY TABLE_NAME;
