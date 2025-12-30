import React from "react";
import { Box, Typography, LinearProgress } from "@mui/material";

export default function HairColorChart({ data }) {
  if (!data) return null;

  const { black, brown, blonde, red } = data;

  const rows = [
    { label: "Black", value: black },
    { label: "Brown", value: brown },
    { label: "Blonde", value: blonde },
    { label: "Red", value: red },
  ];

  return (
    <Box sx={{ p: 2 }}>
      <Typography sx={{ fontWeight: 600, mb: 2 }}>Hair Color Probability</Typography>

      {rows.map((row) => (
        <Box key={row.label} sx={{ mb: 2 }}>
          <Typography sx={{ mb: 0.5 }}>{row.label} — {(row.value * 100).toFixed(1)}%</Typography>
          <LinearProgress
  variant="determinate"
  value={row.value * 100}
  sx={{
    height: 10,
    borderRadius: 5,
    opacity: 0,
    animation: "fadeBar 1s ease forwards",
    animationDelay: "0.3s",

    "@keyframes fadeBar": {
      to: { opacity: 1 },
    },

    "& .MuiLinearProgress-bar": {
      transition: "transform 1s ease",
    }
  }}
/>

        </Box>
      ))}
    </Box>
  );
}
