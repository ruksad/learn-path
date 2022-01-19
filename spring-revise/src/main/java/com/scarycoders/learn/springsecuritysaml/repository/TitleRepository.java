package com.scarycoders.learn.springsecuritysaml.repository;

import com.scarycoders.learn.springsecuritysaml.model.Title;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface TitleRepository extends CrudRepository<Title,String> {
}
