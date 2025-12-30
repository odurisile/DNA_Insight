import React from "react";

export const HairShapes = {
  Default: ({ color }) => (
    <div
      style={{
        width: "180px",
        height: "60px",
        backgroundColor: color,
        borderRadius: "90px 90px 40px 40px",
        position: "absolute",
        top: "20px",
        left: "40px",
      }}
    />
  ),

  Curly: ({ color }) => (
    <div
      style={{
        width: "190px",
        height: "90px",
        backgroundColor: color,
        borderRadius: "100px",
        position: "absolute",
        top: "10px",
        left: "35px",
        filter: "brightness(0.9)",
      }}
    />
  ),

  Straight: ({ color }) => (
    <div
      style={{
        width: "170px",
        height: "70px",
        backgroundColor: color,
        borderRadius: "80px 80px 20px 20px",
        position: "absolute",
        top: "15px",
        left: "45px",
      }}
    />
  ),
};
