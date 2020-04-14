package com.roche.learn.storeDataInS3

import spock.lang.Specification

class StoreDataInS3ApplicationTest extends Specification {
    def "Main"() {
        given:
        when:
        def a=1
        then:
        notThrown(Exception)
    }

    def "Main 1"() {
        given:
        when:
        def a=1
        then:
        true
    }
}
