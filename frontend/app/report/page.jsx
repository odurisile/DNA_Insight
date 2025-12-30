"use client";
import { useEffect, useMemo, useState } from 'react';
import {
  Button,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Stack,
  LinearProgress,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tooltip
} from '@mui/material';
import DownloadIcon from "@mui/icons-material/Download";
import ColorLensIcon from "@mui/icons-material/ColorLens";
import HealthAndSafetyIcon from "@mui/icons-material/HealthAndSafety";
import ScienceIcon from "@mui/icons-material/Science";
import { generatePDF } from '@/lib/api';

export default function ReportPage() {
  const [data, setData] = useState(null);

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
      .filter(([, v]) => v)
      .map(([trait, v]) => ({
        trait,
        percentile: v.percentile,
        snps: v.snps_used
      }));
  }, [health]);

  const variantRows = useMemo(() => {
    const dominants = (health?.dominant_mutations || []).map(v => ({ ...v, category: "Dominant" }));
    const carriers = (health?.carrier_status || []).map(v => ({ ...v, category: "Carrier" }));
    return [...dominants, ...carriers];
  }, [health]);

  const percent = (val) => (val || val === 0) ? `${val.toFixed(1)}%` : "—";

  const traitValue = (d) => {
    if (!d) return "—";
    if (typeof d === "string") return d;
    if (typeof d === "object") {
        if (d.result) return d.result;
        return Object.entries(d).map(([k, v]) => `${k.replace(/_/g, " ")}: ${v}`).join(" • ");
    }
    return "—";
  };

  const traitConfidence = (d) => {
    if (d && typeof d === "object" && typeof d.confidence === "number") {
      return percent(d.confidence * 100);
    }
    return null;
  };

  if (!data) return <div className='container'>No report data found.</div>;

  async function downloadPDF() {
    const payload = health ? { ...data, health } : data;
    const blob = await generatePDF(payload);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "genetic_report.pdf";
    a.click();
  }

  return (
    <div className='container'>
      <div className="hero" style={{ marginBottom: 22 }}>
        <div className="hero-content">
          <Chip label="Interactive genotype evidence" size="small" sx={{ width: "fit-content", background: "rgba(255,255,255,0.12)", color: "#fff" }} />
          <Typography variant='h4'>Genome Portrait</Typography>
          <Typography variant='body1' sx={{ maxWidth: 680, opacity: 0.9 }}>
            A Promethease-style evidence layer wrapped in a 23andMe-like experience. Every section below
            ties your calls back to the underlying genotype.
          </Typography>
          <Stack direction="row" spacing={2} sx={{ mt: 1 }}>
            <Button variant='contained' color='secondary' startIcon={<DownloadIcon />} onClick={downloadPDF}>
              Download PDF
            </Button>
            {health?.apoe?.genotype && (
              <Chip label={`APOE ${health.apoe.genotype}`} color="default" variant="outlined" />
            )}
          </Stack>
        </div>
      </div>

      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Card className="section-card">
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                <HealthAndSafetyIcon color="primary" />
                <Typography variant='h6'>Risk Dashboard</Typography>
              </Stack>
              <Typography variant='body2' color="text.secondary">
                Clinical-style severity plus consumer-friendly summaries.
              </Typography>
              <div className="chip-row">
                {health?.risk_summary && Object.entries(health.risk_summary).map(([k, v]) => (
                  <Chip key={k} label={`${k}: ${v}`} color={v === "High" ? "secondary" : "default"} />
                ))}
              </div>
              {health?.apoe?.genotype && (
                <Typography variant='body2' sx={{ mt: 1.5 }}>
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
                <Typography variant='h6'>Polygenic & targeted signal</Typography>
              </Stack>
              {prsRows.length === 0 && (
                <Typography color="text.secondary">No PRS calls available.</Typography>
              )}
              <div className="grid-gap">
                {prsRows.map((row) => (
                  <div key={row.trait}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <Typography textTransform="capitalize">{row.trait.replace("_", " ")}</Typography>
                      <Typography fontWeight={700}>{percent(row.percentile)}</Typography>
                    </Stack>
                    <LinearProgress
                      variant="determinate"
                      value={Math.min(100, row.percentile)}
                      sx={{ height: 8, borderRadius: 4, backgroundColor: "#e5e7eb" }}
                    />
                    <Typography variant='caption' color="text.secondary">
                      SNPs used: {row.snps}
                    </Typography>
                  </div>
                ))}
              </div>
              {health?.height_percentile !== undefined && health?.height_percentile !== null && (
                <Typography variant='body2' sx={{ mt: 2 }}>
                  Height percentile: {percent(health.height_percentile)}
                </Typography>
              )}
              {health?.targeted && (
                <Typography variant='body2' sx={{ mt: 2 }}>
                  Celiac markers: {health.targeted.celiac?.genotype || "—"} / support {health.targeted.celiac_support?.genotype || "—"} ({health.risk_summary?.Celiac || "—"})
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={2} sx={{ mt: 2 }}>
        <Grid item xs={12} md={7}>
          <Card className="section-card">
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                <ColorLensIcon color="primary" />
                <Typography variant='h6'>Trait Studio</Typography>
              </Stack>
              <Grid container spacing={2}>
                {[
                  { label: "Eye color", data: traits.eye_color },
                  { label: "Hair color", data: traits.hair_color },
                  { label: "Skin tone", data: traits.skin_color },
                  { label: "Freckling", data: traits.freckling },
                  { label: "Tanning response", data: traits.tanning_response },
                  { label: "Face shape", data: traits.face_shape },
                  { label: "Lactose tolerance", data: traits.lactose_tolerance },
                  { label: "Caffeine metabolism", data: traits.caffeine_metabolism },
                  { label: "Muscle performance", data: traits.muscle_performance },
                  { label: "Alcohol flush", data: traits.alcohol_flush },
                  { label: "Nicotine dependence", data: traits.nicotine_dependence },
                  { label: "Folate metabolism", data: traits.folate_metabolism },
                ].map(({ label, data: d }) => {
                  const conf = traitConfidence(d);
                  const value = traitValue(d);
                  return (
                    <Grid item xs={12} sm={6} key={label}>
                      <Card variant="outlined" sx={{ borderRadius: 12, height: "100%" }}>
                        <CardContent>
                          <Typography variant='subtitle2' color="text.secondary">{label}</Typography>
                          <Typography variant='h6'>{value}</Typography>
                          {conf && (
                            <Typography variant='body2' color="text.secondary">
                              Confidence: {conf}
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
                <Typography variant='h6'>ClinVar / carrier calls</Typography>
              </Stack>
              {variantRows.length === 0 ? (
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
                    {variantRows.map((v) => (
                      <TableRow key={`${v.rsid}-${v.gene}`}>
                        <TableCell>{v.gene}</TableCell>
                        <TableCell>{v.rsid}</TableCell>
                        <TableCell>{v.variant}</TableCell>
                        <TableCell>{v.genotype || "—"}</TableCell>
                        <TableCell>
                          <Chip
                            label={v.category}
                            color={v.category === "Dominant" ? "secondary" : "default"}
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
            <Typography variant='h6'>Genotype evidence</Typography>
          </Stack>
          <Typography variant='body2' color="text.secondary" sx={{ mb: 1 }}>
            Promethease-like transparency: the SNPs and genotypes behind the calls above.
          </Typography>
          <Divider sx={{ mb: 2 }} />
          {genotypePanel.length === 0 && (
            <Typography color="text.secondary">No key SNPs captured from this file.</Typography>
          )}
          <Stack spacing={2}>
            {genotypePanel.map((block) => (
              <div key={block.title}>
                <Typography variant='subtitle1'>{block.title}</Typography>
                <Typography variant='body2' color="text.secondary">{block.description}</Typography>
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
