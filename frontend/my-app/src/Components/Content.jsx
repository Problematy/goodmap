import React, { useState } from "react";
import { Map } from "./TabComponent/Tab1/Map";
import { Sidebar } from "./TabComponent/Tab1/Sidebar";
import { Tabs } from "./TabComponent/Tabs";
import { Form } from "./TabComponent/Tab1/Form";

const TabAbout = () => {
  return <div>"About Us"</div>;
};

const TabFAQ = () => {
  return <div>'FAQ content'</div>;
};

const TabCollection = () => {
  return <div>"On-line Collection - Redirected"</div>;
};

const TabMap = () => {
  return (
    <>
      <div className="map-tab_container">
        <Sidebar />
        <Map />
      </div>
      <Form />
    </>
  );
};

const setComponent = (tab) => {
  switch (tab) {
    case 1:
      return <TabMap />;
    case 2:
      return <TabCollection />;
    case 3:
      return <TabFAQ />;
    case 4:
      return <TabAbout />;
    default:
      return null;
  }
};

const Content = () => {
  const [tab, setTab] = useState(1);

  const handleClick = (id) => () => {
    setTab(id);
    console.log(id);
  };

  return (
    <>
      <Tabs handleClick={handleClick} tab={tab} />
      {setComponent(tab)}
    </>
  );
};

export { Content };
