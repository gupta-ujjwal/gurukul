-- Learning Agent Database Schema
-- This file contains the complete database structure for the learning agent application

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS Sessions;
DROP TABLE IF EXISTS Progress_tracker;
DROP TABLE IF EXISTS Student;

-- Create Student table
CREATE TABLE Student (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    class VARCHAR(50) NOT NULL,
    username VARCHAR(80) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    profile_image TEXT, -- Base64 encoded image string
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create Progress_tracker table
CREATE TABLE Progress_tracker (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    studentId INTEGER NOT NULL,
    subject VARCHAR(100) NOT NULL,
    last_chapter_covered VARCHAR(100),
    next_chapter VARCHAR(100),
    overall_progress INTEGER DEFAULT 0,
    last_login_at DATETIME,
    FOREIGN KEY (studentId) REFERENCES Student (id) ON DELETE CASCADE,
    UNIQUE (studentId, subject)
);

-- Create Sessions table
CREATE TABLE Sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    StudentId INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    duration INTEGER, -- duration in minutes
    summarised_summary TEXT,
    FOREIGN KEY (StudentId) REFERENCES Student (id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX idx_student_username ON Student(username);
CREATE INDEX idx_progress_studentId ON Progress_tracker(studentId);
CREATE INDEX idx_progress_subject ON Progress_tracker(subject);
CREATE INDEX idx_sessions_studentId ON Sessions(StudentId);
CREATE INDEX idx_sessions_created_at ON Sessions(created_at);

-- Insert sample data (optional - comment out if not needed)
/*
INSERT INTO Student (name, class, username, password) VALUES 
('John Doe', '10th Grade', 'john.doe', 'password123'),
('Jane Smith', '11th Grade', 'jane.smith', 'password123');

INSERT INTO Progress_tracker (studentId, subject, last_chapter_covered, next_chapter, overall_progress) VALUES
(1, 'Mathematics', 'Chapter 3: Algebra', 'Chapter 4: Geometry', 65),
(1, 'Science', 'Chapter 2: Physics', 'Chapter 3: Chemistry', 45),
(2, 'Mathematics', 'Chapter 5: Calculus', 'Chapter 6: Statistics', 80),
(2, 'Literature', 'Chapter 1: Poetry', 'Chapter 2: Prose', 90);

INSERT INTO Sessions (StudentId, duration, summarised_summary) VALUES
(1, 45, 'Completed algebra exercises and reviewed basic concepts'),
(2, 60, 'Read and analyzed poetry from the Romantic period');
*/