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
import com.roche.learn.storeDataInS3.utils.StreamingCsvResultSetExtractor;
import com.roche.learn.storeDataInS3.utils.Utils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.io.SequenceInputStream;
import java.sql.Connection;
import java.sql.DatabaseMetaData;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.text.SimpleDateFormat;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.TimeZone;


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

    public Object uploadFile(String fileName, String file) {
        File file1 = new File(file);
        return amazonS3.putObject(new PutObjectRequest(props.getAwsServices().getBucketName(), "TestFile", file1));
    }


    public DbMetaData extractMetadata() throws SQLException {
        try (Connection connection = jdbcTemplate.getDataSource().getConnection()) {
            String catalog = connection.getCatalog();
            DbMetaData dbMetaData = new DbMetaData();
            dbMetaData.setDataBaseName(catalog);
            final DatabaseMetaData metaData = connection.getMetaData();

            ResultSet rs = metaData.getTables(catalog, null, null, new String[]{"TABLE"});
            while (rs.next()) {
                String tableName = rs.getString("TABLE_NAME");
                final TableMetaData tableMetaData = new TableMetaData();
                tableMetaData.setName(tableName);
                List<ArchiveAttribute> archiveAbleAttributes = tableMetaData.getArchiveAbleAttributes();
                archiveAbleAttributes.clear();
                ResultSet columns = metaData.getColumns(null, null, tableName, null);

                while (columns.next()) {
                    String column_name = columns.getString("COLUMN_NAME");
                    String is_autoIncrement = columns.getString("IS_AUTOINCREMENT");
                    String dataType = columns.getString("DATA_TYPE");
                    /**
                     * is column is auto increment and data type is date(91 code) or timestamp(93) then only columns are
                     * archive-able
                     */
                    if ("YES".equalsIgnoreCase(is_autoIncrement)) {
                        ArchiveAttribute archiveAttribute = getArchiveAttribute(column_name, false);
                        archiveAbleAttributes.add(archiveAttribute);
                    }
                    if ("91".equals(dataType)) {
                        ArchiveAttribute archiveAttribute = getArchiveAttribute(column_name, true);
                        archiveAbleAttributes.add(archiveAttribute);
                    }

                    if ("93".equals(dataType)) {
                        ArchiveAttribute archiveAttribute = getArchiveAttribute(column_name, true);
                        archiveAbleAttributes.add(archiveAttribute);
                    }
                }
                dbMetaData.getTableMetaData().add(tableMetaData);
            }

            getMaxMinValueInTables(dbMetaData, connection);
            this.metaData = dbMetaData;
            return dbMetaData;
        }

    }

    DbMetaData getMaxMinValueInTables(DbMetaData dbMetaData, Connection connection) throws SQLException {
        String queryMax = "select max( %s) from %s";
        String queryMin = "select min(%s) from %s";
        try (Statement statement = connection.createStatement()) {
            dbMetaData.getTableMetaData().forEach(table -> {
                table.getArchiveAbleAttributes().forEach(attribute -> {
                    String qfm = String.format(queryMax, attribute.getName(), table.getName());
                    String qfMi = String.format(queryMin, attribute.getName(), table.getName());
                    try {
                        ResultSet resultSet = statement.executeQuery(qfm);
                        resultSet.next();
                        if (attribute.isDate()) {
                            final String format = getStringFromDate(resultSet);

                            attribute.setMaxDate(format);
                        } else {
                            attribute.setMaxValue(resultSet.getInt(1));
                        }
                        ResultSet resultSet1 = statement.executeQuery(qfMi);
                        resultSet1.next();
                        if (attribute.isDate()) {

                            final String format = getStringFromDate(resultSet1);

                            attribute.setMinDate(format);
                        } else {
                            attribute.setMinValue(resultSet1.getInt(1));
                        }
                    } catch (SQLException e) {
                        e.printStackTrace();
                    }
                });
            });
        }
        return dbMetaData;
    }

    private String getStringFromDate(ResultSet resultSet) throws SQLException {
        final SimpleDateFormat df = new SimpleDateFormat(Utils.DATE_FORMAT);
        df.setTimeZone(TimeZone.getDefault());
        return df.format(resultSet.getTimestamp(1));
    }

    private ArchiveAttribute getArchiveAttribute(String column_name, boolean b) {
        ArchiveAttribute archiveAttribute = new ArchiveAttribute();
        archiveAttribute.setDate(b);
        archiveAttribute.setName(column_name);
        return archiveAttribute;
    }


    public void runQuery(String tableName, String attributeName, LocalDateTime from, LocalDateTime to) throws FileNotFoundException {
        final String dateRangeRecordsQuery = getDateRangeRecordsQuery(Utils.DATE_RANGE_RECORDS_QUERY, tableName, attributeName, from, to);
        try (ByteArrayOutputStream byteArrayOs = new ByteArrayOutputStream()) {
            Void query = jdbcTemplate.query(dateRangeRecordsQuery, new StreamingCsvResultSetExtractor(byteArrayOs));
            String folderName = getFileName(tableName, from, to, 1);
            uploadToS3(folderName, byteArrayOs);
            final String dateRangeRecordsQuery1 = getDateRangeRecordsQuery(Utils.DATE_RANGE_DELETE_RECORDS_QUERY, tableName, attributeName, from, to);
            final int update = jdbcTemplate.update(dateRangeRecordsQuery1);
            syncArchiveMetaDate(metaData.getDataBaseName(),getArchiveName(tableName,from,to,1));
        } catch (IOException e) {
            e.printStackTrace();
        }

    }

    private String getFileName(String tableName, LocalDateTime from, LocalDateTime to, int version) {
        return metaData.getDataBaseName() + "/" + tableName + "/" + getDateFormatted(from, to, version) + ".csv";
    }

    private String getDateFormatted(LocalDateTime from, LocalDateTime to, int version) {
        return from.format(DateTimeFormatter.ofPattern("yyyy-mm-dd")) + "_"
                + to.format(DateTimeFormatter.ofPattern("yyyy-mm-dd")) + "_" + version;
    }

    private String getArchiveName(String tableName, LocalDateTime from, LocalDateTime to, int version){
        return  tableName + "_" + getDateFormatted(from,to,version);
    }
    private void uploadToS3(String folderName, ByteArrayOutputStream byteArrayOs) {
        final byte[] bytes = byteArrayOs.toByteArray();
        final ByteArrayInputStream byteArrayInputStream = new ByteArrayInputStream(bytes);
        final ObjectMetadata objectMetadata = new ObjectMetadata();
        objectMetadata.setContentLength(bytes.length);
        try {
            amazonS3.putObject(new PutObjectRequest(props.getAwsServices().getBucketName(), folderName + "/TestFile2.csv", byteArrayInputStream, objectMetadata));
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
        log.info("back up file{} for table {} and db {}  uploaded  ", "Test file", folderName.split("_")[0], folderName.split("_")[1]);
    }

    public DbMetaData getMetaData() {
        return metaData;
    }

    private String getDateRangeRecordsQuery(String query, String tableName, String attribute, LocalDateTime from, LocalDateTime to) {
        if (Objects.isNull(to)) {
            to = LocalDateTime.now();
        }
        return String.format(query, tableName, attribute, from.toString(), to.toString());
    }


    private boolean syncArchiveMetaDate(String dbName, String archiveNameWithVersion) {

        String metaDataFileName = dbName + "/metadata.txt";
        final ObjectListing objectListing = amazonS3.listObjects(props.getAwsServices().getBucketName(), dbName);
        final Optional<S3ObjectSummary> any = objectListing.getObjectSummaries().stream().filter(x -> x.getKey().equals(metaDataFileName)).findAny();
        InputStream inputStream = new ByteArrayInputStream(archiveNameWithVersion.getBytes());

        if (any.isPresent()) {
            final S3Object object = amazonS3.getObject(props.getAwsServices().getBucketName(), metaDataFileName);
            inputStream = new SequenceInputStream(object.getObjectContent(), inputStream);
        }
        final ObjectMetadata objectMetadata = new ObjectMetadata();
        objectMetadata.setContentType("text/plain");
        amazonS3.putObject(new PutObjectRequest(props.getAwsServices().getBucketName(), metaDataFileName, inputStream, objectMetadata));
        return true;
    }
}
