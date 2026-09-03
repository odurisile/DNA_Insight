"use client";
import { useState } from "react";
import { Typography, Card, CardContent, Button, Alert, Stack, TextField, MenuItem } from "@mui/material";
import HeightPGSCard from "@/components/HeightPGSCard";
import { computeHeightPGS } from "@/lib/api";
import { AnalysisProgress, ConfidenceGuide, DemoGenomeButton, SessionNotice } from "@/components/AnalysisUX";

export default function HeightPage() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [sex, setSex] = useState("unspecified");
  const [globalAncestry, setGlobalAncestry] = useState("");
  const [observedHeight, setObservedHeight] = useState("");

  const onSubmit = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("sex", sex);
    if (observedHeight.trim()) {
      formData.append("observed_height_cm", observedHeight.trim());
    }
    if (globalAncestry.trim()) {
      try {
        JSON.parse(globalAncestry);
        formData.append("global_ancestry", globalAncestry);
      } catch (err) {
        setError("Global ancestry must be valid JSON, e.g. {\"AFR\":0.6,\"EUR\":0.4}");
        setLoading(false);
        return;
      }
    }
    try {
      const data = await computeHeightPGS(formData);
      setResult(data);
    } catch (e) {
      setError(e.message || "Height PGS failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ paddingTop: 16, paddingBottom: 32 }}>
      <Typography variant="h4" gutterBottom>Height Polygenic Score</Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
        Upload a raw genotype file (23andMe/Ancestry-style) to compute a demo height polygenic score and projected height distribution.
      </Typography>
      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2} alignItems={{ xs: "stretch", sm: "center" }}>
            <Button variant="outlined" component="label">
              Choose file
              <input aria-label="Choose a raw DNA file" type="file" hidden accept=".txt,.csv,.tsv" onChange={(e) => setFile(e.target.files?.[0] || null)} />
            </Button>
            <Typography variant="body2" color="text.secondary">
              {file ? file.name : "No file selected"}
            </Typography>
            <Button variant="contained" onClick={onSubmit} disabled={!file || loading}>
              {loading ? "Computing..." : "Compute Height PGS"}
            </Button>
            <DemoGenomeButton disabled={loading} onLoad={(sample, sampleError) => { setFile(sample); setError(sampleError?.message || null); }} />
          </Stack>
          <Stack direction="row" spacing={2} sx={{ mt: 2, flexWrap: "wrap" }}>
            <TextField
              select
              label="Biological sex"
              size="small"
              value={sex}
              onChange={(e) => setSex(e.target.value)}
              sx={{ minWidth: 180 }}
            >
              <MenuItem value="unspecified">Unspecified</MenuItem>
              <MenuItem value="male">Male</MenuItem>
              <MenuItem value="female">Female</MenuItem>
            </TextField>
            <TextField
              label="Global ancestry (JSON, optional)"
              size="small"
              placeholder='{"AFR":0.6,"EUR":0.4}'
              value={globalAncestry}
              onChange={(e) => setGlobalAncestry(e.target.value)}
              sx={{ minWidth: 320, flexGrow: 1 }}
            />
            <TextField
              label="Observed height (cm, optional)"
              size="small"
              type="number"
              value={observedHeight}
              onChange={(e) => setObservedHeight(e.target.value)}
              sx={{ minWidth: 200 }}
            />
          </Stack>
          <Stack spacing={1.5} sx={{ mt: 2 }}>
            <AnalysisProgress active={loading} message="Calculating marker coverage and height distribution…" />
            {error && <Alert severity="error">{error}</Alert>}
            <SessionNotice />
            <ConfidenceGuide />
          </Stack>
        </CardContent>
      </Card>

      {result && <HeightPGSCard result={result} />}
    </div>
  );
}
