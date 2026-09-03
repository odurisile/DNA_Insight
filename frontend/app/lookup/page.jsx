"use client";

import { useState } from "react";
import {
  Alert,
  Button,
  Card,
  CardContent,
  Chip,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { lookupGene } from "@/lib/api";
import GeneInfoTooltip from "@/components/GeneInfoTooltip";
import { AnalysisProgress, DemoGenomeButton, SessionNotice } from "@/components/AnalysisUX";

export default function LookupPage() {
  const [file, setFile] = useState(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  async function onSubmit() {
    if (!file || !query.trim()) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("query", query.trim());
      const response = await lookupGene(formData);
      setResult(response);
    } catch (err) {
      setError(err.message || "Gene lookup failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container" style={{ paddingTop: 16, paddingBottom: 32 }}>
      <Typography variant="h4" gutterBottom>
        Gene Lookup
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
        Search the app&apos;s supported genetics catalog by gene symbol or rsID against an uploaded raw DNA file.
      </Typography>

      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Stack spacing={2}>
            <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
              <Button variant="outlined" component="label">
                Choose file
                <input
                  type="file"
                  aria-label="Choose a raw DNA file"
                  hidden
                  accept=".txt,.csv,.tsv"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                />
              </Button>
              <Typography variant="body2" color="text.secondary">
                {file ? file.name : "No file selected"}
              </Typography>
              <DemoGenomeButton disabled={loading} onLoad={(sample, sampleError) => { setFile(sample); setError(sampleError?.message || ""); }} />
            </Stack>

            <TextField
              label="Gene or rsID"
              placeholder="Examples: APOE, MC1R, rs429358"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />

            <Button variant="contained" onClick={onSubmit} disabled={!file || !query.trim() || loading}>
              {loading ? "Searching..." : "Lookup gene"}
            </Button>

            <AnalysisProgress active={loading} message="Searching supported markers in your file…" />
            {error && <Alert severity="error">{error}</Alert>}
            <SessionNotice />
            <Alert severity="info">
              This endpoint searches the supported gene catalog used by the app. It is not a whole-genome annotation service.
            </Alert>
          </Stack>
        </CardContent>
      </Card>

      {result && (
        <Stack spacing={2}>
          <Typography variant="h6">
            Results for {result.query} ({result.result_count})
          </Typography>
          {result.result_count === 0 && (
            <Alert severity="warning">
              No supported gene catalog matches found for that query.
            </Alert>
          )}
          {result.results?.map((entry) => (
            <Card key={entry.gene} className="section-card">
              <CardContent>
                <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
                  <Typography variant="h6">
                    <GeneInfoTooltip gene={entry.gene} snps={entry.matches.map((match) => match.rsid)} />
                  </Typography>
                  <Chip label={`${entry.present_count}/${entry.matched_count} markers present`} size="small" />
                </Stack>
                <Stack spacing={1}>
                  {entry.matches.map((match) => (
                    <Card key={match.rsid} variant="outlined" sx={{ borderRadius: 3 }}>
                      <CardContent>
                        <Stack direction="row" justifyContent="space-between" gap={2} flexWrap="wrap">
                          <div>
                            <Typography
                              component="a"
                              variant="subtitle1"
                              href={`https://www.ncbi.nlm.nih.gov/snp/${encodeURIComponent(match.rsid)}`}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              {match.rsid}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              {match.category} | {match.note}
                            </Typography>
                          </div>
                          <div style={{ textAlign: "right" }}>
                            <Typography variant="body2" fontWeight={700}>
                              {match.present_in_file ? match.genotype : "Not observed"}
                            </Typography>
                            {match.present_in_file && (
                              <Typography variant="caption" color="text.secondary">
                                chr{match.chrom}:{match.pos}
                              </Typography>
                            )}
                          </div>
                        </Stack>
                      </CardContent>
                    </Card>
                  ))}
                </Stack>
              </CardContent>
            </Card>
          ))}
        </Stack>
      )}
    </div>
  );
}
