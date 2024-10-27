import React from "react";
import { UserUser } from "../context/userContext";

const UserInfo: React.FC = ()=>{
    let user= UserUser();
    return <div>User: {user.name}</div>

}
export default UserInfo;