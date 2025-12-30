import React, { useEffect, useState } from "react";
import {
  Box,
  Typography,
  Card,
  CardContent,
  LinearProgress,
  Divider,
} from "@mui/material";

import ChildAvatar from "../components/avatar/ChildAvatar";
import EyeColorChart from "../charts/EyeColorChart";
import HairColorChart from "../charts/HairColorChart";
import SkinToneChart from "../charts/SkinToneChart";

import { useLocation } from "react-router-dom";

export default function ChildResultsPage() {
  const location = useLocation();
  const parent1 = location.state?.parent1;
  const parent2 = location.state?.parent2;
  const mode = location.state?.mode || "fast";

  const [loading, setLoading] = useState(true);
  const [child, setChild] = useState(null);

  // API: predict child
  useEffect(() => {
    const predict = async () => {
      setLoading(true);

      try {
        const res = await fetch("http://localhost:5000/child", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ parent1, parent2, mode }),
        });

        const data = await res.json();

        if (data.status === "ok") {
          setChild(data.child);
        } else {
          alert("Prediction error: " + data.message);
        }
      } catch (err) {
        alert("Could not connect to backend: " + err);
      }

      setLoading(false);
    };

    predict();
  }, []);

  if (loading) {
    return (
      <Box sx={{ p: 4 }}>
        <Typography variant="h5" sx={{ mb: 2 }}>
          Predicting your child's traits…
        </Typography>
        <LinearProgress />
      </Box>
    );
  }

  if (!child) {
    return (
      <Box sx={{ p: 4 }}>
        <Typography>No prediction data available.</Typography>
      </Box>
    );
  }

  const traits = child.traits;

  // Extract visual chart data
  const eyeProb = traits.eye_color?.probabilities || null;
  const hairProb = traits.hair_color?.probabilities || null;
  const skinProb = traits.skin_color?.probabilities || null;

  return (
    <Box
      sx={{
        width: "100%",
        minHeight: "100vh",
        bgcolor: "#f5f6fb",
        p: 4,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      {/* Title */}
      <Typography variant="h4" sx={{ mb: 1, fontWeight: 700 }}>
        Predicted Child Traits
      </Typography>

      {/* Model badge */}
      <Typography sx={{ mb: 4, color: "#7a7a7a" }}>
        Model used: <strong>{traits.model_used}</strong>
      </Typography>

      {/* Avatar Section */}
      <ChildAvatar traits={traits} />

      <Divider sx={{ width: "85%", my: 4 }} />

      {/* Results grid */}
      <Box
        sx={{
          width: "90%",
          maxWidth: "1100px",
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 4,
        }}
      >
        {/* LEFT COLUMN — TRAIT CARDS */}
        <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
          {/* Eye Color */}
          <Card sx={{ borderRadius: 3, boxShadow: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                Eye Color
              </Typography>
              <Typography sx={{ mb: 2 }}>
                <strong>{traits.eye_color.result}</strong> 
                {" — "} {(traits.eye_color.confidence * 100).toFixed(1)}%
              </Typography>

              {/* Eye chart */}
              {eyeProb && <EyeColorChart data={eyeProb} />}
            </CardContent>
          </Card>

          {/* Hair Color */}
          <Card sx={{ borderRadius: 3, boxShadow: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                Hair Color
              </Typography>
              <Typography sx={{ mb: 2 }}>
                <strong>{traits.hair_color.result}</strong>
                {" — "} {(traits.hair_color.confidence * 100).toFixed(1)}%
              </Typography>

              {/* Hair chart */}
              {hairProb && <HairColorChart data={hairProb} />}
            </CardContent>
          </Card>

          {/* Skin Tone */}
          <Card sx={{ borderRadius: 3, boxShadow: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                Skin Tone
              </Typography>
              <Typography sx={{ mb: 2 }}>
                <strong>{traits.skin_color.result}</strong>
              </Typography>

              {/* Skin chart */}
              {skinProb && <SkinToneChart data={skinProb} />}
            </CardContent>
          </Card>
        </Box>

        {/* RIGHT COLUMN — OTHER TRAITS */}
        <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
          {/* Freckles */}
          <Card sx={{ borderRadius: 3, boxShadow: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Freckling
              </Typography>
              <Typography>{traits.freckling.result}</Typography>
            </CardContent>
          </Card>

          {/* Tanning */}
          <Card sx={{ borderRadius: 3, boxShadow: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Tanning Response
              </Typography>
              <Typography>{traits.tanning.result}</Typography>
            </CardContent>
          </Card>

          {/* Red Hair Probability */}
          {traits.red_hair_probability && (
            <Card sx={{ borderRadius: 3, boxShadow: 3 }}>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Red Hair Probability
                </Typography>
                <Typography>
                  {(traits.red_hair_probability.percent || 0).toFixed(1)}%
                </Typography>
              </CardContent>
            </Card>
          )}
        </Box>
      </Box>

      {/* Ancestry Summary */}
      <Divider sx={{ width: "85%", my: 4 }} />

      <Typography variant="h5" sx={{ mb: 2, fontWeight: 600 }}>
        Estimated Child Ancestry
      </Typography>

      <Box sx={{ width: "60%", maxWidth: "600px" }}>
        {Object.entries(child.ancestry || {}).map(([pop, val]) => (
          <Box key={pop} sx={{ mb: 2 }}>
            <Typography sx={{ mb: 0.5 }}>
              {pop.toUpperCase()} — {(val * 100).toFixed(1)}%
            </Typography>
            <LinearProgress
              variant="determinate"
              value={val * 100}
              sx={{
                height: 10,
                borderRadius: 5,
                "& .MuiLinearProgress-bar": { borderRadius: 5 },
              }}
            />
          </Box>
        ))}
      </Box>
    </Box>
  );
}
