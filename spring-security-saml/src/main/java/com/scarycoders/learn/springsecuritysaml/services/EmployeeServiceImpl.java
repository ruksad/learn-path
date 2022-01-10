package com.scarycoders.learn.springsecuritysaml.services;

import com.scarycoders.learn.springsecuritysaml.model.Employee;
import com.scarycoders.learn.springsecuritysaml.repository.DepartmentRepository;
import com.scarycoders.learn.springsecuritysaml.repository.EmployeeRepository;
import com.scarycoders.learn.springsecuritysaml.repository.TitleRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Service
public class EmployeeServiceImpl implements EmployeeService {

    private EmployeeRepository employeeRepository;
    private DepartmentRepository departmentRepository;
    private TitleRepository titleRepository;

    @Autowired
    private EmployeeServiceImpl(EmployeeRepository employeeRepository,
                                DepartmentRepository departmentRepository,
                                TitleRepository titleRepository) {
        this.employeeRepository=employeeRepository;
        this.departmentRepository=departmentRepository;
        this.titleRepository=titleRepository;
    }

    @Override
    public List<Employee> findAll(PageRequest page) {
        ArrayList<Employee> employees = new ArrayList<>();
        employeeRepository.findAll(page).iterator().forEachRemaining(employees::add);
        return employees;
    }

    @Override
    public Employee findById(Integer id) {
        Optional<Employee> byId = employeeRepository.findById(id);
        if(byId.isPresent())
            return byId.get();
        return null;
    }
}
