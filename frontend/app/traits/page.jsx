"use client";

import { useMemo, useState } from "react";
import {
  Alert,
  Button,
  Card,
  CardContent,
  Chip,
  MenuItem,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { fetchGwasTraits } from "@/lib/api";
import { AnalysisProgress, ConfidenceGuide, DemoGenomeButton, SessionNotice } from "@/components/AnalysisUX";

export default function TraitsPage() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [search, setSearch] = useState("");
  const [minSnps, setMinSnps] = useState("2");
  const [sortBy, setSortBy] = useState("snps");

  async function onSubmit() {
    if (!file) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("min_snps", minSnps);
      const response = await fetchGwasTraits(formData);
      setResult(response);
    } catch (err) {
      setError(err.message || "GWAS trait lookup failed");
    } finally {
      setLoading(false);
    }
  }

  const filteredTraits = useMemo(() => {
    const traits = result?.traits || [];
    const query = search.trim().toLowerCase();
    let rows = query ? traits.filter((item) => item.trait.toLowerCase().includes(query)) : traits;

    rows = [...rows].sort((a, b) => {
      if (sortBy === "percentile") return b.percentile - a.percentile;
      if (sortBy === "zscore") return Math.abs(b.z) - Math.abs(a.z);
      return b.snps_used - a.snps_used;
    });

    return rows;
  }, [result, search, sortBy]);

  return (
    <div className="container" style={{ paddingTop: 16, paddingBottom: 32 }}>
      <Typography variant="h4" gutterBottom>
        GWAS Trait Explorer
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
        Score all GWAS trait strings in the database that have enough overlapping SNP signal in an uploaded raw DNA file.
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

            <Stack direction="row" spacing={2} flexWrap="wrap">
              <TextField
                select
                label="Minimum SNPs"
                size="small"
                value={minSnps}
                onChange={(e) => setMinSnps(e.target.value)}
                sx={{ minWidth: 180 }}
              >
                <MenuItem value="1">1 SNP</MenuItem>
                <MenuItem value="2">2 SNPs</MenuItem>
                <MenuItem value="3">3 SNPs</MenuItem>
                <MenuItem value="5">5 SNPs</MenuItem>
              </TextField>

              <TextField
                select
                label="Sort by"
                size="small"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                sx={{ minWidth: 180 }}
              >
                <MenuItem value="snps">SNP count</MenuItem>
                <MenuItem value="zscore">Absolute z-score</MenuItem>
                <MenuItem value="percentile">Percentile</MenuItem>
              </TextField>
            </Stack>

            <Button variant="contained" onClick={onSubmit} disabled={!file || loading}>
              {loading ? "Scoring traits..." : "Load GWAS traits"}
            </Button>

            <AnalysisProgress active={loading} message="Matching markers and scoring GWAS traits…" />
            {error && <Alert severity="error">{error}</Alert>}
            <SessionNotice />
            <ConfidenceGuide />
            <Alert severity="info">
              This surfaces trait strings present in the local GWAS database. It does not mean every trait is clinically valid or production-ready for consumer reporting.
            </Alert>
          </Stack>
        </CardContent>
      </Card>

      {result && (
        <Stack spacing={2}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2}>
            <Typography variant="h6">
              Matched traits: {result.result_count}
            </Typography>
            <Chip label={`Minimum SNPs: ${result.min_snps}`} size="small" />
          </Stack>

          <TextField
            label="Filter trait names"
            size="small"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />

          <Card className="section-card">
            <CardContent>
              {filteredTraits.length === 0 ? (
                <Typography color="text.secondary">No GWAS traits matched the current filters.</Typography>
              ) : (
                <div className="responsive-table" role="region" aria-label="GWAS trait results" tabIndex={0}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Trait</TableCell>
                      <TableCell>SNPs used</TableCell>
                      <TableCell>Percentile</TableCell>
                      <TableCell>Z-score</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredTraits.map((trait) => (
                      <TableRow key={trait.trait}>
                        <TableCell>{trait.trait}</TableCell>
                        <TableCell>{trait.snps_used}</TableCell>
                        <TableCell>{trait.percentile.toFixed(1)}%</TableCell>
                        <TableCell>{trait.z.toFixed(3)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </Stack>
      )}
    </div>
  );
}
