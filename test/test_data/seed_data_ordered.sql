-- Seed data for ordered list system testing
USE `online_shop`;

-- Clear existing data (for fresh testing)
DELETE FROM `liste_au_produse_ordered`;
DELETE FROM `liste_au_categorii`;
DELETE FROM `liste_au_produse`;
DELETE FROM `comenzi_au_produse`;
DELETE FROM `comenzi`;
DELETE FROM `liste`;
DELETE FROM `produse`;
DELETE FROM `category`;

-- Reset auto-increment counters
ALTER TABLE `category` AUTO_INCREMENT = 1;
ALTER TABLE `produse` AUTO_INCREMENT = 1;
ALTER TABLE `liste` AUTO_INCREMENT = 1;

-- Seed categories
INSERT INTO `online_shop`.`category` (`name`, `image_path`, `is_deleted`) VALUES 
('Fruits', '/images/categories/fruits.jpg', 0),
('Vegetables', '/images/categories/vegetables.jpg', 0),
('Dairy', '/images/categories/dairy.jpg', 0),
('Bakery', '/images/categories/bakery.jpg', 0),
('Meat', '/images/categories/meat.jpg', 0),
('Beverages', '/images/categories/beverages.jpg', 0);

-- Seed products
INSERT INTO `online_shop`.`produse` (`nume`, `cantitate`, `pret`, `description`, `category_id`, `unitati_id`, `is_deleted`) VALUES 
-- Fruits (category_id = 1)
('Apples', 1, 500, 'Fresh red apples', 1, 1, 0),
('Bananas', 1, 300, 'Yellow bananas', 1, 1, 0),
('Oranges', 1, 400, 'Sweet oranges', 1, 1, 0),
('Strawberries', 1, 800, 'Fresh strawberries', 1, 1, 0),

-- Vegetables (category_id = 2)
('Carrots', 1, 200, 'Fresh carrots', 2, 1, 0),
('Tomatoes', 1, 350, 'Ripe tomatoes', 2, 1, 0),
('Cucumbers', 1, 250, 'Fresh cucumbers', 2, 1, 0),
('Lettuce', 1, 150, 'Green lettuce', 2, 1, 0),

-- Dairy (category_id = 3)
('Milk', 1, 600, 'Fresh milk', 3, 2, 0),
('Cheese', 1, 1200, 'Aged cheese', 3, 1, 0),
('Yogurt', 1, 450, 'Natural yogurt', 3, 2, 0),
('Butter', 1, 800, 'Fresh butter', 3, 1, 0),

-- Bakery (category_id = 4)
('Bread', 1, 300, 'Fresh bread', 4, 1, 0),
('Croissants', 1, 500, 'Buttery croissants', 4, 1, 0),
('Cake', 1, 1500, 'Chocolate cake', 4, 1, 0),
('Cookies', 1, 200, 'Homemade cookies', 4, 1, 0),

-- Meat (category_id = 5)
('Chicken', 1, 2500, 'Fresh chicken breast', 5, 1, 0),
('Beef', 1, 4000, 'Premium beef', 5, 1, 0),
('Pork', 1, 3000, 'Fresh pork', 5, 1, 0),

-- Beverages (category_id = 6)
('Coffee', 1, 800, 'Fresh coffee', 6, 2, 0),
('Tea', 1, 300, 'Herbal tea', 6, 2, 0),
('Juice', 1, 500, 'Fresh orange juice', 6, 2, 0);

-- Seed lists
INSERT INTO `online_shop`.`liste` (`data`, `is_current`, `is_published`, `mesaj_introducere`, `alte_detalii`, `numar_whatsapp`, `orare_livrari_id`, `is_deleted`) VALUES 
('2024-01-15', 1, 1, 'Welcome to our fresh produce list!', 'All items are fresh and locally sourced.', '+40123456789', 1, 0),
('2024-01-22', 0, 1, 'Weekly grocery list', 'Order by Friday for Sunday delivery.', '+40123456789', 1, 0),
('2024-01-29', 0, 0, 'Special order list', 'Custom orders only.', '+40123456789', 1, 0);

