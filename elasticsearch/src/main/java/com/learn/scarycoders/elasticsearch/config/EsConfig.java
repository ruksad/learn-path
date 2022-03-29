package com.learn.scarycoders.elasticsearch.config;

import org.elasticsearch.client.RestHighLevelClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.elasticsearch.client.ClientConfiguration;
import org.springframework.data.elasticsearch.client.RestClients;
import org.springframework.data.elasticsearch.config.AbstractElasticsearchConfiguration;
import org.springframework.data.elasticsearch.repository.config.EnableElasticsearchRepositories;

@Configuration
@EnableElasticsearchRepositories(basePackages = "com.learn.scarycoders.elasticsearch.repository")
public class EsConfig extends AbstractElasticsearchConfiguration {

    @Value("${custom.elastic-search-url}")
    private String esUrl;

    @Override
    @Bean
    public RestHighLevelClient elasticsearchClient() {
        ClientConfiguration build = ClientConfiguration.builder().connectedTo(esUrl).build();

        return RestClients.create(build).rest();
    }
}
