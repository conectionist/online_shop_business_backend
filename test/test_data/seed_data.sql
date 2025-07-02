-- Seed data for test database
USE `online_shop`;

-- Seed categories
INSERT INTO `online_shop`.`category` (`id`, `name`, `image_path`, `is_deleted`) VALUES 
(1, 'Fruits', '/images/categories/fruits.jpg', 0),
(2, 'Vegetables', '/images/categories/vegetables.jpg', 0),
(3, 'Dairy', '/images/categories/dairy.jpg', 0),
(4, 'Bakery', '/images/categories/bakery.jpg', 0);

-- Seed units
INSERT INTO `online_shop`.`unitati` (`id`, `denumire`) VALUES 
(1, 'buc'),
(2, 'g'),
(3, 'kg'),
(4, 'l'),
(5, 'ml');

-- Seed products
INSERT INTO `online_shop`.`produse` (`id`, `nume`, `cantitate`, `pret`, `primary_image_path`, `description`, `category_id`, `unitati_id`, `stock`, `is_deleted`) VALUES
(1, 'Apple', 1, 250, '/images/products/apple.jpg', 'Fresh red apples', 1, 1, 100, 0),
(2, 'Banana', 1, 300, '/images/products/banana.jpg', 'Yellow bananas', 1, 3, 150, 0),
(3, 'Carrot', 1, 200, '/images/products/carrot.jpg', 'Fresh carrots', 2, 3, 200, 0),
(4, 'Milk', 1, 450, '/images/products/milk.jpg', 'Fresh cow milk', 3, 4, 50, 0),
(5, 'Bread', 1, 350, '/images/products/bread.jpg', 'Freshly baked bread', 4, 1, 30, 0);
