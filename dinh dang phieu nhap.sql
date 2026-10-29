
USE Cafe;

SET SQL_SAFE_UPDATES = 0;

DELETE FROM chi_tiet_phieu_nhap;
DELETE FROM phieu_nhap;
UPDATE nguyen_lieu SET SoLuongTon = 0;   

SET SQL_SAFE_UPDATES = 1;
ALTER TABLE phieu_nhap
    ADD CONSTRAINT chk_ma_phieu_nhap CHECK (MaPN REGEXP '^PN[0-9]{3,}$');

SELECT VERSION();
SELECT * FROM phieu_nhap;  