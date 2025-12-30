import React, { useState } from "react";
import {
  Box,
  Typography,
  Card,
  CardContent,
  MenuItem,
  Select,
  Button,
} from "@mui/material";
import { useNavigate, useLocation } from "react-router-dom";

export default function ManualPartnerPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const mode = location.state?.mode || "fast";

  // Local trait state
  const [traits, setTraits] = useState({
    eye_color: "",
    hair_color: "",
    skin_color: "",
    freckling: "",
    tanning: "",
  });

  const handleChange = (key, value) => {
    setTraits((prev) => ({ ...prev, [key]: value }));
  };

  const canContinue =
    traits.eye_color &&
    traits.hair_color &&
    traits.skin_color &&
    traits.freckling &&
    traits.tanning;

  const handleNext = async () => {
    try {
      const res = await fetch("http://localhost:5000/manual_partner", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          traits,
          mode,
        }),
      });

      const data = await res.json();

      if (data.status === "ok") {
        navigate("/childResults", {
          state: {
            parent1: location.state.parent1,
            parent2: data.genotypes,
            mode,
          },
        });
      } else {
        alert("Error: " + data.message);
      }
    } catch (e) {
      alert("Failed: " + e);
    }
  };

  return (
    <Box
      sx={{
        width: "100%",
        minHeight: "100vh",
        bgcolor: "#fafaff",
        p: 4,
      }}
    >
      {/* Page Title */}
      <Typography variant="h4" sx={{ mb: 4, fontWeight: 700 }}>
        Enter Partner Traits Manually
      </Typography>

      {/* Form Container */}
      <Card sx={{ width: 500, borderRadius: 3, boxShadow: 3 }}>
        <CardContent sx={{ p: 4 }}>

          {/* Eye Color */}
          <Typography sx={{ mb: 1, fontWeight: 600 }}>Eye Color</Typography>
          <Select
            fullWidth
            value={traits.eye_color}
            onChange={(e) => handleChange("eye_color", e.target.value)}
            sx={{ mb: 3 }}
          >
            <MenuItem value="Blue">Blue</MenuItem>
            <MenuItem value="Green">Green</MenuItem>
            <MenuItem value="Hazel">Hazel</MenuItem>
            <MenuItem value="Brown">Brown</MenuItem>
          </Select>

          {/* Hair Color */}
          <Typography sx={{ mb: 1, fontWeight: 600 }}>Hair Color</Typography>
          <Select
            fullWidth
            value={traits.hair_color}
            onChange={(e) => handleChange("hair_color", e.target.value)}
            sx={{ mb: 3 }}
          >
            <MenuItem value="Black">Black</MenuItem>
            <MenuItem value="Brown">Brown</MenuItem>
            <MenuItem value="Blonde">Blonde</MenuItem>
            <MenuItem value="Red">Red</MenuItem>
          </Select>

          {/* Skin Tone */}
          <Typography sx={{ mb: 1, fontWeight: 600 }}>Skin Tone</Typography>
          <Select
            fullWidth
            value={traits.skin_color}
            onChange={(e) => handleChange("skin_color", e.target.value)}
            sx={{ mb: 3 }}
          >
            <MenuItem value="Light">Light</MenuItem>
            <MenuItem value="Medium">Medium</MenuItem>
            <MenuItem value="Dark">Dark</MenuItem>
          </Select>

          {/* Freckling */}
          <Typography sx={{ mb: 1, fontWeight: 600 }}>Freckling</Typography>
          <Select
            fullWidth
            value={traits.freckling}
            onChange={(e) => handleChange("freckling", e.target.value)}
            sx={{ mb: 3 }}
          >
            <MenuItem value="Low">Low</MenuItem>
            <MenuItem value="Medium">Medium</MenuItem>
            <MenuItem value="High">High</MenuItem>
          </Select>

          {/* Tanning */}
          <Typography sx={{ mb: 1, fontWeight: 600 }}>Tanning Response</Typography>
          <Select
            fullWidth
            value={traits.tanning}
            onChange={(e) => handleChange("tanning", e.target.value)}
            sx={{ mb: 3 }}
          >
            <MenuItem value="Tans easily">Tans easily</MenuItem>
            <MenuItem value="Mixed">Mixed</MenuItem>
            <MenuItem value="Burns easily">Burns easily</MenuItem>
          </Select>

        </CardContent>
      </Card>

      {/* Continue Button */}
      <Box sx={{ mt: 4 }}>
        <Button
          disabled={!canContinue}
          variant="contained"
          onClick={handleNext}
          sx={{
            px: 4,
            py: 1.5,
            fontSize: "1.1rem",
            borderRadius: 3,
            boxShadow: 3,
          }}
        >
          Continue →
        </Button>
      </Box>
    </Box>
  );
}
