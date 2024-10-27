import React from 'react';
import './App.css';
import { UserProvider, UserUser } from './context/userContext';
import Greeting from './components/greeting';
import Counter from './components/counter';
import Timer from './components/timer';
import UserInfo from './components/userInfo';
import { BrowserRouter as Router ,Routes, Route} from 'react-router-dom';

/* const UserInfo: React.FC = () => {
  let user = userUser();
  return <div>User: {user.name}</div>;
}
 */
const Home: React.FC= ()=>{
  return (<div>
    <Greeting name="Ruksad"/>
    <Counter/>
  </div>)
};

const About: React.FC= ()=>{
  return (<div>
    <Timer/>
    <UserInfo/>
  </div>)
};

const App: React.FC = () => {


  return (
    <UserProvider>
      <Router>
        <Routes>
          <Route path='/' element={<Home/>}/>
          <Route path='/about' element= {<About/>}/>
        </Routes>
      </Router>
    </UserProvider>);
}

export default App;
