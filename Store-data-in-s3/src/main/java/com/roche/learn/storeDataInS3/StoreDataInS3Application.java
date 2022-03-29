package com.roche.learn.storeDataInS3;

import com.amazonaws.auth.AWSCredentialsProvider;
import com.amazonaws.services.s3.AmazonS3;
import com.amazonaws.services.s3.AmazonS3ClientBuilder;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@SpringBootApplication
public class StoreDataInS3Application {

    public static void main(String[] args) {
        SpringApplication.run(StoreDataInS3Application.class, args);
    }

    @Bean
    public AmazonS3 amazonS3Client(AWSCredentialsProvider awsCredentialsProvider, @Value("${cloud.aws.region.static}") String region) {
        return AmazonS3ClientBuilder.standard().withCredentials(awsCredentialsProvider).withRegion(region).build();
    }
}
