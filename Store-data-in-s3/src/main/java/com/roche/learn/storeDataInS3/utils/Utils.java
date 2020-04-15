package com.roche.learn.storeDataInS3.utils;

import com.roche.learn.storeDataInS3.model.DbMetaData;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.text.SimpleDateFormat;
import java.util.TimeZone;

public class Utils {


    public static DbMetaData getMaxMinValueInTables(DbMetaData dbMetaData, Connection connection) throws SQLException {

        try (Statement statement = connection.createStatement()) {
            dbMetaData.getTableMetaData().forEach(table -> {
                table.getArchiveAbleAttributes().forEach(attribute -> {
                    String qfm = String.format(AppStringUtils.QUERY_MAX, attribute.getName(), table.getName());
                    String qfMi = String.format(AppStringUtils.QUERY_MIN, attribute.getName(), table.getName());
                    try {
                        ResultSet resultSet = statement.executeQuery(qfm);
                        while (resultSet.next()) {
                            if (attribute.isDate()) {
                                final String format = getStringFromDate(resultSet);

                                attribute.setMaxDate(format);
                            } else {
                                attribute.setMaxValue(resultSet.getInt(1));
                            }
                        }
                        ResultSet resultSet1 = statement.executeQuery(qfMi);
                        while (resultSet1.next()) {
                            if (attribute.isDate()) {

                                final String format = getStringFromDate(resultSet1);

                                attribute.setMinDate(format);
                            } else {
                                attribute.setMinValue(resultSet1.getInt(1));
                            }
                        }
                    } catch (SQLException e) {
                        e.printStackTrace();
                    }
                });
            });
        }
        return dbMetaData;
    }

    private static String getStringFromDate(ResultSet resultSet) throws SQLException {
        final SimpleDateFormat df = new SimpleDateFormat(AppStringUtils.DATE_FORMAT);
        df.setTimeZone(TimeZone.getDefault());
        return null == resultSet.getTimestamp(1) ? "" : df.format(resultSet.getTimestamp(1));
    }

}
