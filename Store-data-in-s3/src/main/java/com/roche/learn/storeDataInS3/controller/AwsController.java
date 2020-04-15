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
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Objects;

@RestController
@Slf4j
public class AwsController {

    private S3Ops s3Ops;

    @Autowired
    AwsController(S3Ops s3Ops) {
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

        if (isDateAttribute) {
            final LocalDateTime fromLD = LocalDateTime.parse(from, DateTimeFormatter.ISO_DATE_TIME);
            LocalDateTime toLD;
            if (Objects.isNull(to)) {
                toLD = LocalDateTime.now();
            } else {
                toLD = LocalDateTime.parse(from, DateTimeFormatter.ISO_DATE_TIME);
            }
            log.info("archiving for table {} and attribute {} and for date from {}, to {}",tableName,attributeName,from,to);
            s3Ops.runQuery(tableName, attributeName, fromLD, toLD);
        } else {

        }
        return ResponseEntity.ok(Boolean.TRUE);
    }

    @PostMapping(value = "/db/tables/unArchive/{archive}")
    public ResponseEntity<Boolean> unArchiveByAttribute(@PathVariable String archive) throws IOException {
        s3Ops.unArchive(archive);
        return ResponseEntity.ok(Boolean.TRUE);
    }
}

