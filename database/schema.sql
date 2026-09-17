-- Mobile Shop Sales Management — Database Schema
-- Run this once to create the database and tables:
--   mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS mobile_shop
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE mobile_shop;

-- ---------------------------------------------------------------
-- Sales
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sales (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  sale_date     DATE NOT NULL,
  product_name  VARCHAR(150) NOT NULL,
  amount        DECIMAL(10,2) NOT NULL DEFAULT 0,
  split_amount  DECIMAL(10,2) NOT NULL DEFAULT 0,
  total_amount  DECIMAL(10,2) NOT NULL DEFAULT 0,
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_sale_date (sale_date)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------
-- Expenses
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS expenses (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  expense_date   DATE NOT NULL,
  expense_name   VARCHAR(150) NOT NULL,
  amount         DECIMAL(10,2) NOT NULL DEFAULT 0,
  created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_expense_date (expense_date)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------
-- Purchases
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS purchases (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  purchase_date  DATE NOT NULL,
  dealer_name    VARCHAR(150) NOT NULL,
  product_name   VARCHAR(150) NOT NULL,
  amount         DECIMAL(10,2) NOT NULL DEFAULT 0,
  created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_purchase_date (purchase_date)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------
-- Customer Enquiries
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS enquiries (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  enquiry_date    DATE NOT NULL,
  customer_name   VARCHAR(150) NOT NULL,
  product_name    VARCHAR(150) NOT NULL,
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_enquiry_date (enquiry_date)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------
-- Repairs — tracks a device from drop-off to hand-back
-- ---------------------------------------------------------------
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
