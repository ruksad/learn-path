package com.learn;

import java.util.*;
import java.util.stream.Collectors;

public class Test {
    public static void main(String[] args) {
        int arr[]={1,2,3,1,2,4,5,6,7,9,12,3,1};
        Map<Integer, Integer> map=new HashMap();

        for(int i=0;i<arr.length;i++){
            map.compute(arr[i],(k,v)->(v==null)?1:++v);
            /*if(map.get(arr[i])==null){
               map.put(arr[i],1) ;
            }else{
                map.put(arr[i],map.get(arr[i])+1);
            }*/
        }
        System.out.println("map ="+map);
        List<Integer> ints=map.entrySet().stream()
                .filter(x->x.getValue()==1).map(x->x.getKey()).collect(Collectors.toList());

        System.out.println("duplicates= "+ints);
        List<Integer> collect = Arrays.stream(arr).boxed().collect(Collectors.toList());
        ints.forEach(x-> {

            collect.remove(x);

        });

        Collections.sort(collect); //,(a,b)->b-a)
        //SpringApplication.run(StoreDataInS3Application.class, args);
        System.out.println(collect);
    }
}
