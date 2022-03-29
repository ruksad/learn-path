package com.learn.scarycoders.elasticsearch.service;

import com.learn.scarycoders.elasticsearch.document.Person;
import org.springframework.data.domain.Page;

public interface PersonService {
    void save(Person person);
    Page<Person> findAll();
    Person findById(String id);
}
