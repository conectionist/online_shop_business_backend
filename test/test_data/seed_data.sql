-- Seed data for test database
USE `online_shop`;

-- Seed categories
INSERT INTO `online_shop`.`category` (`id`, `name`, `image_path`, `is_deleted`) VALUES 
(1, 'Fruits', '/images/categories/fruits.jpg', 0),
(2, 'Vegetables', '/images/categories/vegetables.jpg', 0),
(3, 'Dairy', '/images/categories/dairy.jpg', 0),
(4, 'Bakery', '/images/categories/bakery.jpg', 0);
