package com.learn.scarycoders.elasticsearch.helper;

import org.springframework.core.io.ClassPathResource;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;


public class MappingUtils {

    public static String loadAsString(final String path){
        try {
            File file = new ClassPathResource(path).getFile();
            return new String(Files.readAllBytes(file.toPath()));
        } catch (IOException e) {
            e.printStackTrace();
            return null;
        }

    }
}
