-- Migration: Add delivery and payment method fields to orders table
-- Date: 2025-01-XX
-- Description: Adds delivery_type_id, payment_method_id, and delivery_address columns to comenzi table

-- Add new columns to comenzi table
ALTER TABLE `comenzi` 
ADD COLUMN `delivery_type_id` TINYINT NULL,
ADD COLUMN `payment_method_id` INT NULL,
ADD COLUMN `delivery_address` VARCHAR(150) NULL;

-- Add indexes for performance
ALTER TABLE `comenzi` 
ADD INDEX `idx_comenzi_delivery_type` (`delivery_type_id`),
ADD INDEX `idx_comenzi_payment_method` (`payment_method_id`),
ADD INDEX `idx_comenzi_delivery_address` (`delivery_address`);

-- Add foreign key constraints
ALTER TABLE `comenzi` 
ADD CONSTRAINT `fk_comenzi_delivery_type` 
    FOREIGN KEY (`delivery_type_id`) REFERENCES `tipuri_livrare` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
ADD CONSTRAINT `fk_comenzi_payment_method` 
    FOREIGN KEY (`payment_method_id`) REFERENCES `modalitati_de_plata` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE;

-- Verify the changes
-- SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT 
-- FROM INFORMATION_SCHEMA.COLUMNS 
-- WHERE TABLE_SCHEMA = 'online_shop' AND TABLE_NAME = 'comenzi' 
-- ORDER BY ORDINAL_POSITION;
