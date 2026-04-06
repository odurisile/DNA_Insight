"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Grid,
  LinearProgress,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import DownloadIcon from "@mui/icons-material/Download";
import ColorLensIcon from "@mui/icons-material/ColorLens";
import HealthAndSafetyIcon from "@mui/icons-material/HealthAndSafety";
import ScienceIcon from "@mui/icons-material/Science";
import { generatePDF } from "@/lib/api";

const EMPTY_VALUE = "N/A";

function formatPercent(val) {
  return val || val === 0 ? `${val.toFixed(1)}%` : EMPTY_VALUE;
}

function resolveTraitValue(data) {
  if (!data) return EMPTY_VALUE;
  if (typeof data === "string") return data;
  if (typeof data === "object") {
    if (data.result) return data.result;
    return Object.entries(data)
      .map(([key, value]) => `${key.replace(/_/g, " ")}: ${value}`)
      .join(" | ");
  }
  return EMPTY_VALUE;
}

function hasMeaningfulValue(value) {
  if (!value) return false;
  const normalized = String(value).trim().toLowerCase();
  return !["n/a", "unknown", ""].includes(normalized);
}

function resolveTraitConfidence(data) {
  if (data && typeof data === "object" && typeof data.confidence === "number") {
    return formatPercent(data.confidence * 100);
  }
  return null;
}

