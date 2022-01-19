package com.scarycoders.learn.springsecuritysaml.model;

import com.fasterxml.jackson.annotation.JsonIgnore;

import javax.persistence.Embeddable;
import javax.persistence.FetchType;
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;
import java.io.Serializable;
import java.util.Objects;

@Embeddable
public class TitlePk implements Serializable {
    private String title;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "emp_no")
    @JsonIgnore
    private Employee employee;

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
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
        TitlePk titlePk = (TitlePk) o;
        return Objects.equals(title, titlePk.title) && Objects.equals(employee, titlePk.employee);
    }

    @Override
    public int hashCode() {
        return Objects.hash(title, employee);
    }
}
