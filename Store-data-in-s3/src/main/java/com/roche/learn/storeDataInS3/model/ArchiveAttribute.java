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

    public static ArchiveAttribute getArchiveAttribute(String column_name, boolean b) {
        ArchiveAttribute archiveAttribute = new ArchiveAttribute();
        archiveAttribute.setDate(b);
        archiveAttribute.setName(column_name);
        return archiveAttribute;
    }
}
