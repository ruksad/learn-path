import React, { useState } from "react";


const Counter:React.FC= ()=>{
    const[count, setCount]= useState<number>(0);

    return (<div>
        <p>you clicked {count} times</p>
        <button onClick={()=> setCount(count+1)}>Clicke me</button>
    </div>);
};

export default Counter;