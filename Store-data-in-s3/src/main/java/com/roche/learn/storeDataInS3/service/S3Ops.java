package com.roche.learn.storeDataInS3.service;

import com.amazonaws.AmazonServiceException;
import com.amazonaws.SdkClientException;
import com.amazonaws.services.s3.AmazonS3;
import com.amazonaws.services.s3.model.ObjectListing;
import com.amazonaws.services.s3.model.ObjectMetadata;
import com.amazonaws.services.s3.model.PutObjectRequest;
import com.amazonaws.services.s3.model.S3Object;
import com.amazonaws.services.s3.model.S3ObjectSummary;
import com.roche.learn.storeDataInS3.config.ApplicationProps;
import com.roche.learn.storeDataInS3.model.ArchiveAttribute;
import com.roche.learn.storeDataInS3.model.DbMetaData;
import com.roche.learn.storeDataInS3.model.TableMetaData;
import com.roche.learn.storeDataInS3.utils.AppStringUtils;
import com.roche.learn.storeDataInS3.utils.StreamingCsvResultSetExtractor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.io.SequenceInputStream;
import java.sql.SQLException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.stream.Collectors;

import static com.roche.learn.storeDataInS3.utils.AppStringUtils.s3ObjectContentToList;


@Service
@Slf4j
public class S3Ops {

    private AmazonS3 amazonS3;
    private ApplicationProps props;
    private JdbcTemplate jdbcTemplate;
    private DbMetaData metaData;

    @Autowired
    S3Ops(AmazonS3 amazonS3, ApplicationProps props, JdbcTemplate jdbcTemplate) {
        this.amazonS3 = amazonS3;
        this.props = props;
        this.jdbcTemplate = jdbcTemplate;
    }

    public DbMetaData extractInfo() throws SQLException, IOException {
        this.metaData = DbMetaData.extractMetadata(jdbcTemplate);
        final String metaDataKey = metaData.getDataBaseName() + AppStringUtils.FILE_DELIMITER + AppStringUtils.METADATA_FILE_NAME;
        final Optional<S3ObjectSummary> objectPresent = isObjectPresent(metaData.getDataBaseName(), metaDataKey);
        if (objectPresent.isPresent()) {
            final List<String> strings = s3ObjectContentToList(getS3Object(metaDataKey));
            metaData.setAvailableArchives(strings);
        } else {
            metaData.setAvailableArchives(Collections.EMPTY_LIST);
        }
        return metaData;
    }


    public void runQuery(String tableName, String attributeName, String from, String to,boolean isDateAttribute) throws FileNotFoundException {
        to = getToValueIfEmpty(tableName, attributeName, to, isDateAttribute);
        final String rangeRecordsQuery = getRangeRecordsQuery(AppStringUtils.RANGE_RECORDS_QUERY, tableName, attributeName, from, to);
        log.info("finding data for sql query {}", rangeRecordsQuery);
        try (ByteArrayOutputStream byteArrayOs = new ByteArrayOutputStream()) {
            Void query = jdbcTemplate.query(rangeRecordsQuery, new StreamingCsvResultSetExtractor(byteArrayOs));
            final int fileVersion = getArchiveVersion(tableName);
            String fileWithFolderS3 = AppStringUtils.getFileName(metaData.getDataBaseName(), tableName, from, to, fileVersion,isDateAttribute);
            uploadToS3(fileWithFolderS3, byteArrayOs);
            final String dateRangeRecordsQuery1 = getRangeRecordsQuery(AppStringUtils.DATE_RANGE_DELETE_RECORDS_QUERY, tableName, attributeName, from, to);
            log.info("Delete query for records {}", dateRangeRecordsQuery1);
            final int update = jdbcTemplate.update(dateRangeRecordsQuery1);
            log.info("Total number of records deleted {}", update);
            syncArchiveMetaDate(metaData.getDataBaseName(), AppStringUtils.getArchiveName(tableName, from, to, fileVersion,isDateAttribute) + "\n");
        } catch (IOException e) {
            e.printStackTrace();
        }

    }

