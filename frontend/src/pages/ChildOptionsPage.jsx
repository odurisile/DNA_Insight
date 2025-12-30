import React, { useState } from "react";
import { Box, Card, CardActionArea, CardContent, Typography, Switch } from "@mui/material";
import { useNavigate } from "react-router-dom";

export default function ChildOptionsPage() {
  const navigate = useNavigate();
  
  const [mode, setMode] = useState("fast");

  const handleModeToggle = () => {
    setMode((m) => (m === "fast" ? "hirisplex" : "fast"));
  };

  return (
    <Box 
      sx={{
        width: "100%",
        minHeight: "100vh",
        bgcolor: "#f7f7fb",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        pt: 6,
      }}
    >
      {/* Page title */}
      <Typography variant="h4" sx={{ mb: 4, fontWeight: 700 }}>
        Predict Your Child’s Traits
      </Typography>

      {/* Mode Switch */}
      <Box 
        sx={{
          display: "flex",
          alignItems: "center",
          mb: 4,
          bgcolor: "white",
          p: 2,
          borderRadius: 3,
          boxShadow: 1
        }}
      >
        <Typography sx={{ mr: 2, fontWeight: 600 }}>Mode:</Typography>
        <Typography sx={{ mr: 1 }}>Fast Mode</Typography>
        <Switch checked={mode === "hirisplex"} onChange={handleModeToggle} />
        <Typography>HIrisPlex-S</Typography>
      </Box>

      {/* Cards container */}
      <Box 
        sx={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: 3,
          width: "90%",
          maxWidth: "900px",
        }}
      >

        {/* Upload DNA option */}
        <Card sx={{ borderRadius: 4, boxShadow: 3 }}>
          <CardActionArea onClick={() => navigate("/uploadParents", { state: { mode } })}>
            <CardContent sx={{ p: 4 }}>
              <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
                Upload Both Parents' DNA
              </Typography>
              <Typography variant="body2" sx={{ color: "#666" }}>
                Use 23andMe, AncestryDNA, MyHeritage, FTDNA or raw text files.
                Most accurate results.
              </Typography>
            </CardContent>
          </CardActionArea>
        </Card>

        {/* Manual input option */}
        <Card sx={{ borderRadius: 4, boxShadow: 3 }}>
          <CardActionArea onClick={() => navigate("/manualPartner", { state: { mode } })}>
            <CardContent sx={{ p: 4 }}>
              <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
                Enter Partner Traits Manually
              </Typography>
              <Typography variant="body2" sx={{ color: "#666" }}>
                Enter hair color, eye color, skin tone, and other traits.
              </Typography>
            </CardContent>
          </CardActionArea>
        </Card>

        {/* Population simulation option */}
        <Card sx={{ borderRadius: 4, boxShadow: 3 }}>
          <CardActionArea onClick={() => navigate("/simulatePartner", { state: { mode } })}>
            <CardContent sx={{ p: 4 }}>
              <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
                Simulate Partner From Population
              </Typography>
              <Typography variant="body2" sx={{ color: "#666" }}>
                Choose African, European, Asian, South Asian, or Latino/Hispanic population.
              </Typography>
            </CardContent>
          </CardActionArea>
        </Card>

      </Box>
    </Box>
  );
}
