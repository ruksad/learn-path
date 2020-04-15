package com.roche.learn.storeDataInS3.model;

import com.roche.learn.storeDataInS3.utils.Utils;
import lombok.Data;
import org.springframework.jdbc.core.JdbcTemplate;

import java.sql.Connection;
import java.sql.DatabaseMetaData;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

@Data
public class DbMetaData {
    private String dataBaseName;
    private List<TableMetaData> tableMetaData = new ArrayList<>(10);
    private List<String> availableArchives = new ArrayList<>(6);


    public static DbMetaData extractMetadata(JdbcTemplate jdbcTemplate) throws SQLException {
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
                        ArchiveAttribute archiveAttribute = ArchiveAttribute.getArchiveAttribute(column_name, false);
                        archiveAbleAttributes.add(archiveAttribute);
                    }
                    if ("91".equals(dataType)) {
                        ArchiveAttribute archiveAttribute = ArchiveAttribute.getArchiveAttribute(column_name, true);
                        archiveAbleAttributes.add(archiveAttribute);
                    }

                    if ("93".equals(dataType)) {
                        ArchiveAttribute archiveAttribute = ArchiveAttribute.getArchiveAttribute(column_name, true);
                        archiveAbleAttributes.add(archiveAttribute);
                    }
                }
                dbMetaData.getTableMetaData().add(tableMetaData);
            }

            Utils.getMaxMinValueInTables(dbMetaData, connection);
            return dbMetaData;
        }

    }
}
