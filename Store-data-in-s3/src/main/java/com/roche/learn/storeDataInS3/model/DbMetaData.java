package com.roche.learn.storeDataInS3.model;

import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
public class DbMetaData {
    private String dataBaseName;
    private List<TableMetaData> tableMetaData=new ArrayList<>(10);
}
