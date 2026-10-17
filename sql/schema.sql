-- ============================================================================
-- SYMBIOSIS INSTITUTE OF TECHNOLOGY, PUNE
-- Course: Database Concepts for Data Science Lab (DCDS Lab ESE Miniproject)
-- Project: Water Access Inequality Analysis System
-- Relational Schema, Constraints, Views, and Stored Procedure (MySQL 8.0)
-- ============================================================================

CREATE DATABASE IF NOT EXISTS water_access_inequality;
USE water_access_inequality;

DROP TABLE IF EXISTS sanitation;
DROP TABLE IF EXISTS water_quality;
DROP TABLE IF EXISTS communities;

-- 1. Communities Master Table
CREATE TABLE communities (
    community_id INT PRIMARY KEY,
    community_name VARCHAR(100) NOT NULL UNIQUE,
    district VARCHAR(100) NOT NULL,
    population INT NOT NULL CHECK (population > 0),
    income_category ENUM('Low', 'Middle', 'High') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Water Quality & Access Table
CREATE TABLE water_quality (
    water_id INT PRIMARY KEY,
    community_id INT NOT NULL UNIQUE,
    clean_water_access DECIMAL(5, 2) NOT NULL CHECK (clean_water_access BETWEEN 0 AND 100),
    availability_hours DECIMAL(4, 1) NOT NULL CHECK (availability_hours BETWEEN 0 AND 24),
    distance_to_source DECIMAL(5, 2) NOT NULL CHECK (distance_to_source >= 0),
    water_quality_score DECIMAL(5, 2) NOT NULL CHECK (water_quality_score BETWEEN 0 AND 100),
    CONSTRAINT fk_water_community
        FOREIGN KEY (community_id) REFERENCES communities(community_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- 3. Sanitation Indicators Table
CREATE TABLE sanitation (
    sanitation_id INT PRIMARY KEY,
    community_id INT NOT NULL UNIQUE,
    sanitation_coverage DECIMAL(5, 2) NOT NULL CHECK (sanitation_coverage BETWEEN 0 AND 100),
    toilet_availability DECIMAL(5, 2) NOT NULL CHECK (toilet_availability BETWEEN 0 AND 100),
    waste_management_score DECIMAL(5, 2) NOT NULL CHECK (waste_management_score BETWEEN 0 AND 100),
    CONSTRAINT fk_sanitation_community
        FOREIGN KEY (community_id) REFERENCES communities(community_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Indexes for analytical query optimization
CREATE INDEX idx_communities_income ON communities(income_category);
CREATE INDEX idx_water_access ON water_quality(clean_water_access);

-- Analytical View combining all three normalized tables
CREATE OR REPLACE VIEW vw_community_water_sanitation AS
SELECT
    c.community_id,
    c.community_name,
    c.district,
    c.population,
    c.income_category,
    w.clean_water_access,
    w.availability_hours,
    w.distance_to_source,
    w.water_quality_score,
    s.sanitation_coverage,
    s.toilet_availability,
    s.waste_management_score
FROM communities c
INNER JOIN water_quality w ON c.community_id = w.community_id
LEFT JOIN sanitation s ON c.community_id = s.community_id;

-- Stored Procedure: GetPoorWaterAccess(threshold)
DROP PROCEDURE IF EXISTS GetPoorWaterAccess;
DELIMITER //
CREATE PROCEDURE GetPoorWaterAccess(IN access_threshold DECIMAL(5, 2))
BEGIN
    SELECT
        c.community_id,
        c.community_name,
        c.district,
        c.population,
        c.income_category,
        w.clean_water_access,
        w.availability_hours,
        w.distance_to_source,
        w.water_quality_score
    FROM communities c
    INNER JOIN water_quality w ON c.community_id = w.community_id
    WHERE w.clean_water_access < access_threshold
    ORDER BY w.clean_water_access ASC;
END //
DELIMITER ;
