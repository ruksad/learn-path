CREATE DATABASE IF NOT EXISTS employees_data;
USE employees_data;

SELECT 'CREATING DATABASE STRUCTURE' as 'INFO';

DROP TABLE IF EXISTS dept_emp,
                     dept_manager,
                     titles,
                     salaries,
                     employees,
                     departments;

set default_storage_engine = InnoDB;