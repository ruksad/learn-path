import React, { useEffect, useState } from "react";


const Timer: React.FC = ()=>{
    const[time, setTime]= useState<number>(0);

    useEffect(()=>{
        const interval= setInterval(() => {
            setTime((prevTime)=> prevTime+1);
        }, 1000);

        return ()=> clearInterval(interval);
    }, []);

    return <div> Timer: {time} seconds</div>;

};
export default Timer;