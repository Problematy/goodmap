import React, { useState } from "react";
import { Map } from "./TabComponent/Tab1/Map";
import { Sidebar } from "./TabComponent/Tab1/Sidebar";
import { Tabs } from "./TabComponent/Tabs";
import { Form } from "./TabComponent/Tab1/Form";

const setComponent = (tab) => {
  switch (tab) {
    case 1:
      return (
        <>
          <div className="map-tab_container">
            <Sidebar />
            <Map />
          </div>
          <Form />
        </>
      );
    case 2:
      return <div>"On-line Collection - Redirected"</div>;
    case 3:
      return <div>'FAQ content'</div>;
    case 4:
      return <div>"About Us"</div>;
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
