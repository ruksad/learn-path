package com.roche.learn.storeDataInS3.controller;

import com.roche.learn.storeDataInS3.model.DbMetaData;
import com.roche.learn.storeDataInS3.service.S3Ops;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.websocket.server.PathParam;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.sql.SQLException;
import java.time.LocalDateTime;
import java.util.Date;

@RestController
public class AwsController {

    private S3Ops s3Ops;

    @Autowired
    AwsController(S3Ops s3Ops) {
        this.s3Ops = s3Ops;
    }

    @GetMapping(value = "/uploadAFileToS3/{fileName}", produces = "Application/text")
    public Object test(@PathVariable("fileName") String fileName, @RequestParam("filePath") String filePath) {
        return s3Ops.uploadFile(fileName, filePath);
    }

    @GetMapping(value = "/db/attributes", produces = "application/json")
    public ResponseEntity<DbMetaData> getArchiveAbleAttrs() throws SQLException {
        return ResponseEntity.ok(s3Ops.extractMetadata());
    }

    @PostMapping(value = "/db/attributes/archive/{tableName}/{attributeName}", produces = "application/json")
    public ResponseEntity archiveByAttribute(@PathVariable String tableName, @PathVariable String attributeName,
                                             @RequestParam boolean isDateAttribute, @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime from,
                                             @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime to) throws FileNotFoundException {

        if (isDateAttribute) {
            s3Ops.runQuery(tableName,attributeName,from,to);
        } else {

        }
        return null;
    }

    @PostMapping(value = "/db/unArchive/{archive}",produces = "application/txt")
    public Boolean unArchiveByAttribute(@PathVariable String archive) throws IOException {
        s3Ops.unArchive(archive);
        return true;
    }
}

