import React from "react";
import "@trendmicro/react-sidenav/dist/react-sidenav.css";
import SideNav, {
  Toggle,
  Nav,
  NavItem,
  NavIcon,
  NavText,
} from "@trendmicro/react-sidenav";

const Sidebar = () => {
  return (
    <SideNav
      className="sidebar-container"
      onSelect={(selected) => {
        // Add your code here
      }}
    >
      <SideNav.Toggle />
      <SideNav.Nav defaultSelected="home">
        <NavItem eventKey="conditions">
          <NavIcon>
            <i
              className="fa fa-solid fa-sparkles"
              style={{ fontSize: "1.75em" }}
            />
          </NavIcon>
          <NavText>Condition</NavText>
        </NavItem>
        <NavItem eventKey="type">
          <NavIcon>
            <i
              className="fa fa-solid fa-list-check"
              style={{ fontSize: "1.75em" }}
            />
          </NavIcon>
          <NavText>Type</NavText>
        </NavItem>
        <NavItem eventKey="gender">
          <NavIcon>
            <i className="fa fa-solid fa-user" style={{ fontSize: "1.75em" }} />
          </NavIcon>
          <NavText>Gender</NavText>
        </NavItem>
        <NavItem eventKey="place">
          <NavIcon>
            <i className="fa fa-fw fa-home" style={{ fontSize: "1.75em" }} />
          </NavIcon>
          <NavText>Type of Place</NavText>
        </NavItem>
      </SideNav.Nav>
    </SideNav>
  );
};

export { Sidebar };
