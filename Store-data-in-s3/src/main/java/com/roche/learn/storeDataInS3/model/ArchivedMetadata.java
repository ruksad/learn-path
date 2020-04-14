package com.roche.learn.storeDataInS3.model;

import lombok.Data;

@Data
public class ArchivedMetadata {
    private String dbName;
    private String tableName;
    private boolean isArchivedForDate;
    private String from;
    private String to;
}
