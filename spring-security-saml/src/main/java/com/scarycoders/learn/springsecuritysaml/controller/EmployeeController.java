package com.scarycoders.learn.springsecuritysaml.controller;

import com.scarycoders.learn.springsecuritysaml.model.Employee;
import com.scarycoders.learn.springsecuritysaml.services.EmployeeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("api/v1/employees")
public class EmployeeController {

    private final EmployeeService employeeService;

    @Autowired
    private EmployeeController(EmployeeService employeeService){
        this.employeeService=employeeService;
    }
    @GetMapping(value= "/all",produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<List<Employee>> getAllEmployees(@RequestParam("pageNo") int pageNumber
            ,@RequestParam("pageSize") int pageSize){
        PageRequest page = PageRequest.of(pageNumber, pageSize);
        List<Employee> all = employeeService.findAll(page);
        return ResponseEntity.status(HttpStatus.OK).body(all);
    }

    @GetMapping(value = "/employee/{id}",produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Employee> getById(@PathVariable("id") Integer id){
        Employee byId = employeeService.findById(id);
        return ResponseEntity.status(HttpStatus.OK).body(byId);
    }
}
