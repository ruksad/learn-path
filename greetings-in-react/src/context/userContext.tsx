
import React, {useContext, createContext, ReactNode} from "react";

interface User {
    name:string;
}
const UserContext= createContext<User| undefined> (undefined);

interface UserProviderProps{
    children: ReactNode;
}

export const UserProvider: React.FC<UserProviderProps>= ({children})=>{
    const user:User ={name:'Siddiqui'};
    return <UserContext.Provider value={user}>{children}</UserContext.Provider>
};

export const UserUser= (): User =>{
    let context= useContext(UserContext);
    if(!context){
        throw new Error('User must be used within user provider');
    }
    return context; 
};