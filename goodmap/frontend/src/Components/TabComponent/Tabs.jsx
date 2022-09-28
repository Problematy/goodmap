import React from "react";
import { button1, button2, button3, button4 } from "../../dictionary";
import clsx from "clsx";

const buttons = [button1, button2, button3, button4];

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
  );
};

const Login = () => {
  return <i className="fa fa-solid fa-user user"></i>;
};

const LanguagesList = () => {
  return (
    <ul className="lang-list">
      <li className="lang-list__elem">PL </li>
      <li className="lang-list__elem">EN </li>
      <li className="lang-list__elem lang-elem__last">UK </li>
    </ul>
  );
};

const Languages = () => {
  return (
    <div className="lang-container">
      <LanguagesList />
      <Login />
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
