package com.learn.scarycoders.elasticsearch.repository;

import com.learn.scarycoders.elasticsearch.document.Person;
import org.springframework.data.elasticsearch.repository.ElasticsearchRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface PersonRepository extends ElasticsearchRepository<Person,String> {
}