    private String getToValueIfEmpty(String tableName, String attributeName, String to, boolean isDateAttribute) {
        if(Objects.isNull(to)){
            if(isDateAttribute){
                to = LocalDateTime.now().format(DateTimeFormatter.ISO_DATE_TIME);
            }else{
                final Optional<TableMetaData> first = metaData.getTableMetaData().stream().filter(x -> x.getName().equals(tableName)).findFirst();
                final Optional<ArchiveAttribute> first1 = first.get().getArchiveAbleAttributes().stream().filter(x -> x.getName().equals(attributeName)).findFirst();
                to=String.valueOf(first1.get().getMaxValue());
            }
        }
        return to;
    }

    /**
     * archive version depends on the number of times a table archived
     *
     * @param tableName
     * @return
     * @throws IOException
     */
    private int getArchiveVersion(String tableName) throws IOException {
        String metaDataFileName = metaData.getDataBaseName() + AppStringUtils.FILE_DELIMITER + AppStringUtils.METADATA_FILE_NAME;
        final Optional<S3ObjectSummary> s3ObjectSummary = isObjectPresent(metaData.getDataBaseName(), metaDataFileName);
        if (s3ObjectSummary.isPresent()) {
            final S3Object object = getS3Object(metaDataFileName);

            List<String> archives = AppStringUtils.s3ObjectContentToList(object);

            final List<String> collect = archives.stream().filter(x -> x.contains(tableName)).collect(Collectors.toList());
            if (!collect.isEmpty()) {
                final String[] s = collect.get(collect.size() - 1).split("_");
                return Integer.valueOf(s[s.length - 1]) + 1;
            }
            return 1;
        }
        return 1;
    }


    private void uploadToS3(String folderName, ByteArrayOutputStream byteArrayOs) {
        final byte[] bytes = byteArrayOs.toByteArray();
        final ByteArrayInputStream byteArrayInputStream = new ByteArrayInputStream(bytes);
        final ObjectMetadata objectMetadata = new ObjectMetadata();
        objectMetadata.setContentLength(bytes.length);
        uploadToS3UsingInputStream(folderName, byteArrayInputStream, objectMetadata);
        log.info("back up file{} for table {} and db {}  uploaded  ", "Test file", folderName.split("_")[0], folderName.split("_")[1]);
    }

    private void uploadToS3UsingInputStream(String folderName, InputStream inputStream, ObjectMetadata objectMetadata) {
        try {
            amazonS3.putObject(new PutObjectRequest(props.getAwsServices().getBucketName(), folderName, inputStream, objectMetadata));
        } catch (AmazonServiceException ase) {
            log.info("Error while uploading file to s3: {}", ase);
            throw ase;
        } catch (SdkClientException sdk) {
            log.info("Error while uploading file to s3: {}", sdk);
            throw sdk;
        } catch (Exception e) {
            log.info("Error while uploading file to s3: {}", e);
            throw e;
        }
    }

    private String getRangeRecordsQuery(String query, String tableName, String attribute, String from, String to) {
        return String.format(query, tableName, attribute, from, to);
    }

    //TODO we can reduce the number of lookup for file present
    private boolean syncArchiveMetaDate(String dbName, String archiveNameWithVersion) throws IOException {

        String metaDataFileName = dbName + AppStringUtils.FILE_DELIMITER + AppStringUtils.METADATA_FILE_NAME;
        InputStream inputStream = new ByteArrayInputStream(archiveNameWithVersion.getBytes());

        final Optional<S3ObjectSummary> any = isObjectPresent(dbName, metaDataFileName);
        if (any.isPresent()) {
            final S3Object object = getS3Object(metaDataFileName);
            inputStream = new SequenceInputStream(object.getObjectContent(), inputStream);
        }
        final ObjectMetadata objectMetadata = new ObjectMetadata();
        objectMetadata.setContentType("text/plain");
        uploadToS3UsingInputStream(metaDataFileName, inputStream, objectMetadata);
        log.info("metadata file is appended with archive name{}", archiveNameWithVersion);
        return true;
    }

    private S3Object getS3Object(String fullFileOrFolderName) {
        return amazonS3.getObject(props.getAwsServices().getBucketName(), fullFileOrFolderName);
    }

