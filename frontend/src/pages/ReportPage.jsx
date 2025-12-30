import React from "react";
import { Card, CardContent, Typography, Divider, Box, LinearProgress } from "@mui/material";

const SectionTitle = ({ children }) => (
  <Typography variant="h5" sx={{ mt: 4, mb: 2 }}>
    {children}
  </Typography>
);

const TraitCard = ({ title, result, probabilities = {} }) => (
  <Card sx={{ mb: 3 }}>
    <CardContent>
      <Typography variant="h6">{title}</Typography>
      <Typography variant="body1" sx={{ mb: 2 }}>
        Result: <strong>{result}</strong>
      </Typography>

      {Object.keys(probabilities).length > 0 && (
        <>
          <Typography variant="body2" sx={{ mb: 1 }}>
            Probabilities:
          </Typography>

          {Object.entries(probabilities).map(([key, value]) => (
            <Box key={key} sx={{ mb: 1 }}>
              <Typography variant="body2">
                {key} — {(value * 100).toFixed(1)}%
              </Typography>
              <LinearProgress variant="determinate" value={value * 100} sx={{ height: 6, borderRadius: 3 }} />
            </Box>
          ))}
        </>
      )}
    </CardContent>
  </Card>
);

export default function ReportPage({ data }) {
  const traits = data.traits || {};
  const ancestry = data.ancestry || {};
  const health = data.health || [];

  return (
    <Box sx={{ maxWidth: 900, mx: "auto", py: 4 }}>
      <Typography variant="h4" sx={{ mb: 2 }}>
        Genetic Report
      </Typography>

      {/* TRAITS */}
      <SectionTitle>Traits</SectionTitle>
      {Object.entries(traits).map(([key, trait]) => (
        <TraitCard
          key={key}
          title={key.replace(/_/g, " ").toUpperCase()}
          result={trait.result}
          probabilities={trait.probabilities || {}}
        />
      ))}

      <Divider />

      {/* HEALTH */}
      <SectionTitle>Health Risks</SectionTitle>
      {health.length === 0 ? (
        <Typography>No significant health markers detected.</Typography>
      ) : (
        health.map((h) => (
          <Card key={h.name} sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6">{h.name}</Typography>
              <Typography variant="body1">Risk: {h.level}</Typography>
            </CardContent>
          </Card>
        ))
      )}

      <Divider />

      {/* ANCESTRY */}
      <SectionTitle>Ancestry</SectionTitle>
      <Card>
        <CardContent>
          {Object.entries(ancestry).map(([region, pct]) => (
            <Typography key={region}>
              {region}: {(pct * 100).toFixed(1)}%
            </Typography>
          ))}
        </CardContent>
      </Card>
    </Box>
  );
}
