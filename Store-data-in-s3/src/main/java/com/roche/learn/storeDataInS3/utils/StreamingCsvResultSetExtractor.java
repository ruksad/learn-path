package com.roche.learn.storeDataInS3.utils;

import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.ResultSetExtractor;
import org.springframework.util.StringUtils;

import java.io.OutputStream;
import java.io.PrintWriter;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.util.Arrays;

public class StreamingCsvResultSetExtractor implements ResultSetExtractor<Void> {
    private static char DELIMITER = ',';

    private final OutputStream os;

    /**
     * @param os the OutputStream to stream the CSV to
     */
    public StreamingCsvResultSetExtractor(final OutputStream os) {
        this.os = os;
    }

    @Override
    public Void extractData(ResultSet rs) throws SQLException, DataAccessException {

        try (PrintWriter pw = new PrintWriter(os, true);) {
            ResultSetMetaData rsmd = rs.getMetaData();
            int columnCount = rsmd.getColumnCount();
            writeHeader(rsmd, columnCount, pw);
            while (rs.next()) {
                for (int i = 1; i <= columnCount; i++) {
                    Object value = rs.getObject(i);
                    if(value instanceof String && ((String) value).contains("'")){

                       value= ((String) value).replaceAll("'","''");
                    }
                    if("''".equals(value)){
                        pw.write("''");
                    }else if(null==value){
                        pw.write("null");
                    }else {
                        pw.write("'" + value.toString() + "'");
                    }

                    if (i != columnCount) {
                        pw.append(DELIMITER);
                    }
                }
                pw.println();
            }
            pw.flush();
        } catch (final SQLException e) {
            throw new RuntimeException(e);
        }
        return null;
    }


    private static void writeHeader(final ResultSetMetaData rsmd,
                                    final int columnCount, final PrintWriter pw) throws SQLException {
        for (int i = 1; i <= columnCount; i++) {
            pw.write(rsmd.getColumnName(i));
            if (i != columnCount) {
                pw.append(DELIMITER);
            }
        }
        pw.println();
    }
}