    private Optional<S3ObjectSummary> isObjectPresent(String dbName, String fullFileOrFolderName) {
        final ObjectListing objectListing = s3ObjectListing(dbName);
        return objectListing.getObjectSummaries().stream().filter(x -> x.getKey().equals(fullFileOrFolderName)).findAny();
    }

    private ObjectListing s3ObjectListing(String dbName) {
        return amazonS3.listObjects(props.getAwsServices().getBucketName(), dbName);
    }

    /**
     * @param objectListing     s3 Object listing
     * @param extension         extension to checked if available in s3 folder suffixed with dbName param
     * @param otherThanThisFile file to be excluded in this check
     * @return
     */
    private boolean isExtensionPresentInS3(ObjectListing objectListing, String extension, String otherThanThisFile) {

        final Optional<S3ObjectSummary> any = objectListing.getObjectSummaries().stream().filter(x -> !x.getKey().contains(otherThanThisFile) && x.getKey().contains(extension))
                .findAny();
        return any.isPresent();
    }

    public boolean unArchive(String archive) throws IOException {
        if (metaData.getAvailableArchives().contains(archive)) {
            String dbName = metaData.getDataBaseName();
            final String[] s = archive.split("_");
            String tableName = s[0];
            final S3Object s3Object = getS3Object(dbName + AppStringUtils.FILE_DELIMITER + tableName + AppStringUtils.FILE_DELIMITER + archive + AppStringUtils.ARCHIVE_FILE_EXTENSION);
            final List<String> strings = s3ObjectContentToList(s3Object);
            final List<String> transform = AppStringUtils.csvListToSQLValuesList(strings);
            if(transform.size()>1 && !StringUtils.isEmpty(transform.get(1))){
                final String insertRecord = String.format(AppStringUtils.INSERT_QUERY, tableName, transform.get(0), transform.get(1));
                final int update = jdbcTemplate.update(insertRecord);
            }
            deleteArchiveFromMetaDataFile(archive, dbName);
            deleteArchiveFromFolder(dbName, tableName, archive);
            return true;
        } else {
            return false;
        }
    }

    private boolean deleteArchiveFromFolder(String dbName, String tableName, String archive) {
        String key;
        final ObjectListing objectListing = s3ObjectListing(dbName);
        if (!isExtensionPresentInS3(objectListing, AppStringUtils.ARCHIVE_FILE_EXTENSION, archive)) {
            objectListing.getObjectSummaries().stream().forEach(x -> {
                deleteObjectFromS3(x.getKey());
            });

        } else {
            key = dbName + AppStringUtils.FILE_DELIMITER + tableName + AppStringUtils.FILE_DELIMITER + archive + AppStringUtils.ARCHIVE_FILE_EXTENSION;
            deleteObjectFromS3(key);
        }
        return true;
    }

    private void deleteObjectFromS3(String key) {
        try {
            amazonS3.deleteObject(props.getAwsServices().getBucketName(), key);
        } catch (AmazonServiceException e) {
            log.info("Error while deleting {}", e);
            throw e;
        } catch (SdkClientException e) {
            log.info("Error while deleting {}", e);
            throw e;
        }
    }

    private boolean deleteArchiveFromMetaDataFile(String archive, String dbName) throws IOException {
        final S3Object s3Object1 = getS3Object(dbName + AppStringUtils.FILE_DELIMITER + AppStringUtils.METADATA_FILE_NAME);
        final List<String> strings1 = s3ObjectContentToList(s3Object1);
        StringBuilder sb = new StringBuilder();
        strings1.stream().filter(x -> !x.equals(archive)).forEach(x -> sb.append(x + "\n"));
        final ByteArrayInputStream byteArrayInputStream = new ByteArrayInputStream(sb.toString().getBytes());
        final ObjectMetadata objectMetadata = new ObjectMetadata();
        objectMetadata.setContentType("text/plain");
        uploadToS3UsingInputStream(dbName + AppStringUtils.FILE_DELIMITER + AppStringUtils.METADATA_FILE_NAME, byteArrayInputStream, objectMetadata);
        return true;
    }


}
