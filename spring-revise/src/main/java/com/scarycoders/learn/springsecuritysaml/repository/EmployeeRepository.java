package com.scarycoders.learn.springsecuritysaml.repository;

import com.scarycoders.learn.springsecuritysaml.model.Employee;
import org.springframework.data.repository.PagingAndSortingRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface EmployeeRepository extends PagingAndSortingRepository<Employee,Integer> {
}
