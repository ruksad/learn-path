package com.learn.scarycoders.elasticsearch.controller;

import com.learn.scarycoders.elasticsearch.document.Person;
import com.learn.scarycoders.elasticsearch.service.PersonService;
import org.apache.http.HttpStatus;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/es/persons")
public class PersonController {

    private PersonService personService;

    @Autowired
    public PersonController(PersonService personService){
        this.personService=personService;
    }

    @PostMapping(path = "/person", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<String> save(@RequestBody final Person person){
        personService.save(person);
        return ResponseEntity.status(HttpStatus.SC_CREATED).body("Entity Saved");
    }

    @GetMapping(path = "/person/{id}",produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Person> findById(@PathVariable("id") String id){
        Person byId = personService.findById(id);
        return ResponseEntity.ok(byId);
    }

    @GetMapping(path = "/all",produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Page<Person>> findAll(){
        Page<Person> all = personService.findAll();
        return ResponseEntity.ok(all);
    }
}
