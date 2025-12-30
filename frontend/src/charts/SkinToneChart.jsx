import React from "react";
import { Box, Typography, LinearProgress } from "@mui/material";

export default function SkinToneChart({ data }) {
  if (!data) return null;

  const { very_light, light, medium, dark, very_dark } = data;

  const rows = [
    { label: "Very Light", value: very_light },
    { label: "Light", value: light },
    { label: "Medium", value: medium },
    { label: "Dark", value: dark },
    { label: "Very Dark", value: very_dark },
  ];

  return (
    <Box sx={{ p: 2 }}>
      <Typography sx={{ fontWeight: 600, mb: 2 }}>Skin Tone Probability</Typography>

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
