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
  `nume` VARCHAR(45) NOT NULL,
  `cantitate` SMALLINT NOT NULL,
  `pret` SMALLINT NOT NULL,
  `description` VARCHAR(1500) NULL DEFAULT NULL,
  `category_id` INT NOT NULL,
  `unitati_id` INT NOT NULL,
  `stock` INT NULL DEFAULT NULL,
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
  `mesaj_introducere` VARCHAR(45) NULL,
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
  `denumire` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC),
  UNIQUE INDEX `modalitati_UNIQUE` (`denumire` ASC))
ENGINE = InnoDB
AUTO_INCREMENT = 5
DEFAULT CHARACTER SET = utf8mb4;


-- -----------------------------------------------------
-- Table `online_shop`.`tipuri_livrare`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `online_shop`.`tipuri_livrare` (
  `id` TINYINT NOT NULL AUTO_INCREMENT,
  `denumire` VARCHAR(45) NOT NULL,
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
  `field_name` ENUM('price', 'description', 'stock', 'availability') NOT NULL,
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
-- Table `online_shop`.`business_details_has_modalitati_de_plata`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `online_shop`.`business_details_has_modalitati_de_plata` (
  `business_details_id` TINYINT NOT NULL,
  `modalitati_de_plata_id` INT NOT NULL,
  PRIMARY KEY (`business_details_id`, `modalitati_de_plata_id`),
  INDEX `fk_business_details_has_modalitati_de_plata_modalitati_de_p_idx` (`modalitati_de_plata_id` ASC),
  INDEX `fk_business_details_has_modalitati_de_plata_business_detail_idx` (`business_details_id` ASC),
  CONSTRAINT `fk_business_details_has_modalitati_de_plata_business_details1`
    FOREIGN KEY (`business_details_id`)
    REFERENCES `online_shop`.`business_details` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_business_details_has_modalitati_de_plata_modalitati_de_pla1`
    FOREIGN KEY (`modalitati_de_plata_id`)
    REFERENCES `online_shop`.`modalitati_de_plata` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
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
-- Table `online_shop`.`liste_au_produse`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `online_shop`.`liste_au_produse` (
  `liste_id` INT NOT NULL,
  `produse_id` INT NOT NULL,
  PRIMARY KEY (`liste_id`, `produse_id`),
  INDEX `fk_liste_has_produse_produse1_idx` (`produse_id` ASC),
  INDEX `fk_liste_has_produse_liste1_idx` (`liste_id` ASC),
  CONSTRAINT `fk_liste_has_produse_liste1`
    FOREIGN KEY (`liste_id`)
    REFERENCES `online_shop`.`liste` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_liste_has_produse_produse1`
    FOREIGN KEY (`produse_id`)
    REFERENCES `online_shop`.`produse` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

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
INSERT INTO `online_shop`.`modalitati_de_plata` (`id`, `denumire`) VALUES (DEFAULT, 'Cash');
INSERT INTO `online_shop`.`modalitati_de_plata` (`id`, `denumire`) VALUES (DEFAULT, 'Card');
INSERT INTO `online_shop`.`modalitati_de_plata` (`id`, `denumire`) VALUES (DEFAULT, 'Transfer Bancar');
INSERT INTO `online_shop`.`modalitati_de_plata` (`id`, `denumire`) VALUES (DEFAULT, 'Transfer Revolut');

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

