DROP DATABASE IF EXISTS uniquery;
CREATE DATABASE uniquery;
USE uniquery;

CREATE TABLE universities (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  location VARCHAR(200),
  founded_year INT,
  ranking INT
);

CREATE TABLE faculties (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  email VARCHAR(200),
  title VARCHAR(100),
  university_id INT,
  FOREIGN KEY (university_id) REFERENCES universities(id)
);

CREATE TABLE departments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  university_id INT,
  head_id INT,
  FOREIGN KEY (university_id) REFERENCES universities(id),
  FOREIGN KEY (head_id) REFERENCES faculties(id)
);

CREATE TABLE research_projects (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  department_id INT,
  start_year INT,
  end_year INT,
  funding DECIMAL(12,2),
  FOREIGN KEY (department_id) REFERENCES departments(id)
);

INSERT INTO universities (name, location, founded_year, ranking) VALUES
('Tech University', 'New York, USA', 1890, 5),
('Global Science Institute', 'London, UK', 1920, 12),
('Pacific State University', 'Sydney, Australia', 1950, 20),
('Continental Research College', 'Berlin, Germany', 1875, 15),
('Nova Innovation University', 'Toronto, Canada', 2000, 30);

INSERT INTO faculties (name, email, title, university_id) VALUES
('Dr. John Miller', 'john.m@techuni.edu', 'Professor of AI', 1),
('Dr. Emily Zhang', 'emily.z@techuni.edu', 'Associate Professor of Robotics', 1),
('Prof. Anna Smith', 'anna.s@gsi.ac.uk', 'Head of Physics', 2),
('Dr. Liam Brown', 'liam.b@gsi.ac.uk', 'Lecturer in Chemistry', 2),
('Dr. Sophia Green', 'sophia.g@psu.edu.au', 'Dean of Engineering', 3),
('Prof. Hans Weber', 'hans.w@crc.de', 'Head of Mathematics', 4),
('Dr. Marie Keller', 'marie.k@crc.de', 'Professor of Computer Science', 4),
('Dr. Daniel Clark', 'daniel.c@niu.ca', 'Lecturer in Data Science', 5);

INSERT INTO departments (name, university_id, head_id) VALUES
('Computer Science', 1, 1),
('Robotics', 1, 2),
('Physics', 2, 3),
('Chemistry', 2, 4),
('Engineering', 3, 5),
('Mathematics', 4, 6),
('Computer Engineering', 4, 7),
('Data Science', 5, 8);

INSERT INTO research_projects (title, department_id, start_year, end_year, funding) VALUES
('AI in Healthcare', 1, 2024, 2026, 500000.00),
('Autonomous Drones', 2, 2023, 2025, 650000.00),
('Quantum Materials', 3, 2023, 2025, 750000.00),
('Green Chemistry Innovations', 4, 2022, 2024, 300000.00),
('Renewable Energy Systems', 5, 2021, 2025, 900000.00),
('Advanced Algebra Research', 6, 2020, 2023, 200000.00),
('Neural Computing Models', 7, 2024, 2027, 820000.00),
('AI for Climate Change', 8, 2025, 2028, 1000000.00);
