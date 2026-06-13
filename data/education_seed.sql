-- Education Seed Data
CREATE TABLE qualification_levels (level_id INT PRIMARY KEY AUTO_INCREMENT, level_name VARCHAR(100), level_rank INT);
CREATE TABLE qualification_canonical (canonical_id INT PRIMARY KEY AUTO_INCREMENT, canonical_name VARCHAR(255), level_id INT, short_code VARCHAR(20));
CREATE TABLE qualification_aliases (alias_id INT PRIMARY KEY AUTO_INCREMENT, raw_string VARCHAR(255), canonical_id INT, normalized VARCHAR(255), source VARCHAR(50), confidence FLOAT);
CREATE TABLE field_of_study (field_id INT PRIMARY KEY AUTO_INCREMENT, canonical_field VARCHAR(255), category VARCHAR(100), field_aliases TEXT);
CREATE TABLE candidate_education (edu_id INT PRIMARY KEY AUTO_INCREMENT, candidate_id INT, raw_degree VARCHAR(255), raw_field VARCHAR(255), canonical_id INT, field_id INT, institution VARCHAR(255), graduation_year INT, cgpa FLOAT, parse_status VARCHAR(20), confidence FLOAT);

INSERT INTO qualification_levels (level_name, level_rank) VALUES ('SCHOOL', 1);
INSERT INTO qualification_levels (level_name, level_rank) VALUES ('DIPLOMA', 2);
INSERT INTO qualification_levels (level_name, level_rank) VALUES ('UG ENGINEERING', 3);
INSERT INTO qualification_levels (level_name, level_rank) VALUES ('UG SCIENCE', 3);
INSERT INTO qualification_levels (level_name, level_rank) VALUES ('PG ENGINEERING', 4);
INSERT INTO qualification_levels (level_name, level_rank) VALUES ('PG OTHER', 4);
INSERT INTO qualification_levels (level_name, level_rank) VALUES ('DOCTORATE', 5);
