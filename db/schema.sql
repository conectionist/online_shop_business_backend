-- DO NOT MODIFY THIS FILE!!!
-- IF WANT TO MAKE CHANGES, CREATE AN ALEMBIC MIGRATION FILE IN MIGRATIONS FOLDER

-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

-- -----------------------------------------------------
-- Schema online_shop
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema online_shop
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `online_shop` DEFAULT CHARACTER SET utf8mb4 ;
USE `online_shop` ;

-- -----------------------------------------------------
-- Table `online_shop`.`category`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `online_shop`.`category` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(45) NOT NULL,
  `image_path` VARCHAR(256) NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_deleted` TINYINT NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `name_UNIQUE` (`name` ASC),
  INDEX `idx_category_is_deleted` (`is_deleted` ASC))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `online_shop`.`unitati`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `online_shop`.`unitati` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `denumire` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC),
  UNIQUE INDEX `denumire_UNIQUE` (`denumire` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `online_shop`.`produse`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `online_shop`.`produse` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nume` VARCHAR(100) NOT NULL,
  `cantitate` SMALLINT NOT NULL,
  `pret` SMALLINT NOT NULL,
  `description` VARCHAR(1500) NULL DEFAULT NULL,
  `category_id` INT NOT NULL,
  `unitati_id` INT NOT NULL,
  -- `stock` field removed - stock is now managed at list-product level
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_deleted` TINYINT NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC),
  UNIQUE INDEX `nume_UNIQUE` (`nume` ASC),
  INDEX `fk_produse_category1_idx` (`category_id` ASC),
  INDEX `fk_produse_unitati1_idx` (`unitati_id` ASC),
  INDEX `idx_produse_is_deleted` (`is_deleted` ASC),
  CONSTRAINT `fk_produse_category1`
    FOREIGN KEY (`category_id`)
    REFERENCES `online_shop`.`category` (`id`),
  CONSTRAINT `fk_produse_unitati1`
    FOREIGN KEY (`unitati_id`)
    REFERENCES `online_shop`.`unitati` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `online_shop`.`secondary_images`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `online_shop`.`secondary_images` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `path` VARCHAR(256) NOT NULL,
  `produse_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC),
  UNIQUE INDEX `path_UNIQUE` (`path` ASC),
  INDEX `fk_images_produse1_idx` (`produse_id` ASC),
  CONSTRAINT `fk_images_produse1`
    FOREIGN KEY (`produse_id`)
    REFERENCES `online_shop`.`produse` (`id`)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `online_shop`.`product_images`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `online_shop`.`product_images` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `path` VARCHAR(256) NOT NULL,
  `produse_id` INT NOT NULL,
  `position` SMALLINT NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC),
  UNIQUE INDEX `path_UNIQUE` (`path` ASC),
  INDEX `idx_product_images_position` (`position` ASC),
  INDEX `fk_product_images_produse1_idx` (`produse_id` ASC),
  CONSTRAINT `fk_product_images_produse1`
    FOREIGN KEY (`produse_id`)
    REFERENCES `online_shop`.`produse` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `online_shop`.`orare_livrari`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `online_shop`.`orare_livrari` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `orar_livrari` VARCHAR(1000) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4;


