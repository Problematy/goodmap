import React from "react";
import { button1, button2, button3, button4 } from "../../dictionary";
import clsx from "clsx";

const buttons = [button1, button2, button3, button4];

// const ButtonAbout = ({ handleClick, num }) => {
//   return (
//     <button
//       href="#"
//       className="list-elem list-elem__last"
//       onClick={handleClick(num)}
//     >
//       {button4[1]}
//     </button>
//   );
// };

// const ButtonFAQ = ({ handleClick, num }) => {
//   return (
//     <button href="#" className="list-elem" onClick={handleClick(num)}>
//       FAQ
//     </button>
//   );
// };

// const ButtonCollections = ({ handleClick, num }) => {
//   return (
//     <button href="#" className="list-elem" onClick={handleClick(num)}>
//       {button2[1]}
//     </button>
//   );
// };

// const ButtonMap = ({ handleClick, num }) => {
//   return (
//     <button className="list-elem" onClick={handleClick(num)}>
//       {button1[1]}
//     </button>
//   );
// };

const List = ({ handleClick, tab }) => {
  return (
    <ul className="list-container">
      {buttons.map((elem, id) => {
        return (
          <button
            key={id}
            className={clsx("list-elem", {
              active: id + 1 === tab,
            })}
            onClick={handleClick(id + 1)}
          >
            {elem[1]}
          </button>
        );
      })}
    </ul>
    // <ul className="list-container">
    //   <ButtonMap handleClick={handleClick} num={1} />
    //   <ButtonCollections handleClick={handleClick} num={2} />
    //   <ButtonFAQ handleClick={handleClick} num={3} />
    //   <ButtonAbout handleClick={handleClick} num={4} />
    // </ul>
  );
};

const Languages = () => {
  return (
    <div className="lang-container">
      <ul className="lang-list">
        <li className="lang-list__elem">PL </li>
        <li className="lang-list__elem">EN </li>
        <li className="lang-list__elem lang-elem__last">UK </li>
      </ul>
      <i className="fa fa-solid fa-user user"></i>
    </div>
  );
};

const Logo = () => {
  return <div className="title-page">Placeholder for Logo</div>;
};

const Tabs = ({ handleClick, tab }) => {
  return (
    <>
      <div className="tabs-container">
        <Logo />
        <nav>
          <Languages />
          <List handleClick={handleClick} tab={tab} />
        </nav>
      </div>
    </>
  );
};

export { Tabs };
