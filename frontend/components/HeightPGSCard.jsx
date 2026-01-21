import { Card, CardContent, Typography, Chip, Stack, Box, Divider } from "@mui/material";

function gaussian(x, mean, sd) {
  const coeff = 1 / (sd * Math.sqrt(2 * Math.PI));
  const exponent = -0.5 * Math.pow((x - mean) / sd, 2);
  return coeff * Math.exp(exponent);
}

export default function HeightPGSCard({ result, title }) {
  if (!result) return null;
  const {
    predicted_height_cm_mean,
    predicted_height_cm_sd_total,
    predicted_height_cm_ci90,
    predicted_height_cm_ci95,
    percentile,
    ancestry_confidence,
    warnings = [],
    snp_details = [],
    ancestry_breakdown = {},
    ancestry_height_components = {},
    debug_tools = {},
  } = result;

  const mean = predicted_height_cm_mean;
  const sd = predicted_height_cm_sd_total || 1;
  const minX = mean - 3 * sd;
  const maxX = mean + 3 * sd;

  const points = [];
  const steps = 80;
  let maxY = 0;
  for (let i = 0; i <= steps; i++) {
    const x = minX + (i / steps) * (maxX - minX);
    const y = gaussian(x, mean, sd);
    maxY = Math.max(maxY, y);
    points.push({ x, y });
  }

  const width = 360;
  const height = 180;
  const scaleX = (x) => ((x - minX) / (maxX - minX)) * width;
  const scaleY = (y) => height - (y / maxY) * (height - 20);

  const pathD = points
    .map((p, idx) => `${idx === 0 ? "M" : "L"} ${scaleX(p.x)} ${scaleY(p.y)}`)
    .join(" ");

  const ci90 = [
    { x: predicted_height_cm_ci90.low, label: "CI90 Low" },
    { x: predicted_height_cm_ci90.high, label: "CI90 High" },
  ];

  const ancestryEntries = Object.entries(ancestry_height_components || {});
  const maxComponent = ancestryEntries.reduce((max, [, v]) => Math.max(max, Math.abs(v || 0)), 0) || 1;

  return (
    <Card variant="outlined" sx={{ borderRadius: 2 }}>
      <CardContent>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">{title || "Height Polygenic Score"}</Typography>
          <Chip
            label={`Confidence: ${ancestry_confidence?.tier || "unknown"}`}
            color={ancestry_confidence?.tier === "high" ? "success" : ancestry_confidence?.tier === "moderate" ? "warning" : "default"}
            size="small"
            aria-label={`Confidence tier ${ancestry_confidence?.tier || "unknown"}`}
          />
        </Stack>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          Percentile: {percentile.toFixed(1)} • Mean: {mean.toFixed(1)} cm
        </Typography>
        <Box sx={{ position: "relative", width: "100%", overflowX: "auto", pb: 1 }}>
          <svg width={width} height={height} role="img" aria-label="Height distribution">
            <path d={`${pathD} L ${scaleX(maxX)} ${height} L ${scaleX(minX)} ${height} Z`} fill="#e8ecf6" />
            <path d={pathD} fill="none" stroke="#4b6cb7" strokeWidth="2" />
            <line
              x1={scaleX(mean)}
              x2={scaleX(mean)}
              y1={height}
              y2={scaleY(gaussian(mean, mean, sd))}
              stroke="#d97706"
              strokeWidth="2"
            />
            {ci90.map((ci) => (
              <line
                key={ci.label}
                x1={scaleX(ci.x)}
                x2={scaleX(ci.x)}
                y1={height}
                y2={0}
                stroke="rgba(79,70,229,0.2)"
                strokeWidth="2"
                strokeDasharray="4 4"
              />
            ))}
          </svg>
        </Box>
        <Stack direction="row" spacing={2} sx={{ flexWrap: "wrap", mb: 1 }}>
          <Chip label={`Mean: ${mean.toFixed(1)} cm`} size="small" />
          <Chip label={`CI90: ${predicted_height_cm_ci90.low.toFixed(1)} – ${predicted_height_cm_ci90.high.toFixed(1)} cm`} size="small" />
          <Chip label={`CI95: ${predicted_height_cm_ci95.low.toFixed(1)} – ${predicted_height_cm_ci95.high.toFixed(1)} cm`} size="small" />
        </Stack>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {ancestry_confidence?.reason || "Using default reference."} {ancestry_confidence?.calibration_note || ""}
        </Typography>
        {ancestryEntries.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2">Local ancestry components</Typography>
            {ancestryEntries.map(([label, value]) => (
              <Box key={label} sx={{ display: "flex", alignItems: "center", gap: 1, mt: 0.5 }}>
                <Typography variant="caption" sx={{ width: 48 }}>{label}</Typography>
                <Box sx={{ flexGrow: 1, height: 8, background: "#f1f5f9", borderRadius: 4 }}>
                  <Box
                    sx={{
                      width: `${(Math.abs(value) / maxComponent) * 100}%`,
                      height: "100%",
                      background: "#4b6cb7",
                      borderRadius: 4,
                    }}
                  />
                </Box>
                <Typography variant="caption">{Number(value).toFixed(2)}</Typography>
              </Box>
            ))}
            {Object.keys(ancestry_breakdown || {}).length > 0 && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: "block" }}>
                Global ancestry: {Object.entries(ancestry_breakdown).map(([k, v]) => `${k} ${(v * 100).toFixed(1)}%`).join(" • ")}
              </Typography>
            )}
          </Box>
        )}
        {warnings && warnings.length > 0 && (
          <Box sx={{ mb: 1 }}>
            <Typography variant="subtitle2" color="warning.main">Warnings</Typography>
            {warnings.map((w, idx) => (
              <Typography key={idx} variant="body2" color="text.secondary">• {w}</Typography>
            ))}
          </Box>
        )}
        {debug_tools?.observed_height_cm !== undefined && (
          <Box sx={{ mb: 1 }}>
            <Typography variant="subtitle2">Debug</Typography>
            <Typography variant="body2" color="text.secondary">
              Observed: {Number(debug_tools.observed_height_cm).toFixed(1)} cm ƒ?› Error: {Number(debug_tools.prediction_error_cm).toFixed(1)} cm
            </Typography>
          </Box>
        )}
        {snp_details && snp_details.length > 0 && (
          <Box sx={{ mb: 1 }}>
            <Typography variant="subtitle2">SNPs and genotypes</Typography>
            <Typography variant="caption" color="text.secondary">
              Effect allele dosage shown when available; “imputed” indicates EAF-based fill.
            </Typography>
            <Stack spacing={0.3} sx={{ mt: 0.5 }}>
              {snp_details.map((d, idx) => (
                <Typography key={d.rsid || idx} variant="body2" color="text.secondary">
                  {d.rsid}: {d.genotype || "imputed"} • dosage {d.dosage !== undefined ? Number(d.dosage).toFixed(2) : "n/a"} • effect {d.effect || "?"}
                </Typography>
              ))}
            </Stack>
          </Box>
        )}
        <Divider sx={{ my: 1 }} />
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          Height is influenced by many genes and environment (nutrition, illness, hormones). Results are probabilistic and may err by several cm; performance varies by ancestry. Not medical advice.
        </Typography>
        <details>
          <summary>Learn more</summary>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This polygenic score uses a demo weight set and default reference values (mean 170 cm, genetic SD 6.5 cm). Environment and measurement error add residual variation. Calibration may differ across ancestries; coverage and ambiguous SNP handling affect confidence.
          </Typography>
        </details>
      </CardContent>
    </Card>
  );
}
