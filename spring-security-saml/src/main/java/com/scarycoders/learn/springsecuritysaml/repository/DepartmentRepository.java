package com.scarycoders.learn.springsecuritysaml.repository;

import com.scarycoders.learn.springsecuritysaml.model.Department;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface DepartmentRepository extends CrudRepository<Department,String> {
}
