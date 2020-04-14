package com.roche.learn.storeDataInS3.model;

import lombok.Data;

import java.util.Date;

@Data
public class ArchiveAttribute {

    private String name;
    private boolean isDate;
    private String minDate;
    private String maxDate;
    private Integer minValue;
    private Integer maxValue;
}
