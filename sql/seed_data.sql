-- ============================================================================
-- Seed Data for Water Access Inequality Analysis System (Communities A - J)
-- ============================================================================
USE water_access_inequality;

DELETE FROM sanitation;
DELETE FROM water_quality;
DELETE FROM communities;

-- Insert Communities
INSERT INTO communities (community_id, community_name, district, population, income_category) VALUES (1, 'Community A', 'Pune Rural North', 4200, 'Low');
INSERT INTO communities (community_id, community_name, district, population, income_category) VALUES (2, 'Community B', 'Mulshi West', 5800, 'Middle');
INSERT INTO communities (community_id, community_name, district, population, income_category) VALUES (3, 'Community C', 'Velhe Valley', 3150, 'Low');
INSERT INTO communities (community_id, community_name, district, population, income_category) VALUES (4, 'Community D', 'Bhor Central', 6400, 'Middle');
INSERT INTO communities (community_id, community_name, district, population, income_category) VALUES (5, 'Community E', 'Shirur East', 4900, 'Low');
INSERT INTO communities (community_id, community_name, district, population, income_category) VALUES (6, 'Community F', 'Maval Corridor', 7200, 'Middle');
INSERT INTO communities (community_id, community_name, district, population, income_category) VALUES (7, 'Community G', 'Khed South', 5100, 'Low');
INSERT INTO communities (community_id, community_name, district, population, income_category) VALUES (8, 'Community H', 'Baramati Town', 8900, 'Middle');
INSERT INTO communities (community_id, community_name, district, population, income_category) VALUES (9, 'Community I', 'Junnar Hills', 4650, 'Low');
INSERT INTO communities (community_id, community_name, district, population, income_category) VALUES (10, 'Community J', 'Aundh Urban Core', 12500, 'High');

-- Insert Water Quality Indicators
INSERT INTO water_quality (water_id, community_id, clean_water_access, availability_hours, distance_to_source, water_quality_score) VALUES (101, 1, 30.0, 4.0, 3.5, 55.0);
INSERT INTO water_quality (water_id, community_id, clean_water_access, availability_hours, distance_to_source, water_quality_score) VALUES (102, 2, 45.0, 8.0, 2.1, 66.0);
INSERT INTO water_quality (water_id, community_id, clean_water_access, availability_hours, distance_to_source, water_quality_score) VALUES (103, 3, 42.0, 6.0, 2.8, 62.0);
INSERT INTO water_quality (water_id, community_id, clean_water_access, availability_hours, distance_to_source, water_quality_score) VALUES (104, 4, 55.0, 10.0, 1.6, 72.0);
INSERT INTO water_quality (water_id, community_id, clean_water_access, availability_hours, distance_to_source, water_quality_score) VALUES (105, 5, 48.0, 7.0, 2.4, 68.0);
INSERT INTO water_quality (water_id, community_id, clean_water_access, availability_hours, distance_to_source, water_quality_score) VALUES (106, 6, 65.0, 14.0, 1.2, 78.0);
INSERT INTO water_quality (water_id, community_id, clean_water_access, availability_hours, distance_to_source, water_quality_score) VALUES (107, 7, 60.0, 11.0, 1.5, 74.0);
INSERT INTO water_quality (water_id, community_id, clean_water_access, availability_hours, distance_to_source, water_quality_score) VALUES (108, 8, 75.0, 18.0, 0.8, 84.0);
INSERT INTO water_quality (water_id, community_id, clean_water_access, availability_hours, distance_to_source, water_quality_score) VALUES (109, 9, 68.0, 12.0, 1.3, 78.0);
INSERT INTO water_quality (water_id, community_id, clean_water_access, availability_hours, distance_to_source, water_quality_score) VALUES (110, 10, 95.0, 24.0, 0.2, 96.0);

-- Insert Sanitation Indicators
INSERT INTO sanitation (sanitation_id, community_id, sanitation_coverage, toilet_availability, waste_management_score) VALUES (201, 1, 35.0, 40.0, 48.0);
INSERT INTO sanitation (sanitation_id, community_id, sanitation_coverage, toilet_availability, waste_management_score) VALUES (202, 2, 52.0, 58.0, 60.0);
INSERT INTO sanitation (sanitation_id, community_id, sanitation_coverage, toilet_availability, waste_management_score) VALUES (203, 3, 44.0, 49.0, 54.0);
INSERT INTO sanitation (sanitation_id, community_id, sanitation_coverage, toilet_availability, waste_management_score) VALUES (204, 4, 60.0, 65.0, 68.0);
INSERT INTO sanitation (sanitation_id, community_id, sanitation_coverage, toilet_availability, waste_management_score) VALUES (205, 5, 50.0, 55.0, 58.0);
INSERT INTO sanitation (sanitation_id, community_id, sanitation_coverage, toilet_availability, waste_management_score) VALUES (206, 6, 70.0, 75.0, 74.0);
INSERT INTO sanitation (sanitation_id, community_id, sanitation_coverage, toilet_availability, waste_management_score) VALUES (207, 7, 62.0, 68.0, 66.0);
INSERT INTO sanitation (sanitation_id, community_id, sanitation_coverage, toilet_availability, waste_management_score) VALUES (208, 8, 80.0, 85.0, 82.0);
INSERT INTO sanitation (sanitation_id, community_id, sanitation_coverage, toilet_availability, waste_management_score) VALUES (209, 9, 66.0, 72.0, 70.0);
INSERT INTO sanitation (sanitation_id, community_id, sanitation_coverage, toilet_availability, waste_management_score) VALUES (210, 10, 96.0, 98.0, 95.0);
