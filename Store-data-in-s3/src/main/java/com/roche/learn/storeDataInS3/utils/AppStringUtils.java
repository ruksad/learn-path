package com.roche.learn.storeDataInS3.utils;

import com.amazonaws.services.s3.model.S3Object;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

public class AppStringUtils {

    public static String RANGE_RECORDS_QUERY = "SELECT * FROM %s WHERE %s  BETWEEN '%s' AND '%s';";
    public static String DATE_FORMAT = "yyyy-MM-dd'T'HH:mm'Z'";
    public static String DATE_RANGE_DELETE_RECORDS_QUERY = "DELETE FROM %s WHERE %s BETWEEN '%s' AND '%s'";

    public static String INSERT_QUERY = "INSERT INTO %s %s VALUES %s";
    public static String METADATA_FILE_NAME = "metadata.txt";
    public static String FILE_DELIMITER = "/";
    public static String ARCHIVE_FILE_EXTENSION = ".csv";

    public static String QUERY_MAX = "select max( %s) from %s";
    public static String QUERY_MIN = "select min(%s) from %s";

    public static List<String> s3ObjectContentToList(S3Object object) throws IOException {
        final BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(object.getObjectContent()));
        String line;
        List<String> archives = new ArrayList<>();
        while ((line = bufferedReader.readLine()) != null) {
            archives.add(line);
        }
        return archives;
    }

    public static String getFileName(String dbName, String tableName, String from, String to, int version, boolean isDateAttribute) {
        return dbName + "/" + tableName + "/" + getArchiveName(tableName,from,to,version,isDateAttribute)+AppStringUtils.ARCHIVE_FILE_EXTENSION;
    }

    private static String getDateFormatted(String from, String to, int version) {
        return LocalDateTime.parse(from,DateTimeFormatter.ISO_DATE_TIME).format(DateTimeFormatter.ofPattern("yyyy-mm-dd")) + "_"
                + LocalDateTime.parse(to,DateTimeFormatter.ISO_DATE_TIME).format(DateTimeFormatter.ofPattern("yyyy-mm-dd")) + "_" + version;
    }

    public static String getArchiveName(String tableName, String from, String to, int version,boolean isDateAttribute) {
        String archiveName=tableName + "_" ;
        if(isDateAttribute){
            return archiveName+ getDateFormatted(from, to, version);
        }else{
            return archiveName+"IDRANGE_"+from+"_"+to+"_"+version;
        }
    }

    public static List<String> csvListToSQLValuesList(List<String> strings) {
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