-- -----------------------------------------------------
-- Table `online_shop`.`liste`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `online_shop`.`liste` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `data` DATE NOT NULL,
  `is_current` TINYINT NOT NULL,
  `is_published` TINYINT NULL DEFAULT NULL,
  `mesaj_introducere` VARCHAR(100) NULL,
  `alte_detalii` VARCHAR(500) NULL,
  `numar_whatsapp` VARCHAR(15) NULL,
  `orare_livrari_id` INT NOT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_deleted` TINYINT NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC),
  INDEX `idx_liste_data` (`data` ASC),
  INDEX `idx_liste_is_deleted` (`is_deleted` ASC),
  INDEX `fk_liste_orare_livrari1_idx` (`orare_livrari_id` ASC),
  CONSTRAINT `fk_liste_orare_livrari1`
    FOREIGN KEY (`orare_livrari_id`)
    REFERENCES `online_shop`.`orare_livrari` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
AUTO_INCREMENT = 5
DEFAULT CHARACTER SET = utf8mb4;


-- -----------------------------------------------------
-- Table `online_shop`.`modalitati_de_plata`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `online_shop`.`modalitati_de_plata` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(20) NOT NULL,
  `description` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC),
  UNIQUE INDEX `name_UNIQUE` (`name` ASC))
ENGINE = InnoDB
AUTO_INCREMENT = 5
DEFAULT CHARACTER SET = utf8mb4;


-- -----------------------------------------------------
-- Table `online_shop`.`tipuri_livrare`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `online_shop`.`tipuri_livrare` (
  `id` TINYINT NOT NULL AUTO_INCREMENT,
  `denumire` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC),
  UNIQUE INDEX `denumire_UNIQUE` (`denumire` ASC))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4;


-- -----------------------------------------------------
-- Table `online_shop`.`product_overrides`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `online_shop`.`product_overrides` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `produse_id` INT NOT NULL,
  `field_name` ENUM('price', 'description', 'availability') NOT NULL,
  `old_value` TEXT NULL,
  `new_value` TEXT NOT NULL,
  `notes` VARCHAR(500) NULL,
  `is_active` BOOLEAN DEFAULT TRUE,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC),
  INDEX `idx_product_active_override` (`produse_id`, `field_name`, `is_active`),
  INDEX `fk_product_overrides_produse1_idx` (`produse_id` ASC),
  CONSTRAINT `fk_product_overrides_produse1`
    FOREIGN KEY (`produse_id`)
    REFERENCES `online_shop`.`produse` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `online_shop`.`comenzi`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `online_shop`.`comenzi` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nume_client` VARCHAR(50) NOT NULL,
  `data_plasarii` DATETIME NOT NULL,
  `liste_id` INT NOT NULL,
  `order_notes` VARCHAR(500) NULL DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC),
  INDEX `fk_comenzi_liste1_idx` (`liste_id` ASC),
  INDEX `idx_comenzi_data_plasarii` (`data_plasarii` ASC),
  INDEX `idx_comenzi_nume_client` (`nume_client` ASC),
  CONSTRAINT `fk_comenzi_liste1`
    FOREIGN KEY (`liste_id`)
    REFERENCES `online_shop`.`liste` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `online_shop`.`comenzi_au_produse`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `online_shop`.`comenzi_au_produse` (
  `comenzi_id` INT NOT NULL,
  `produse_id` INT NOT NULL,
  `pret_produs` SMALLINT NOT NULL,
  `cantitate_produs` SMALLINT NOT NULL,
  `unitati_id` INT NOT NULL,
  PRIMARY KEY (`comenzi_id`, `produse_id`),
  INDEX `fk_comenzi_has_produse_produse1_idx` (`produse_id` ASC),
  INDEX `fk_comenzi_has_produse_comenzi1_idx` (`comenzi_id` ASC),
  INDEX `fk_comenzi_has_produse_unitati1_idx` (`unitati_id` ASC),
  CONSTRAINT `fk_comenzi_has_produse_comenzi1`
    FOREIGN KEY (`comenzi_id`)
    REFERENCES `online_shop`.`comenzi` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_comenzi_has_produse_produse1`
    FOREIGN KEY (`produse_id`)
    REFERENCES `online_shop`.`produse` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_comenzi_has_produse_unitati1`
    FOREIGN KEY (`unitati_id`)
    REFERENCES `online_shop`.`unitati` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `online_shop`.`business_details`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `online_shop`.`business_details` (
  `id` TINYINT NOT NULL AUTO_INCREMENT,
  `adresa` VARCHAR(200) NULL,
  `telefon` VARCHAR(20) NULL,
  `logo_path` VARCHAR(256) NULL,
  `motto` VARCHAR(256) NULL,
  `list_not_available_msg` VARCHAR(200) NULL,
  `alte_detalii` VARCHAR(500) NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `online_shop`.`admins`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `online_shop`.`admins` (
  `id` TINYINT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(50) NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC),
  UNIQUE INDEX `username_UNIQUE` (`username` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `online_shop`.`liste_au_tipuri_livrare`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `online_shop`.`liste_au_tipuri_livrare` (
  `liste_id` INT NOT NULL,
  `tipuri_livrare_id` TINYINT NOT NULL,
  PRIMARY KEY (`liste_id`, `tipuri_livrare_id`),
  INDEX `fk_liste_has_tipuri_livrare_tipuri_livrare1_idx` (`tipuri_livrare_id` ASC),
  INDEX `fk_liste_has_tipuri_livrare_liste1_idx` (`liste_id` ASC),
  CONSTRAINT `fk_liste_has_tipuri_livrare_liste1`
    FOREIGN KEY (`liste_id`)
    REFERENCES `online_shop`.`liste` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_liste_has_tipuri_livrare_tipuri_livrare1`
    FOREIGN KEY (`tipuri_livrare_id`)
    REFERENCES `online_shop`.`tipuri_livrare` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4;


-- -----------------------------------------------------
-- Table `online_shop`.`liste_au_categorii` (List-Category ordering)
-- This table manages the order of categories within each list.
-- Each list can have categories in a specific admin-defined order.
-- The position field determines the display order (0 = first, 1 = second, etc.)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `online_shop`.`liste_au_categorii` (
  `liste_id` INT NOT NULL,
  `category_id` INT NOT NULL,
  `position` INT NOT NULL,
  PRIMARY KEY (`liste_id`, `category_id`),
  INDEX `idx_liste_categorii_position` (`liste_id`, `position` ASC),
  INDEX `fk_liste_au_categorii_liste1_idx` (`liste_id` ASC),
  INDEX `fk_liste_au_categorii_category1_idx` (`category_id` ASC),
  CONSTRAINT `fk_liste_au_categorii_liste1`
    FOREIGN KEY (`liste_id`)
    REFERENCES `online_shop`.`liste` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_liste_au_categorii_category1`
    FOREIGN KEY (`category_id`)
    REFERENCES `online_shop`.`category` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4;


-- -----------------------------------------------------
-- Table `online_shop`.`liste_au_produse_ordered` (List-Product ordering within categories)
-- This table manages the order of products within each category for each list.
-- Each product in a list belongs to a specific category and has a position within that category.
-- The position field determines the display order within the category (0 = first, 1 = second, etc.)
-- The stoc_produs field stores the stock quantity for this product in this specific list.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `online_shop`.`liste_au_produse_ordered` (
  `liste_id` INT NOT NULL,
  `produse_id` INT NOT NULL,
  `category_id` INT NOT NULL,
  `position` INT NOT NULL,
  `stoc_produs` INT NULL DEFAULT NULL,
  PRIMARY KEY (`liste_id`, `produse_id`),
  INDEX `idx_liste_produse_category_position` (`liste_id`, `category_id`, `position` ASC),
  INDEX `fk_liste_au_produse_ordered_liste1_idx` (`liste_id` ASC),
  INDEX `fk_liste_au_produse_ordered_produse1_idx` (`produse_id` ASC),
  INDEX `fk_liste_au_produse_ordered_category1_idx` (`category_id` ASC),
  CONSTRAINT `fk_liste_au_produse_ordered_liste1`
    FOREIGN KEY (`liste_id`)
    REFERENCES `online_shop`.`liste` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_liste_au_produse_ordered_produse1`
    FOREIGN KEY (`produse_id`)
    REFERENCES `online_shop`.`produse` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_liste_au_produse_ordered_category1`
    FOREIGN KEY (`category_id`)
    REFERENCES `online_shop`.`category` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

-- -----------------------------------------------------
-- List Ordering System Documentation
-- -----------------------------------------------------
-- This database implements a flexible ordering system for lists:
--
-- 1. LIST-CATEGORY ORDERING (liste_au_categorii):
--    - Each list can have categories in a specific order
--    - Position field determines category display order (0 = first)
--    - Categories can be reordered independently for each list
--
-- 2. PRODUCT-CATEGORY ORDERING (liste_au_produse_ordered):
--    - Each product in a list belongs to a specific category
--    - Position field determines product order within its category (0 = first)
--    - Products can be reordered within categories
--    - Stock quantity (stoc_produs) is managed per list-product
--
-- 3. EXAMPLE USAGE:
--    List1 with categories: [Category2(pos=0), Category1(pos=1), Category3(pos=2)]
--    Category1 products: [Product2(pos=0), Product3(pos=1), Product1(pos=2), Product4(pos=3)]
--    This results in the exact order specified by the admin.
--
-- 4. PERFORMANCE:
--    - Indexes on (liste_id, position) for efficient category ordering
--    - Indexes on (liste_id, category_id, position) for efficient product ordering
--    - CASCADE constraints ensure data integrity when lists are deleted
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Data for table `online_shop`.`unitati`
-- -----------------------------------------------------
START TRANSACTION;
USE `online_shop`;
INSERT INTO `online_shop`.`unitati` (`id`, `denumire`) VALUES (DEFAULT, 'buc');
INSERT INTO `online_shop`.`unitati` (`id`, `denumire`) VALUES (DEFAULT, 'g');
INSERT INTO `online_shop`.`unitati` (`id`, `denumire`) VALUES (DEFAULT, 'kg');
INSERT INTO `online_shop`.`unitati` (`id`, `denumire`) VALUES (DEFAULT, 'l');
INSERT INTO `online_shop`.`unitati` (`id`, `denumire`) VALUES (DEFAULT, 'ml');
INSERT INTO `online_shop`.`unitati` (`id`, `denumire`) VALUES (DEFAULT, 'portii');

COMMIT;


-- -----------------------------------------------------
-- Data for table `online_shop`.`modalitati_de_plata`
-- -----------------------------------------------------
START TRANSACTION;
USE `online_shop`;
INSERT INTO `online_shop`.`modalitati_de_plata` (`id`, `name`, `description`) VALUES (DEFAULT, 'cash', 'Cash');
INSERT INTO `online_shop`.`modalitati_de_plata` (`id`, `name`, `description`) VALUES (DEFAULT, 'card', 'Card');
INSERT INTO `online_shop`.`modalitati_de_plata` (`id`, `name`, `description`) VALUES (DEFAULT, 'transfer_bancar', 'Transfer Bancar');
INSERT INTO `online_shop`.`modalitati_de_plata` (`id`, `name`, `description`) VALUES (DEFAULT, 'transfer_revolut', 'Transfer Revolut');

COMMIT;


-- -----------------------------------------------------
-- Data for table `online_shop`.`tipuri_livrare`
-- -----------------------------------------------------
START TRANSACTION;
USE `online_shop`;
INSERT INTO `online_shop`.`tipuri_livrare` (`id`, `denumire`) VALUES (DEFAULT, 'Ridicare de la sediu');
INSERT INTO `online_shop`.`tipuri_livrare` (`id`, `denumire`) VALUES (DEFAULT, 'Ridicare de la punct fix');
INSERT INTO `online_shop`.`tipuri_livrare` (`id`, `denumire`) VALUES (DEFAULT, 'Livrare la domiciliu');

COMMIT;


-- -----------------------------------------------------
-- Data for table `online_shop`.`category`
-- -----------------------------------------------------
START TRANSACTION;
USE `online_shop`;
INSERT INTO `online_shop`.`category` (`name`, `is_deleted`) VALUES ('Uncategorized', 0);

COMMIT;

