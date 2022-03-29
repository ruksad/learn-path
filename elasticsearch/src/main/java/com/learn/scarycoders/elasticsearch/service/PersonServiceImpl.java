package com.learn.scarycoders.elasticsearch.service;

import com.learn.scarycoders.elasticsearch.document.Person;
import com.learn.scarycoders.elasticsearch.repository.PersonRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

@Service
public class PersonServiceImpl implements PersonService {

    private PersonRepository personRepo;

    @Autowired
    public PersonServiceImpl(PersonRepository personRepo){
        this.personRepo=personRepo;
    }

    @Override
    public void save(Person person) {
        personRepo.save(person);
    }

    @Override
    public Page<Person> findAll() {
        return personRepo.findAll(Pageable.unpaged());
    }

    @Override
    public Person findById(String id) {
        return personRepo.findById(id).orElse(null);
    }
}
