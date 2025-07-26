-- Seed data for test database
USE `online_shop`;

-- Seed categories (let them auto-increment, starting after the default "Uncategorized" category)
INSERT INTO `online_shop`.`category` (`name`, `image_path`, `is_deleted`) VALUES 
('Fruits', '/images/categories/fruits.jpg', 0),
('Vegetables', '/images/categories/vegetables.jpg', 0),
('Dairy', '/images/categories/dairy.jpg', 0),
('Bakery', '/images/categories/bakery.jpg', 0);
