package com.roche.learn.storeDataInS3.model;

import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.ArrayList;
import java.util.List;

@Data
@NoArgsConstructor
public class TableMetaData {
    private String name;
    private List<ArchiveAttribute> archiveAbleAttributes = new ArrayList<>(10);
}
