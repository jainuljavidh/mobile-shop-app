-- Run this ONLY if you already created the mobile_shop database before
-- the Repairs section was added. If you're setting up fresh, just run
-- schema.sql — it already includes the repairs table.
--
--   mysql -u root -p < database/migration_add_repairs.sql

USE mobile_shop;

CREATE TABLE IF NOT EXISTS repairs (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  received_date   DATE NOT NULL,
  customer_name   VARCHAR(150) NOT NULL,
  product_name    VARCHAR(150) NOT NULL,
  issue           VARCHAR(255) NOT NULL,
  amount          DECIMAL(10,2) NOT NULL DEFAULT 0,
  status          ENUM('Received', 'In Progress', 'Completed', 'Delivered to Customer')
                    NOT NULL DEFAULT 'Received',
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_received_date (received_date),
  INDEX idx_status (status)
) ENGINE=InnoDB;
