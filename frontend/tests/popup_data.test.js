import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";

import { getFormattedData } from "../src/popup_data";

const correctMarkerData = {
  title: "Most Grunwaldzki",
  position: [51.1095, 17.0525],
  subtitle: "big bridge",
  data: {
    length: 112.5,
    accessible_by: ["pedestrians", "cars"],
    website: { type: "hyperlink", value: "https://www.google.com" },
    websiteWithDisplayValue: { type: "hyperlink", value: "https://www.google.com", displayValue: "testWebsite" },
    unknownDataType: { type: "unknown", value: "example value for unknown data type" },
  },
};

const dataKeys = Object.keys(correctMarkerData.data);

describe("should render marker popup correctly", () => {
  it("should render marker popup name", () => {
    expect(screen.getByText(correctMarkerData.title)).toBeInTheDocument();
  });

  it("should render marker popup subtitle", () => {
    expect(screen.getByText(/big bridge/i)).toBeInTheDocument();
  });

  describe("should render data", () => {
    it("should render data keys", () => {
      dataKeys.forEach(key => {
        expect(screen.getByText(key)).toBeInTheDocument();
      });
    });

    it("should render data with primitive value", () => {
      expect(screen.getByText(/: 112\.5/i)).toBeInTheDocument();
    });

    it("should render data with array value", () => {
      expect(screen.getByText(/: pedestrians, cars/i)).toBeInTheDocument();
    });

    describe("should render complex data", () => {
      it("should display `displayValue` if given", () => {
        expect(screen.getByRole("link", { name: "testWebsite" })).toBeInTheDocument();
      });

      it("should render hyperlink", () => {
        expect(screen.getByRole("link", { name: "https://www.google.com" })).toBeInTheDocument();
      });

      it("should render unknown data type as text", () => {
        expect(screen.getByText(/: example value for unknown data type/i)).toBeInTheDocument();
      });
    });
  });
});

beforeEach(() => {
  render(getFormattedData(correctMarkerData));
});