export default function ReportPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    const raw = sessionStorage.getItem("reportData");
    if (raw) setData(JSON.parse(raw));
  }, []);

  const health = data?.health || data?.risk;
  const traits = data?.traits || {};
  const genotypePanel = data?.genotype_panel || [];

  const prsRows = useMemo(() => {
    if (!health?.prs) return [];
    return Object.entries(health.prs)
      .filter(([, value]) => value)
      .map(([trait, value]) => ({
        trait,
        percentile: value.percentile,
        snps: value.snps_used,
      }));
  }, [health]);

  const variantRows = useMemo(() => {
    const dominants = (health?.dominant_mutations || []).map((variant) => ({ ...variant, category: "Dominant" }));
    const carriers = (health?.carrier_status || []).map((variant) => ({ ...variant, category: "Carrier" }));
    return [...dominants, ...carriers];
  }, [health]);

  const wellnessCategories = useMemo(() => {
    const sleepSignals = [
      { label: "Sleep chronotype", value: resolveTraitValue(traits.sleep_chronotype) },
      { label: "Caffeine metabolism", value: resolveTraitValue(traits.caffeine_metabolism) },
      { label: "Nicotine dependence", value: resolveTraitValue(traits.nicotine_dependence) },
    ].filter((item) => item.value !== EMPTY_VALUE && item.value !== "Unknown");

    const recoverySignals = [
      { label: "Folate metabolism", value: resolveTraitValue(traits.folate_metabolism) },
      { label: "Vitamin D levels", value: resolveTraitValue(traits.vitamin_d) },
      { label: "Pain sensitivity", value: resolveTraitValue(traits.pain_sensitivity) },
      { label: "Alcohol flush", value: resolveTraitValue(traits.alcohol_flush) },
    ].filter((item) => item.value !== EMPTY_VALUE && item.value !== "Unknown");

    const fitnessSignals = [
      { label: "Muscle performance", value: resolveTraitValue(traits.muscle_performance) },
      { label: "Endurance", value: resolveTraitValue(traits.endurance) },
      { label: "BMI PRS", value: health?.risk_summary?.Obesity || EMPTY_VALUE },
      { label: "Heart PRS", value: health?.risk_summary?.HeartDisease || EMPTY_VALUE },
    ].filter((item) => item.value !== EMPTY_VALUE && item.value !== "Unknown");

    return [
      {
        title: "Sleep",
        description: "Chronotype and stimulant-related signals that can affect timing and sleep pressure.",
        signals: sleepSignals,
      },
      {
        title: "Recovery",
        description: "Signals connected to nutrient handling, inflammation sensitivity, and post-stress recovery.",
        signals: recoverySignals,
      },
      {
        title: "Fitness Response",
        description: "Training-response cues combining muscle bias with cardiometabolic context.",
        signals: fitnessSignals,
      },
    ].filter((category) => category.signals.length > 0);
  }, [health, traits]);

  const filteredGenotypeBlocks = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return genotypePanel;
    return genotypePanel
      .map((block) => ({
        ...block,
        snps: block.snps.filter((snp) =>
          [block.title, block.description, snp.gene, snp.rsid, snp.genotype]
            .filter(Boolean)
            .some((value) => String(value).toLowerCase().includes(query))
        ),
      }))
      .filter((block) => block.snps.length > 0);
  }, [genotypePanel, search]);

  const filteredVariantRows = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return variantRows;
    return variantRows.filter((variant) =>
      [variant.gene, variant.rsid, variant.variant, variant.genotype, variant.category]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(query))
    );
  }, [search, variantRows]);

  if (!data) return <div className="container">No report data found.</div>;

  async function downloadPDF() {
    try {
      setError("");
      const payload = health ? { ...data, health } : data;
      const blob = await generatePDF(payload);
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "genetic_report.pdf";
      anchor.click();
    } catch (err) {
      setError(err.message || "PDF generation failed");
    }
  }

  const traitCards = [
    { label: "Eye color", data: traits.eye_color },
    { label: "Hair color", data: traits.hair_color },
    { label: "Freckling", data: traits.freckling },
    { label: "Tanning response", data: traits.tanning_response },
    { label: "Lactose tolerance", data: traits.lactose_tolerance },
    { label: "Caffeine metabolism", data: traits.caffeine_metabolism },
    { label: "Muscle performance", data: traits.muscle_performance },
    { label: "Alcohol flush", data: traits.alcohol_flush },
    { label: "Nicotine dependence", data: traits.nicotine_dependence },
    { label: "Folate metabolism", data: traits.folate_metabolism },
    { label: "Vitamin D levels", data: traits.vitamin_d },
    { label: "Sleep chronotype", data: traits.sleep_chronotype },
    { label: "Pain sensitivity", data: traits.pain_sensitivity },
    { label: "Endurance", data: traits.endurance },
    { label: "Bitter taste", data: traits.bitter_taste },
  ]
    .map((item) => ({
      ...item,
      value: resolveTraitValue(item.data),
      confidence: resolveTraitConfidence(item.data),
    }))
    .filter((item) => hasMeaningfulValue(item.value));

  return (
    <div className="container">
      <div className="hero" style={{ marginBottom: 22 }}>
        <div className="hero-content">
          <Chip
            label="Interactive genotype evidence"
            size="small"
            sx={{ width: "fit-content", background: "rgba(255,255,255,0.12)", color: "#fff" }}
          />
          <Typography variant="h4">Genome Portrait</Typography>
          <Typography variant="body1" sx={{ maxWidth: 680, opacity: 0.9 }}>
            Every section below ties your calls back to the underlying genotype.
          </Typography>
          <Stack direction="row" spacing={2} sx={{ mt: 1 }}>
            <Button variant="contained" color="secondary" startIcon={<DownloadIcon />} onClick={downloadPDF}>
              Download PDF
            </Button>
            {health?.apoe?.genotype && <Chip label={`APOE ${health.apoe.genotype}`} color="default" variant="outlined" />}
          </Stack>
        </div>
      </div>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Alert severity="warning" sx={{ mb: 2 }}>
        This report is informational and research-oriented. It is not a diagnosis, treatment plan, or substitute for medical advice.
      </Alert>

      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Card className="section-card">
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                <HealthAndSafetyIcon color="primary" />
                <Typography variant="h6">Risk Dashboard</Typography>
              </Stack>
              <Typography variant="body2" color="text.secondary">
                A summary of your genetic health risks, based on polygenic scores and key variants.
              </Typography>
              <div className="chip-row">
                {health?.risk_summary &&
                  Object.entries(health.risk_summary).map(([key, value]) => (
                    <Chip key={key} label={`${key}: ${value}`} color={value === "High" ? "secondary" : "default"} />
                  ))}
              </div>
              {health?.apoe?.genotype && (
                <Typography variant="body2" sx={{ mt: 1.5 }}>
                  APOE: <strong>{health.apoe.genotype}</strong> ({health.apoe.risk})
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card className="section-card">
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                <ScienceIcon color="secondary" />
                <Typography variant="h6">Polygenic and targeted signal</Typography>
              </Stack>
              {prsRows.length === 0 && <Typography color="text.secondary">No PRS calls available.</Typography>}
              <div className="grid-gap">
                {prsRows.map((row) => (
                  <div key={row.trait}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <Typography textTransform="capitalize">{row.trait.replace("_", " ")}</Typography>
                      <Typography fontWeight={700}>{formatPercent(row.percentile)}</Typography>
                    </Stack>
                    <LinearProgress
                      variant="determinate"
                      value={Math.min(100, row.percentile)}
                      sx={{ height: 8, borderRadius: 4, backgroundColor: "#e5e7eb" }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      SNPs used: {row.snps}
                    </Typography>
                  </div>
                ))}
              </div>
              {health?.height_percentile !== undefined && health?.height_percentile !== null && (
                <Typography variant="body2" sx={{ mt: 2 }}>
                  Height percentile: {formatPercent(health.height_percentile)}
                </Typography>
              )}
              {health?.targeted && (
                <Typography variant="body2" sx={{ mt: 2 }}>
                  Celiac markers: {health.targeted.celiac?.genotype || EMPTY_VALUE} / support{" "}
                  {health.targeted.celiac_support?.genotype || EMPTY_VALUE} ({health.risk_summary?.Celiac || EMPTY_VALUE})
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={2} sx={{ mt: 2 }}>
        <Grid item xs={12}>
          <Card className="section-card">
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                <ScienceIcon color="secondary" />
                <Typography variant="h6">Wellness categories</Typography>
              </Stack>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                These group existing signals into practical themes like sleep, recovery, and training response.
              </Typography>
              <Grid container spacing={2}>
                {wellnessCategories.map((category) => (
                  <Grid item xs={12} md={4} key={category.title}>
                    <Card variant="outlined" sx={{ borderRadius: 12, height: "100%" }}>
                      <CardContent>
                        <Typography variant="h6">{category.title}</Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                          {category.description}
                        </Typography>
                        <Stack spacing={1}>
                          {category.signals.map((signal) => (
                            <Stack key={`${category.title}-${signal.label}`} direction="row" justifyContent="space-between" gap={2}>
                              <Typography variant="body2" color="text.secondary">{signal.label}</Typography>
                              <Typography variant="body2" fontWeight={600} textAlign="right">{signal.value}</Typography>
                            </Stack>
                          ))}
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={7}>
          <Card className="section-card">
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                <ColorLensIcon color="primary" />
                <Typography variant="h6">Trait Studio</Typography>
              </Stack>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Only traits with usable signal in the uploaded file are shown here. Traits without matching marker coverage are hidden instead of displayed as unknown.
              </Typography>
              <Grid container spacing={2}>
                {traitCards.map(({ label, value, confidence }) => {
                  return (
                    <Grid item xs={12} sm={6} key={label}>
                      <Card variant="outlined" sx={{ borderRadius: 12, height: "100%" }}>
                        <CardContent>
                          <Typography variant="subtitle2" color="text.secondary">{label}</Typography>
                          <Typography variant="h6">{value}</Typography>
                          {confidence && (
                            <Typography variant="body2" color="text.secondary">
                              Confidence: {confidence}
                            </Typography>
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                  );
                })}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={5}>
          <Card className="section-card" sx={{ height: "100%" }}>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                <HealthAndSafetyIcon color="primary" />
                <Typography variant="h6">ClinVar and carrier calls</Typography>
              </Stack>
              {filteredVariantRows.length === 0 ? (
                <Typography color="text.secondary">No carrier or dominant variants detected.</Typography>
              ) : (
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Gene</TableCell>
                      <TableCell>RSID</TableCell>
                      <TableCell>Variant</TableCell>
                      <TableCell>Genotype</TableCell>
                      <TableCell>Category</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredVariantRows.map((variant) => (
                      <TableRow key={`${variant.rsid}-${variant.gene}`}>
                        <TableCell>{variant.gene}</TableCell>
                        <TableCell>{variant.rsid}</TableCell>
                        <TableCell>{variant.variant}</TableCell>
                        <TableCell>{variant.genotype || EMPTY_VALUE}</TableCell>
                        <TableCell>
                          <Chip
                            label={variant.category}
                            color={variant.category === "Dominant" ? "secondary" : "default"}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card className="section-card" sx={{ mt: 2 }}>
        <CardContent>
          <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
            <ScienceIcon color="secondary" />
            <Typography variant="h6">Variant and gene search</Typography>
          </Stack>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Search the evidence layer by gene symbol, rsID, genotype, or variant label.
          </Typography>
          <TextField
            label="Search by gene, rsID, genotype, or variant"
            size="small"
            fullWidth
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            sx={{ mb: 2 }}
          />
          <Divider sx={{ mb: 2 }} />
          {filteredGenotypeBlocks.length === 0 && filteredVariantRows.length === 0 && (
            <Typography color="text.secondary">No genotype or variant matches found for that search.</Typography>
          )}
          {!search && genotypePanel.length === 0 && (
            <Typography color="text.secondary">No key SNPs captured from this file.</Typography>
          )}
          <Stack spacing={2}>
            {filteredGenotypeBlocks.map((block) => (
              <div key={block.title}>
                <Typography variant="subtitle1">{block.title}</Typography>
                <Typography variant="body2" color="text.secondary">{block.description}</Typography>
                <div className="chip-row">
                  {block.snps.map((snp) => (
                    <Tooltip key={snp.rsid} title={snp.gene || "Variant"}>
                      <Chip label={`${snp.gene || snp.rsid}: ${snp.genotype}`} />
                    </Tooltip>
                  ))}
                </div>
              </div>
            ))}
          </Stack>
        </CardContent>
      </Card>
    </div>
  );
}
