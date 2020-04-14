package com.roche.learn.storeDataInS3.utils;

public class Utils {

    public static String DATE_RANGE_RECORDS_QUERY= "SELECT * FROM %s WHERE %s  BETWEEN '%s' AND '%s';";
    public static String DATE_FORMAT= "yyyy-MM-dd'T'HH:mm'Z'";
    public static String DATE_RANGE_DELETE_RECORDS_QUERY= "DELETE FROM %s WHERE %s BETWEEN '%s' AND '%s'";
}
