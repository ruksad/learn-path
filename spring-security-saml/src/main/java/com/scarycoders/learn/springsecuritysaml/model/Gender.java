package com.scarycoders.learn.springsecuritysaml.model;

public enum Gender {
    MALE("MALE"),FEMALE("FEMALE");
    private String gender;
    Gender(String gender){
        this.gender=gender;
    }

    public String getGender() {
        return gender;
    }

}
