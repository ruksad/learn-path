package com.roche.learn.storeDataInS3.controller;

import com.roche.learn.storeDataInS3.model.DbMetaData;
import com.roche.learn.storeDataInS3.service.S3Ops;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.sql.SQLException;

@RestController
@Slf4j
public class ArchiveController {

    private S3Ops s3Ops;

    @Autowired
    ArchiveController(S3Ops s3Ops) {
        this.s3Ops = s3Ops;
    }

    @GetMapping(value = "/metadata", produces = "application/json")
    public ResponseEntity<DbMetaData> getArchiveAbleAttrs() throws SQLException, IOException {
        return ResponseEntity.ok(s3Ops.extractInfo());
    }

    @PostMapping(value = "/db/tables/archive/{tableName}/{attributeName}")
    public ResponseEntity archiveByAttribute(@PathVariable String tableName, @PathVariable String attributeName,
                                             @RequestParam boolean isDateAttribute, @RequestParam String from,
                                             @RequestParam(required = false) String to) throws FileNotFoundException {


        //log.info("archiving for table {} and attribute {} and for date from {}, to {}", tableName, attributeName, from, to);
        s3Ops.runQuery(tableName, attributeName, from, to,isDateAttribute);

        return ResponseEntity.ok(Boolean.TRUE);
    }

    @PostMapping(value = "/db/tables/unArchive/{archive}")
    public ResponseEntity<Boolean> unArchiveByAttribute(@PathVariable String archive) throws IOException {

        return ResponseEntity.ok(s3Ops.unArchive(archive));
    }
}

