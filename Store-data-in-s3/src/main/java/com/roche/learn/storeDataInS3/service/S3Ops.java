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

import java.io.BufferedReader;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.SequenceInputStream;
import java.sql.Connection;
import java.sql.DatabaseMetaData;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.text.SimpleDateFormat;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.TimeZone;
import java.util.stream.Collectors;


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
        if (Objects.isNull(to)) {
            to = LocalDateTime.now();
        }
        final String dateRangeRecordsQuery = getDateRangeRecordsQuery(Utils.DATE_RANGE_RECORDS_QUERY, tableName, attributeName, from, to);
        try (ByteArrayOutputStream byteArrayOs = new ByteArrayOutputStream()) {
            Void query = jdbcTemplate.query(dateRangeRecordsQuery, new StreamingCsvResultSetExtractor(byteArrayOs));
            final int fileVersion = getFileVersion(tableName);
            String fileWithFolderS3 = getFileName(tableName, from, to, fileVersion);
            uploadToS3(fileWithFolderS3, byteArrayOs);
            final String dateRangeRecordsQuery1 = getDateRangeRecordsQuery(Utils.DATE_RANGE_DELETE_RECORDS_QUERY, tableName, attributeName, from, to);
            final int update = jdbcTemplate.update(dateRangeRecordsQuery1);

            syncArchiveMetaDate(metaData.getDataBaseName(), getArchiveName(tableName, from, to, fileVersion) + "\n");
        } catch (IOException e) {
            e.printStackTrace();
        }

    }

    private int getFileVersion(String tableName) throws IOException {
        String metaDataFileName = metaData.getDataBaseName() + "/metadata.txt";
        final Optional<S3ObjectSummary> s3ObjectSummary = isObjectPresent(metaData.getDataBaseName(), metaDataFileName);
        if (s3ObjectSummary.isPresent()) {
            final S3Object object = getS3Object(metaDataFileName);

            List<String> archives = inputStreamToList(object);

            final List<String> collect = archives.stream().filter(x -> x.contains(tableName)).collect(Collectors.toList());
            if (!collect.isEmpty()) {
                final String[] s = collect.get(collect.size()-1).split("_");
                return Integer.valueOf(s[s.length - 1]) + 1;
            }
            return 1;
        }
        return 1;
    }

    private List<String> inputStreamToList(S3Object object) throws IOException {
        final BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(object.getObjectContent()));
        String line;
        List<String> archives = new ArrayList<>();
        while ((line = bufferedReader.readLine()) != null) {
            archives.add(line);
        }
        return archives;
    }

    private String getFileName(String tableName, LocalDateTime from, LocalDateTime to, int version) {
        return metaData.getDataBaseName() + "/" + tableName + "/" + tableName + "_" + getDateFormatted(from, to, version) + ".csv";
    }

    private String getDateFormatted(LocalDateTime from, LocalDateTime to, int version) {
        return from.format(DateTimeFormatter.ofPattern("yyyy-mm-dd")) + "_"
                + to.format(DateTimeFormatter.ofPattern("yyyy-mm-dd")) + "_" + version;
    }

    private String getArchiveName(String tableName, LocalDateTime from, LocalDateTime to, int version) {
        return tableName + "_" + getDateFormatted(from, to, version);
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

    public DbMetaData getMetaData() {
        return metaData;
    }

    private String getDateRangeRecordsQuery(String query, String tableName, String attribute, LocalDateTime from, LocalDateTime to) {

        return String.format(query, tableName, attribute, from.toString(), to.toString());
    }

    //TODO we can reduce the number of lookup for file present
    private boolean syncArchiveMetaDate(String dbName, String archiveNameWithVersion) throws IOException {

        String metaDataFileName = dbName + "/metadata.txt";
        final Optional<S3ObjectSummary> any = isObjectPresent(dbName, metaDataFileName);
        InputStream inputStream = new ByteArrayInputStream(archiveNameWithVersion.getBytes());

        if (any.isPresent()) {
            final S3Object object = getS3Object(metaDataFileName);
            inputStream = new SequenceInputStream(object.getObjectContent(), inputStream);
        }
        final ObjectMetadata objectMetadata = new ObjectMetadata();
        objectMetadata.setContentType("text/plain");
        uploadToS3UsingInputStream( metaDataFileName, inputStream, objectMetadata);
        return true;
    }

    private S3Object getS3Object(String fullFileOrFolderName) {
        return amazonS3.getObject(props.getAwsServices().getBucketName(), fullFileOrFolderName);
    }

    private Optional<S3ObjectSummary> isObjectPresent(String dbName, String fullFileOrFolderName) {
        final ObjectListing objectListing = amazonS3.listObjects(props.getAwsServices().getBucketName(), dbName);
        return objectListing.getObjectSummaries().stream().filter(x -> x.getKey().equals(fullFileOrFolderName)).findAny();
    }

    public void unArchive(String archive) throws IOException {
        String dbName = metaData.getDataBaseName();
        final String[] s = archive.split("_");
        String tableName = s[0];
        final S3Object s3Object = getS3Object(dbName + "/" + tableName + "/" + archive + ".csv");
        final List<String> strings = inputStreamToList(s3Object);
        final List<String> transform = transform(strings);
        final String insertRecord = String.format(Utils.INSERT_QUERY, tableName, transform.get(0), transform.get(1));
        final int update = jdbcTemplate.update(insertRecord);
        final S3Object s3Object1 = getS3Object(dbName + "/" + "metadata.txt");
        final List<String> strings1 = inputStreamToList(s3Object1);
        StringBuilder sb=new StringBuilder();
        strings1.stream().filter(x->!x.equals(archive)).forEach(x->sb.append(x+"\n"));
        final ByteArrayInputStream byteArrayInputStream = new ByteArrayInputStream(sb.toString().getBytes());
        final ObjectMetadata objectMetadata = new ObjectMetadata();
        objectMetadata.setContentType("text/plain");
        uploadToS3UsingInputStream(dbName+"/metadata.txt",byteArrayInputStream,objectMetadata);
    }

    private List<String> transform(List<String> strings) {
        List<String> strForSql = new ArrayList<>(4);
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < strings.size(); i++) {
            if (i == 0) {
                strForSql.add("(" + strings.get(i) + ")");
            } else {
                if (i == strings.size() - 1) {
                    sb.append("(" + strings.get(i) + ");");
                    continue;
                }
                sb.append("(" + strings.get(i) + "),");
            }

        }
        strForSql.add(sb.toString());
        return strForSql;
    }
}
