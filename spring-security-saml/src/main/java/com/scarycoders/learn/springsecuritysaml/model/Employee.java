package com.scarycoders.learn.springsecuritysaml.model;

import com.fasterxml.jackson.annotation.JsonManagedReference;

import javax.persistence.*;
import java.sql.Date;
import java.util.List;
import java.util.Objects;

@Entity
@Table(name = "employees")
public class Employee {

    @Id
    private Integer emp_no;
    private Date birth_date;
    private String first_name;
    private String last_name;
    @Enumerated(EnumType.STRING)
    private Gender gender;
    private Date hire_date;
    @ManyToMany
    @JoinTable(name="dept_emp",
            joinColumns = @JoinColumn(name="emp_no"),
            inverseJoinColumns = @JoinColumn(name="dept_no"))
    List<Department> departments;

    @OneToMany(mappedBy = "id.employee",cascade = CascadeType.PERSIST)
    @JsonManagedReference()
    List<Salary> salaries;
    @OneToMany(mappedBy = "id.employee",cascade = CascadeType.PERSIST)
    @JsonManagedReference()
    List<Title> titles;

    @ManyToMany
    @JoinTable(name = "dept_manager",
    joinColumns = @JoinColumn(name="emp_no") ,
    inverseJoinColumns =@JoinColumn(name="dept_no") )
    List<Department> departmentManger;

    public Integer getEmp_no() {
        return emp_no;
    }

    public void setEmp_no(Integer emp_no) {
        this.emp_no = emp_no;
    }

    public Date getBirth_date() {
        return birth_date;
    }

    public void setBirth_date(Date birth_date) {
        this.birth_date = birth_date;
    }

    public String getFirst_name() {
        return first_name;
    }

    public void setFirst_name(String first_name) {
        this.first_name = first_name;
    }

    public String getLast_name() {
        return last_name;
    }

    public void setLast_name(String last_name) {
        this.last_name = last_name;
    }

    public Gender getGender() {
        return gender;
    }

    public void setGender(Gender gender) {
        this.gender = gender;
    }

    public Date getHire_date() {
        return hire_date;
    }

    public void setHire_date(Date hire_date) {
        this.hire_date = hire_date;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Employee employee = (Employee) o;
        return Objects.equals(emp_no, employee.emp_no) && Objects.equals(birth_date, employee.birth_date) && Objects.equals(first_name, employee.first_name) && Objects.equals(last_name, employee.last_name) && Objects.equals(gender, employee.gender) && Objects.equals(hire_date, employee.hire_date);
    }

    @Override
    public int hashCode() {
        return Objects.hash(emp_no, birth_date, first_name, last_name, gender, hire_date);
    }

    public List<Department> getDepartments() {
        return departments;
    }

    public void setDepartments(List<Department> departments) {
        this.departments = departments;
    }

    public List<Salary> getSalaries() {
        return salaries;
    }

    public void setSalaries(List<Salary> salaries) {
        this.salaries = salaries;
    }

    public List<Title> getTitles() {
        return titles;
    }

    public void setTitles(List<Title> titles) {
        this.titles = titles;
    }

    public List<Department> getDepartmentManger() {
        return departmentManger;
    }

    public void setDepartmentManger(List<Department> departmentManger) {
        this.departmentManger = departmentManger;
    }
}
