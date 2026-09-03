"use client";

import { useState } from "react";
import { Alert, Button, CircularProgress, LinearProgress, Stack, Typography } from "@mui/material";
import ScienceIcon from "@mui/icons-material/Science";

export async function loadDemoGenome() {
  const response = await fetch("/sample_genome_23andme.txt");
  if (!response.ok) throw new Error("Could not load the sample genome");
  const blob = await response.blob();
  return new File([blob], "synthetic_sample_genome.txt", { type: "text/plain" });
}

export function DemoGenomeButton({ onLoad, disabled = false, label = "Use synthetic sample" }) {
  const [loading, setLoading] = useState(false);

  async function handleClick() {
    setLoading(true);
    try {
      onLoad(await loadDemoGenome());
    } catch (error) {
      onLoad(null, error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Button
      type="button"
      variant="text"
      startIcon={loading ? <CircularProgress size={18} /> : <ScienceIcon />}
      onClick={handleClick}
      disabled={disabled || loading}
    >
      {loading ? "Loading sample…" : label}
    </Button>
  );
}

export function SelectedFileNotice({ file }) {
  if (!file) return null;
  const isSample = file.name === "synthetic_sample_genome.txt";
  return (
    <Alert severity="success" role="status" aria-live="polite">
      {isSample ? "Synthetic sample ready" : "File selected"}: {file.name}
    </Alert>
  );
}

export function AnalysisProgress({ active, message = "Analyzing genotype markers…" }) {
  if (!active) return null;
  return (
    <Stack spacing={1} role="status" aria-live="polite" aria-busy="true">
      <LinearProgress aria-label={message} />
      <Typography variant="body2" color="text.secondary">
        {message} Large DNA exports may take a minute. Keep this tab open.
      </Typography>
    </Stack>
  );
}

export function SessionNotice() {
  return (
    <Alert severity="info">
      Your raw upload is deleted from the server immediately after processing. Results remain only in this tab&apos;s session and disappear when you close the tab.
    </Alert>
  );
}

export function ConfidenceGuide() {
  return (
    <Alert severity="info">
      Confidence depends on how many required markers are present and how well the reference data represents you. Low coverage means the estimate is less dependable—not that the trait is absent.
    </Alert>
  );
}
