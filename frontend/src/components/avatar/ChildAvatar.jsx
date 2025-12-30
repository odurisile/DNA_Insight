import React from "react";
import { Box } from "@mui/material";
import { skinColors } from "./SkinTones";
import { eyeColors } from "./EyeColors";
import { hairColors } from "./HairColors";
import { HairShapes } from "./HairShapes";

export default function ChildAvatar({ traits }) {
  if (!traits) return null;

  const skin = skinColors[traits.skin_color?.result] || skinColors.Medium;
  const eye = eyeColors[traits.eye_color?.result] || eyeColors.Brown;
  const hairColor = hairColors[traits.hair_color?.result] || hairColors.Brown;
  const HairShape = HairShapes["Default"];

  return (
    <Box
      sx={{
        width: 260,
        height: 260,
        bgcolor: "#fff",
        borderRadius: 4,
        boxShadow: 4,
        position: "relative",
        overflow: "hidden",

        // Animations:
        opacity: 0,
        transform: "translateY(-20px)",
        animation: "avatarFade 0.9s ease forwards",

        "@keyframes avatarFade": {
          to: {
            opacity: 1,
            transform: "translateY(0)",
          },
        },
      }}
    >
      {/* Face */}
      <Box
        sx={{
          width: "160px",
          height: "180px",
          bgcolor: skin,
          borderRadius: "80px",
          position: "absolute",
          top: "40px",
          left: "50px",
        }}
      />

      {/* Eyes */}
      <Box
        sx={{
          width: "32px",
          height: "18px",
          bgcolor: eye,
          borderRadius: "50%",
          position: "absolute",
          top: "110px",
          left: "80px",
        }}
      />
      <Box
        sx={{
          width: "32px",
          height: "18px",
          bgcolor: eye,
          borderRadius: "50%",
          position: "absolute",
          top: "110px",
          left: "150px",
        }}
      />

      {/* Hair */}
      <HairShape color={hairColor} />
    </Box>
  );
}
