package com.scarycoders.learn.springsecuritysaml.model;

import javax.persistence.Column;
import javax.persistence.EmbeddedId;
import javax.persistence.Entity;
import javax.persistence.Table;
import java.sql.Date;
import java.util.Objects;

@Entity
@Table(name="titles")
public class Title {
    private Date fromDate;
    private Date toDate;
    @Column(insertable = false,updatable = false)
    private String title;

    @EmbeddedId
    private TitlePk id;

    public Date getFromDate() {
        return fromDate;
    }

    public void setFromDate(Date fromDate) {
        this.fromDate = fromDate;
    }

    public Date getToDate() {
        return toDate;
    }

    public void setToDate(Date toDate) {
        this.toDate = toDate;
    }


    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Title title1 = (Title) o;
        return Objects.equals(fromDate, title1.fromDate) && Objects.equals(toDate, title1.toDate) ;
    }

    @Override
    public int hashCode() {
        return Objects.hash(fromDate, toDate);
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }
}