-- Test Scenario 1: List with categories in specific order
-- Add categories to List 1 in specific order
INSERT INTO `online_shop`.`liste_au_categorii` (`liste_id`, `category_id`, `position`) VALUES 
(1, 2, 1),  -- Vegetables first (position 1)
(1, 1, 2),  -- Fruits second (position 2)
(1, 3, 3),  -- Dairy third (position 3)
(1, 4, 4);  -- Bakery fourth (position 4)

-- Add products to List 1 with specific ordering within categories
INSERT INTO `online_shop`.`liste_au_produse_ordered` (`liste_id`, `produse_id`, `category_id`, `position`, `stoc_produs`) VALUES 
-- Vegetables (category_id = 2) - position 1 in list
(1, 5, 2, 1, 50),   -- Carrots first in vegetables
(1, 6, 2, 2, 30),   -- Tomatoes second in vegetables
(1, 7, 2, 3, 25),   -- Cucumbers third in vegetables
(1, 8, 2, 4, 20),   -- Lettuce fourth in vegetables

-- Fruits (category_id = 1) - position 2 in list
(1, 2, 1, 1, 40),   -- Bananas first in fruits
(1, 1, 1, 2, 35),   -- Apples second in fruits
(1, 3, 1, 3, 30),   -- Oranges third in fruits
(1, 4, 1, 4, 15),   -- Strawberries fourth in fruits

-- Dairy (category_id = 3) - position 3 in list
(1, 9, 3, 1, 20),   -- Milk first in dairy
(1, 10, 3, 2, 15),  -- Cheese second in dairy
(1, 11, 3, 3, 25),  -- Yogurt third in dairy
(1, 12, 3, 4, 10),  -- Butter fourth in dairy

-- Bakery (category_id = 4) - position 4 in list
(1, 13, 4, 1, 30),  -- Bread first in bakery
(1, 14, 4, 2, 20),  -- Croissants second in bakery
(1, 15, 4, 3, 5),   -- Cake third in bakery
(1, 16, 4, 4, 40);  -- Cookies fourth in bakery

-- Test Scenario 2: List with different category order
-- Add categories to List 2 in different order
INSERT INTO `online_shop`.`liste_au_categorii` (`liste_id`, `category_id`, `position`) VALUES 
(2, 6, 1),  -- Beverages first
(2, 5, 2),  -- Meat second
(2, 1, 3),  -- Fruits third
(2, 4, 4);  -- Bakery fourth

-- Add products to List 2 with different ordering
INSERT INTO `online_shop`.`liste_au_produse_ordered` (`liste_id`, `produse_id`, `category_id`, `position`, `stoc_produs`) VALUES 
-- Beverages (category_id = 6) - position 1 in list
(2, 17, 6, 1, 25),  -- Coffee first in beverages
(2, 18, 6, 2, 30),  -- Tea second in beverages
(2, 19, 6, 3, 20),  -- Juice third in beverages

-- Meat (category_id = 5) - position 2 in list
(2, 14, 5, 1, 10),  -- Chicken first in meat
(2, 15, 5, 2, 8),   -- Beef second in meat
(2, 16, 5, 3, 12),  -- Pork third in meat

-- Fruits (category_id = 1) - position 3 in list
(2, 1, 1, 1, 25),   -- Apples first in fruits
(2, 2, 1, 2, 30),   -- Bananas second in fruits
(2, 4, 1, 3, 15),   -- Strawberries third in fruits

-- Bakery (category_id = 4) - position 4 in list
(2, 13, 4, 1, 20),  -- Bread first in bakery
(2, 14, 4, 2, 15),  -- Croissants second in bakery
(2, 16, 4, 3, 30);  -- Cookies third in bakery

-- Test Scenario 3: Empty list (List 3) - no categories or products added
-- This tests the empty state handling

-- Test Scenario 4: List with single category
-- Add only one category to List 3
INSERT INTO `online_shop`.`liste_au_categorii` (`liste_id`, `category_id`, `position`) VALUES 
(3, 3, 1);  -- Dairy only

-- Add products to List 3 (single category)
INSERT INTO `online_shop`.`liste_au_produse_ordered` (`liste_id`, `produse_id`, `category_id`, `position`, `stoc_produs`) VALUES 
(3, 9, 3, 1, 15),   -- Milk first
(3, 10, 3, 2, 10),  -- Cheese second
(3, 11, 3, 3, 20);  -- Yogurt third 