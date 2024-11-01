import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';


  /**
   * Function conponent not extending React.Component
   * @param {*} props 
   * @returns 
   */
  function Square(props){
    return (
      <button className='square' onClick={props.onClick}>
        {props.value}
      </button>
    )
  }
  
  class Board extends React.Component {
    /* constructor(props){
      super(props);
      this.state= {
        squares: Array(9).fill(null),
        xIsNext: true,
      }
    } */

    renderSquare(i) {
      return (
        <Square
          value={this.props.squares[i]}
          onClick={() => this.props.ruksad(i)}
        />
      );
    }
   

    render() {
      return (
        <div>
          <div className="board-row">
            {this.renderSquare(0)}
            {this.renderSquare(1)}
            {this.renderSquare(2)}
          </div>
          <div className="board-row">
            {this.renderSquare(3)}
            {this.renderSquare(4)}
            {this.renderSquare(5)}
          </div>
          <div className="board-row">
            {this.renderSquare(6)}
            {this.renderSquare(7)}
            {this.renderSquare(8)}
          </div>
        </div>
      );
    }
  }
  
  class Game extends React.Component {
    constructor(props){
      super(props);
      this.state={
        history: [ {squares: Array(9).fill(null)},],
        xIsNext:true,
        stepNumber:0,
      };
    }

    render() {
      let history= this.state.history;
      let current= history[this.state.stepNumber];
      let winner= calculateWinner(current.squares);
      let status;

      let moves= history.map((step,move)=>{
          const desc=  move ? "Go to move #" + move:" Go to game start";

        return (<li key={move}>
          <button onClick={()=> this.jumpTo(move)}> {desc}</button>
        </li>);
      });


      if (winner) {
        status = 'Winner: ' + winner;
      } else {
        status = 'Next player: ' + (this.state.xIsNext ? 'X' : 'O');
      }

      return (
        <div className="game">
          <div className="game-board">
            <Board  squares={current.squares} ruksad={(i)=>this.handleSquareClick(i)}/>
          </div>
          <div className="game-info">
            <div>{status}</div>
            <ol>{moves}</ol>
          </div>
        </div>
      );
    }

    handleSquareClick(i) {
      let history=this.state.history.slice(0,this.state.stepNumber+1);
      let current= history[history.length-1];

      let squares = current.squares.slice();
      if (calculateWinner(squares) || squares[i]) {
        return;
      }

      squares[i] = this.state.xIsNext ? "X" : "O";
      this.setState({ history: history.concat([{squares: squares,}]), stepNumber: history.length,xIsNext: !this.state.xIsNext });
    }

    jumpTo(step){
      this.setState({
        stepNumber: step,
        xIsNext: (step % 2) === 0,
      })
    }
  }
  
  function calculateWinner(squares){
    let lines=[
      [0, 1, 2],
      [3, 4, 5],
      [6, 7, 8],
      [0, 3, 6],
      [1, 4, 7],
      [2, 5, 8],
      [0, 4, 8],
      [2, 4, 6],
    ];

    for(let i=0;i<lines.length;i++){
      let [a,b,c]= lines[i];
      if(squares[a] && squares[a]===squares[b] && squares[a]===squares[c]){
        return squares[a];
      }
    }
    return null;
  }
  // ========================================

  const root= ReactDOM.createRoot(document.getElementById("root"));
  root.render(<Game />)