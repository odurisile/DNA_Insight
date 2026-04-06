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

export default function PartnerSimulationPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const mode = location.state?.mode || "fast";

  const [population, setPopulation] = useState("EUR");
  const [loading, setLoading] = useState(false);

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:5000/simulate_partner", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          population,
          mode,
        }),
      });

      const data = await res.json();

      if (data.status === "ok") {
        navigate("/childResults", {
          state: {
            parent1: location.state?.parent1 || null,
            parent2: data.genotypes,
            mode,
            population,
          },
        });
      } else {
        alert("Error: " + data.message);
      }
    } catch (e) {
      alert("Failed: " + e);
    }
    setLoading(false);
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
      {/* Title */}
      <Typography variant="h4" sx={{ mb: 4, fontWeight: 700 }}>
        Simulate Partner from Population
      </Typography>

      {/* Card */}
      <Card sx={{ width: 500, borderRadius: 3, boxShadow: 3 }}>
        <CardContent sx={{ p: 4 }}>
          <Typography sx={{ mb: 2 }}>
            Choose a population to simulate your partner's genetic profile using
            1000 Genomes allele frequencies.
          </Typography>

          <Typography sx={{ mb: 1, fontWeight: 600 }}>Population</Typography>
          <Select
            fullWidth
            value={population}
            onChange={(e) => setPopulation(e.target.value)}
            sx={{ mb: 3 }}
          >
            {/* Superpopulations */}
            <MenuItem value="AFR">AFR – African</MenuItem>
            <MenuItem value="EUR">EUR – European</MenuItem>
            <MenuItem value="EAS">EAS – East Asian</MenuItem>
            <MenuItem value="SAS">SAS – South Asian</MenuItem>
            <MenuItem value="AMR">AMR – Admixed American</MenuItem>

            {/* Example subpops (your backend freq file can include more) */}
            <MenuItem value="YRI">YRI – Yoruba (Nigeria)</MenuItem>
            <MenuItem value="CEU">CEU – European (Utah)</MenuItem>
            <MenuItem value="CHB">CHB – Han Chinese (Beijing)</MenuItem>
            <MenuItem value="PJL">PJL – Punjabi (Lahore)</MenuItem>
            <MenuItem value="MXL">MXL – Mexican (Los Angeles)</MenuItem>
          </Select>

          <Button
            variant="contained"
            onClick={handleSimulate}
            disabled={loading}
            sx={{
              mt: 2,
              px: 4,
              py: 1.5,
              borderRadius: 3,
              boxShadow: 3,
            }}
          >
            {loading ? "Simulating…" : "Simulate Partner →"}
          </Button>
        </CardContent>
      </Card>
    </Box>
  );
}
