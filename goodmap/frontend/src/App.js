import "./App.css";
import React, { useState, useEffect } from "react";
import { Content } from "./Components/Content";

function App() {
  const [data, setData] = useState();

  useEffect(() => {
    fetch("/api/data")
      .then((res) => res.json())
      .then((data) => (setData(data), console.log(data)));
  });
  return (
    <div className="App">
      <header className="header-container">
        <Content />
      </header>
    </div>
  );
}

export default App;
