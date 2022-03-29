package com.learn.scarycoders.elasticsearch.service;

import com.learn.scarycoders.elasticsearch.helper.Indices;
import com.learn.scarycoders.elasticsearch.helper.MappingUtils;
import lombok.extern.slf4j.Slf4j;
import org.elasticsearch.client.RequestOptions;
import org.elasticsearch.client.RestHighLevelClient;
import org.elasticsearch.client.indices.CreateIndexRequest;
import org.elasticsearch.client.indices.GetIndexRequest;
import org.elasticsearch.common.xcontent.XContentType;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import javax.annotation.PostConstruct;
import java.io.IOException;
import java.util.List;
import java.util.Objects;

@Service
@Slf4j
public class IndexService {

    private final List<String> INDICES_TO_CREATE = List.of(Indices.VEHICLE_INDEX);
    private final RestHighLevelClient client;

    @Autowired
    public IndexService(RestHighLevelClient restHighLevelClient) {
        this.client = restHighLevelClient;
    }

    @PostConstruct
    public void tryToCreateIndices() {
        final String indexSetting = MappingUtils.loadAsString("static/es-settings.json");
        for (String indexName : INDICES_TO_CREATE) {
            try {
                boolean exists = client
                        .indices()
                        .exists(new GetIndexRequest(indexName), RequestOptions.DEFAULT);
                if (exists)
                    continue;
                String indexMapping = MappingUtils.loadAsString("/static/mappings/" + indexName + ".json");
                if (Objects.isNull(indexMapping) || Objects.isNull(indexSetting)) {
                    log.error("error in loading index meta data");
                    continue;
                }
                CreateIndexRequest createIndexRequest = new CreateIndexRequest(indexName);
                createIndexRequest.settings(indexSetting, XContentType.JSON);
                createIndexRequest.mapping(indexMapping,XContentType.JSON);


            } catch (IOException e) {
                log.error(e.getMessage());
            }
        }
    }
}
