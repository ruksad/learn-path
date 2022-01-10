package com.scarycoders.learn.springsecuritysaml.model;

import com.fasterxml.jackson.annotation.JsonBackReference;
import com.fasterxml.jackson.annotation.JsonIgnore;

import javax.persistence.Column;
import javax.persistence.Embeddable;
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;
import java.io.Serializable;
import java.util.Objects;

@Embeddable
public class SalaryPk implements Serializable {

    @Column(name = "salary")
    private Integer salary;

    @ManyToOne
    @JoinColumn(name = "emp_no")
    @JsonIgnore
    private Employee employee;

    public Integer getSalary() {
        return salary;
    }

    public void setSalary(Integer salary) {
        this.salary = salary;
    }

    public Employee getEmployee() {
        return employee;
    }

    public void setEmployee(Employee employee) {
        this.employee = employee;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        SalaryPk salaryPk = (SalaryPk) o;
        return Objects.equals(salary, salaryPk.salary) && Objects.equals(employee, salaryPk.employee);
    }

    @Override
    public int hashCode() {
        return Objects.hash(salary, employee);
    }
}
