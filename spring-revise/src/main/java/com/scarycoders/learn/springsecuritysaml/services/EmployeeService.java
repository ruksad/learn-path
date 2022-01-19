package com.scarycoders.learn.springsecuritysaml.services;

import com.scarycoders.learn.springsecuritysaml.model.Employee;
import org.springframework.data.domain.PageRequest;

import java.util.List;

public interface EmployeeService {
    List<Employee> findAll(PageRequest page);
    Employee findById(Integer id);
}
