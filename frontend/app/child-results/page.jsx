"use client";
import { useEffect, useState } from 'react';
import { Typography, Card, CardContent, Grid, Stack, Chip, LinearProgress, Box, Switch, TextField, FormControlLabel, Button, Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material';
import Link from "next/link";
import ChildAvatar from '@/components/ChildAvatar';
import HeightPGSCard from "@/components/HeightPGSCard";

// ---------------------------------------------
// Color + MC1R red-shift utilities (hair heatmap)
// ---------------------------------------------
const clamp01 = (v) => Math.max(0, Math.min(1, v));

// Converts a hex color string into an RGB tuple.
const hexToRgb = (hex) => {
  const clean = hex.replace("#", "");
  const int = parseInt(clean, 16);
  return [(int >> 16) & 255, (int >> 8) & 255, int & 255];
};

// Converts RGB values into HSL so hue/saturation/lightness can be adjusted independently.
const rgbToHsl = (r, g, b) => {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h, s, l = (max + min) / 2;
  if (max === min) {
    h = s = 0;
  } else {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break;
      case g: h = (b - r) / d + 2; break;
      case b: h = (r - g) / d + 4; break;
      default: h = 0;
    }
    h *= 60;
  }
  return { h, s, l };
};

// Converts HSL values back into RGB values for CSS rendering.
const hslToRgb = (h, s, l) => {
  const c = (1 - Math.abs(2 * l - 1)) * s;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = l - c / 2;
  let r1 = 0, g1 = 0, b1 = 0;
  if (h >= 0 && h < 60) [r1, g1, b1] = [c, x, 0];
  else if (h < 120) [r1, g1, b1] = [x, c, 0];
  else if (h < 180) [r1, g1, b1] = [0, c, x];
  else if (h < 240) [r1, g1, b1] = [0, x, c];
  else if (h < 300) [r1, g1, b1] = [x, 0, c];
  else [r1, g1, b1] = [c, 0, x];
  const r = Math.round((r1 + m) * 255);
  const g = Math.round((g1 + m) * 255);
  const b = Math.round((b1 + m) * 255);
  return [r, g, b];
};

// Estimates MC1R-driven redness intensity from selected MC1R SNP genotypes.
const mc1rRednessFactor = (genotypes = {}) => {
  // Count derived/red-associated alleles (T) across MC1R SNPs (include 5009)
  const mc1rSnps = ["rs1805007", "rs1805008", "rs1805009"];
  let count = 0;
  mc1rSnps.forEach((snp) => {
    const geno = (genotypes[snp] || "").replace("/", "").replace("|", "").toUpperCase();
    count += (geno.match(/T/g) || []).length;
  });
  return clamp01(count / 4); // 0..1
};

// Applies an MC1R-based red hue/saturation shift to a base hair color.
const applyMc1rRedShift = (baseRgb, darknessScore, maxScore, mc1rGenotypes) => {
  const baseHsl = rgbToHsl(baseRgb[0], baseRgb[1], baseRgb[2]);
  const mc1r = mc1rRednessFactor(mc1rGenotypes);
  const darknessNorm = clamp01(darknessScore / Math.max(1, maxScore)); // higher = darker
  const visibility = clamp01(1 - darknessNorm); // red shows in lighter hair
  const finalRedness = mc1r * visibility;

  if (finalRedness <= 0) {
    return `rgb(${baseRgb[0]},${baseRgb[1]},${baseRgb[2]})`;
  }

  const targetHue = 25; // auburn/copper
  const hue = baseHsl.h * (1 - finalRedness) + targetHue * finalRedness;
  const satBoost = 0.18 * finalRedness; // stronger saturation lift for red expression
  const lightBoost = 0.10 * finalRedness * (1 - darknessNorm); // only lifts lighter hair

  const s = clamp01(baseHsl.s + satBoost);
  const l = clamp01(baseHsl.l + lightBoost);
  const [r, g, b] = hslToRgb(hue, s, l);
  return `rgb(${r},${g},${b})`;
};

export default function ChildResults() {
  // Loaded simulation payload for both parents and predicted child outcomes.
  const [data, setData] = useState(null);
  // Initial loading state while reading session data.
  const [loading, setLoading] = useState(true);
  // Toggle for SNP editing/debug-only visual diagnostics.
  const [debugMode, setDebugMode] = useState(false);
  // Expand/collapse state for large heatmaps.
  const [hairHeatmapExpanded, setHairHeatmapExpanded] = useState(false);
  const [skinHeatmapExpanded, setSkinHeatmapExpanded] = useState(false);
  const [eyeHeatmapExpanded, setEyeHeatmapExpanded] = useState(false);
  // Local editable copies of parent SNP sets used in debug mode.
  const [editableSnpsA, setEditableSnpsA] = useState({ eye: {}, hair: {}, skin: {} });
  const [editableSnpsB, setEditableSnpsB] = useState({ eye: {}, hair: {}, skin: {} });

  // Load prediction payload from session storage and initialize editable SNP buffers.
  useEffect(() => {
    const raw = sessionStorage.getItem("childData");
    if (raw) {
      const parsed = JSON.parse(raw);
      setData(parsed);
      if (parsed?.parentA?.key_snps && parsed?.parentB?.key_snps) {
        setEditableSnpsA({
          eye: { ...parsed.parentA.key_snps.eye },
          hair: { ...parsed.parentA.key_snps.hair },
          skin: { ...parsed.parentA.key_snps.skin },
        });
        setEditableSnpsB({
          eye: { ...parsed.parentB.key_snps.eye },
          hair: { ...parsed.parentB.key_snps.hair },
          skin: { ...parsed.parentB.key_snps.skin },
        });
      }
    }
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className='container' style={{ paddingTop: 16 }}>
        <Typography variant='body1' sx={{ mb: 1 }}>Loading results...</Typography>
        <LinearProgress />
      </div>
    );
  }

  if (!data) return <div className='container'>No child prediction data found.</div>;

  const { parentA, parentB, child } = data;
  const childTraits = child?.child_traits || child?.traits || {};
  const distribution = child?.child_trait_distribution || {};
  const childHeight = child?.child_height_pgs;
  const childHeightMale = childHeight?.male;
  const childHeightFemale = childHeight?.female;
  const childHeightDetails = childHeightMale || childHeightFemale || childHeight;
  const parentEyeA = parentA?.key_genotypes?.rs12913832;
  const parentEyeB = parentB?.key_genotypes?.rs12913832;
  const parentKeySnpsA = debugMode ? editableSnpsA : (parentA?.key_snps || {});
  const parentKeySnpsB = debugMode ? editableSnpsB : (parentB?.key_snps || {});

  const normalizeTraitValue = (value) => {
    if (!value) return "N/A";
    if (typeof value === "string") return value;
    if (typeof value === "object" && value.result) return value.result;
    return "N/A";
  };

  // Updates one parent SNP field in the debug editor.
  const updateSnp = (parent, trait, snp, value) => {
    if (parent === "A") {
      setEditableSnpsA((prev) => ({
        ...prev,
        [trait]: { ...(prev[trait] || {}), [snp]: value }
      }));
    } else {
      setEditableSnpsB((prev) => ({
        ...prev,
        [trait]: { ...(prev[trait] || {}), [snp]: value }
      }));
    }
  };

  // Restores editable SNP values back to the original loaded parent SNPs.
  const resetToOriginal = () => {
    if (parentA?.key_snps && parentB?.key_snps) {
      setEditableSnpsA({
        eye: { ...parentA.key_snps.eye },
        hair: { ...parentA.key_snps.hair },
        skin: { ...parentA.key_snps.skin },
      });
      setEditableSnpsB({
        eye: { ...parentB.key_snps.eye },
        hair: { ...parentB.key_snps.hair },
        skin: { ...parentB.key_snps.skin },
      });
    }
  };

  const punnettBlocks = [
    {
      title: "Eye color",
      probs: childTraits.eye_color?.probabilities,
      result: childTraits.eye_color?.result
    },
    {
      title: "Hair color",
      probs: childTraits.hair_color?.probabilities,
      result: childTraits.hair_color?.result
    },
    {
      title: "Skin tone",
      probs: childTraits.skin_color?.probabilities,
      result: childTraits.skin_color?.result
    }
  ].filter(b => b.probs);

  // Renders probability cards for a single trait in a Punnett-style summary block.
  const renderPunnett = (block) => {
    const entries = Object.entries(block.probs || {}).sort((a, b) => b[1] - a[1]);
    return (
      <Card variant="outlined" sx={{ borderRadius: 12, height: "100%" }}>
        <CardContent>
          <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
            <Typography variant='subtitle1'>{block.title}</Typography>
            {block.result && <Chip label={`Predicted: ${block.result}`} size="small" color="primary" />}
          </Stack>
          <Grid container spacing={1}>
            {entries.map(([label, prob]) => (
              <Grid item xs={6} sm={3} key={label}>
                <Card sx={{ background: "#f8fafc", borderRadius: 8 }}>
                  <CardContent sx={{ py: 1.5, textAlign: "center" }}>
                    <Typography variant='subtitle2'>{label}</Typography>
                    <Typography variant='h6'>{(prob * 100).toFixed(1)}%</Typography>
                    <LinearProgress
                      variant="determinate"
                      value={Math.min(100, prob * 100)}
                      sx={{ height: 6, borderRadius: 3, mt: 1 }}
                    />
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>
    );
  };

  // Renders an interactive debug panel for manually editing key SNP inputs.
  const renderDebugPanel = () => {
    const allSnps = {
      eye: ["rs12913832", "rs1800407", "rs1126809", "rs16891982", "rs12203592", "rs1408799"],
      hair: ["rs1805007", "rs1805008", "rs1805009", "rs12821256", "rs12913832", "rs16891982", "rs1042602"],
      skin: ["rs1426654", "rs16891982", "rs1042602", "rs1800407", "rs1805007"],
    };

    return (
      <Card variant="outlined" sx={{ mb: 3, p: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant='h6' color="warning.main">Debug Mode</Typography>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <Button size="small" variant="outlined" onClick={resetToOriginal} disabled={!parentA?.key_snps}>
              Reset to Original
            </Button>
            <FormControlLabel
              control={
                <Switch
                  checked={debugMode}
                  onChange={(e) => setDebugMode(e.target.checked)}
                  color="warning"
                />
              }
              label="Enable Debug"
            />
          </Box>
        </Box>

        <Grid container spacing={3}>
          {Object.entries(allSnps).map(([trait, snps]) => (
            <Grid item xs={12} key={trait}>
              <Card variant="outlined" sx={{ p: 2 }}>
                <Typography variant='subtitle1' sx={{ mb: 2, fontWeight: 600 }}>
                  {trait === "eye" ? "Eye SNPs" : trait === "hair" ? "Hair SNPs" : "Skin SNPs"}
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Typography variant='caption' color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                      Parent A
                    </Typography>
                    <Grid container spacing={1}>
                      {snps.map((snp) => (
                        <Grid item xs={6} sm={4} key={`A-${snp}`}>
                          <TextField
                            label={snp}
                            size="small"
                            fullWidth
                            value={editableSnpsA[trait]?.[snp] || ''}
                            onChange={(e) => updateSnp('A', trait, snp, e.target.value)}
                            placeholder="e.g., AA, AG, GG"
                            sx={{ '& .MuiInputBase-input': { fontSize: '0.75rem' } }}
                          />
                        </Grid>
                      ))}
                    </Grid>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant='caption' color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                      Parent B
                    </Typography>
                    <Grid container spacing={1}>
                      {snps.map((snp) => (
                        <Grid item xs={6} sm={4} key={`B-${snp}`}>
                          <TextField
                            label={snp}
                            size="small"
                            fullWidth
                            value={editableSnpsB[trait]?.[snp] || ''}
                            onChange={(e) => updateSnp('B', trait, snp, e.target.value)}
                            placeholder="e.g., AA, AG, GG"
                            sx={{ '& .MuiInputBase-input': { fontSize: '0.75rem' } }}
                          />
                        </Grid>
                      ))}
                    </Grid>
                  </Grid>
                </Grid>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Card>
    );
  };

  // const renderSnpPunnett = (traitLabel, snpId, parentAgeno, parentBgeno, colorMap) => {
  //   if (!parentAgeno || !parentBgeno) return null;

  //   const allelesFrom = (geno) => (geno || "").replace("/", "").replace("|", "").toUpperCase().split("");
  //   const aAlleles = allelesFrom(parentAgeno);
  //   const bAlleles = allelesFrom(parentBgeno);
  //   if (aAlleles.length < 2 || bAlleles.length < 2) return null;

  //   const combos = [];
  //   for (let ai = 0; ai < aAlleles.length; ai++) {
  //     for (let bi = 0; bi < bAlleles.length; bi++) {
  //       const childG = [aAlleles[ai], bAlleles[bi]].sort().join("");
  //       combos.push(childG);
  //     }
  //   }
  //   const total = combos.length;
  //   const freq = combos.reduce((acc, g) => {
  //     acc[g] = (acc[g] || 0) + 1;
  //     return acc;
  //   }, {});

  //   const rows = aAlleles.map((a, rowIdx) =>
  //     bAlleles.map((b, colIdx) => {
  //       const geno = [a, b].sort().join("");
  //       const pct = ((freq[geno] || 0) / total) * 100;
  //       const labelColor = colorMap?.(geno) || "#4b5563";
  //       return { geno, pct, labelColor };
  //     })
  //   );

  //   const alleleLabel = (allele) => (allele || "").toUpperCase();

  //   return (
  //     <Card className="section-card" sx={{ mb:2 }}>
  //       <CardContent>
  //         <Typography variant='subtitle1'>{traitLabel} • {snpId}</Typography>
  //         <Typography variant='caption' color="text.secondary">Parents: {parentAgeno} × {parentBgeno}</Typography>
  //         <div style={{ display:"grid", gridTemplateColumns:`80px repeat(${bAlleles.length}, 1fr)`, gap:6, alignItems:"center", marginTop:8 }}>
  //           <div></div>
  //           {bAlleles.map((b, idx) => (
  //             <div key={`bhead-${idx}`} style={{ textAlign:"center", fontWeight:700, color:"#6b3b1f" }}>
  //               {alleleLabel(b)}
  //             </div>
  //           ))}
  //           {aAlleles.map((a, rIdx) => (
  //             <>
  //               <div key={`ahead-${rIdx}`} style={{ textAlign:"center", fontWeight:700, color:"#6b3b1f" }}>
  //                 {alleleLabel(a)}
  //               </div>
  //               {rows[rIdx].map((cell, cIdx) => (
  //                 <div key={`cell-${rIdx}-${cIdx}`} style={{ background:"#f3f4f6", borderRadius:10, padding:10, textAlign:"center", border:"1px solid #e5e7eb" }}>
  //                   <Typography variant='subtitle2' sx={{ color: cell.labelColor }}>{cell.geno}</Typography>
  //                   <Typography variant='body2' color="text.secondary">{cell.pct.toFixed(1)}%</Typography>
  //                 </div>
  //               ))}
  //             </>
  //           ))}
  //         </div>
  //       </CardContent>
  //     </Card>
  //   );
  // };

  // Builds and renders a skin-tone heatmap from parent skin-related SNP combinations.
  const renderSkinHeatmap = () => {
    const skinA = parentKeySnpsA.skin;
    const skinB = parentKeySnpsB.skin;
    if (!skinA || !skinB) return null;

    // Target SNPs for skin pigmentation genes
    const targetSnps = [
      "rs1426654", // SLC24A5
      "rs16891982", // SLC45A2
      "rs1042602", // TYR
      "rs1800407", // OCA2
      "rs1805007", // MC1R
    ];

    const snpOrder = targetSnps.filter((snp) => skinA[snp] && skinB[snp]);
    if (snpOrder.length === 0) return null;

    // Standardizes genotype strings into a two-allele array.
    const normalizeGenotype = (geno) => {
      const alleles = (geno || "").toUpperCase().match(/[A-Z]/g) || [];
      return alleles.slice(0, 2);
    };

    // Returns possible gamete alleles and their Mendelian probabilities for one SNP.
    const gametesOneSnp = (geno) => {
      const alleles = normalizeGenotype(geno);
      if (alleles.length < 2) return [];
      if (alleles[0] === alleles[1]) {
        return [{ allele: alleles[0], p: 1 }];
      }
      return [
        { allele: alleles[0], p: 0.5 },
        { allele: alleles[1], p: 0.5 },
      ];
    };

    // Merges duplicate multi-SNP gametes and sums their probabilities.
    const dedupeGametes = (gametes, orderedSnps) => {
      const merged = new Map();
      gametes.forEach((g) => {
        const key = orderedSnps.map((snp) => g.allelesBySnp[snp] || "").join("");
        const prev = merged.get(key);
        if (prev) {
          prev.p += g.p;
          return;
        }
        merged.set(key, { ...g, key });
      });
      return Array.from(merged.values());
    };

    // Builds all parent multi-SNP gametes with probabilities.
    const buildParentGametes = (skinSet, orderedSnps, maxGametes = Number.POSITIVE_INFINITY) => {
      let combos = [{ allelesBySnp: {}, p: 1 }];
      for (const snp of orderedSnps) {
        const gametes = gametesOneSnp(skinSet[snp]);
        if (gametes.length === 0) return [];
        const next = [];
        combos.forEach((combo) => {
          gametes.forEach((g) => {
            next.push({
              allelesBySnp: { ...combo.allelesBySnp, [snp]: g.allele },
              p: combo.p * g.p,
            });
          });
        });
        combos = next;
      }
      const deduped = dedupeGametes(combos, orderedSnps);
      deduped.sort((a, b) => {
        if (b.p !== a.p) return b.p - a.p;
        return a.key.localeCompare(b.key);
      });
      const capped = deduped.slice(0, maxGametes);
      const totalP = capped.reduce((sum, g) => sum + g.p, 0) || 1;
      return capped.map((g) => ({
        ...g,
        p: g.p / totalP,
        label: orderedSnps.map((snp) => g.allelesBySnp[snp] || "?").join(""),
      }));
    };

    // Combines one gamete from each parent into child SNP genotypes.
    const buildChildGenos = (gameteA, gameteB) => {
      const out = {};
      snpOrder.forEach((snp) => {
        const a1 = (gameteA.allelesBySnp[snp] || "").toUpperCase();
        const a2 = (gameteB.allelesBySnp[snp] || "").toUpperCase();
        if (a1 && a2) {
          out[snp] = [a1, a2].sort().join("");
        }
      });
      return out;
    };

    const effectAlleleBySnp = {
      rs1426654: "A",
      rs16891982: "C", 
      rs1042602: "C",
      rs1800407: "C",
      rs1805007: "C", 
    };

    // Resolves the best effect allele to use for each SNP based on observed parent alleles.
    const resolveEffectAllele = (snp, gamA, gamB) => {
      const intended = effectAlleleBySnp[snp];
      const observed = new Set();
      gamA.forEach((g) => g.allelesBySnp[snp] && observed.add(g.allelesBySnp[snp].toUpperCase()));
      gamB.forEach((g) => g.allelesBySnp[snp] && observed.add(g.allelesBySnp[snp].toUpperCase()));
      if (intended && observed.has(intended.toUpperCase())) return intended.toUpperCase();
      const fallbackOrder = ["T", "A", "C", "G"];
      for (const allele of fallbackOrder) {
        if (observed.has(allele)) return allele;
      }
      return observed.values().next().value || null;
    };

    // Counts effect-allele dosage (0/1/2) for a specific child SNP genotype.
    const dosageForSnp = (childGenos, snp, effectAllele) => {
      const effect = effectAllele;
      if (!effect) return 0;
      const geno = (childGenos[snp] || "").toUpperCase();
      return (geno.match(new RegExp(effect, "g")) || []).length;
    };

    // Logistic function used to convert linear score to probability.
    const sigmoid = (x) => 1 / (1 + Math.exp(-x));

    // Estimates probability of lighter skin from weighted SNP dosages.
    const pLightFromGenos = (childGenos, effectAlleles) => {
      // MC1R is excluded from skin lightness by design.
      const b0 = -2.2;
      const betas = {
        rs1426654: 1.6,
        rs16891982: 1.2,
        rs1042602: 0.9,
        rs1800407: 0.3,
      };
      const linear =
        b0 +
        Object.keys(betas).reduce(
          (sum, snp) =>
            sum + betas[snp] * dosageForSnp(childGenos, snp, effectAlleles[snp]),
          0
        );
      return sigmoid(linear);
    };

    const gradientStops = [
  { stop: 0.00, color: [248, 237, 227] }, // very light porcelain white
  { stop: 0.11, color: [242, 222, 203] }, // light peach
  { stop: 0.22, color: [230, 199, 170] }, // light beige
  { stop: 0.33, color: [214, 173, 136] }, // warm light tan
  { stop: 0.44, color: [192, 146, 107] }, // golden tan
  { stop: 0.55, color: [169, 119, 83] },  // medium tan
  { stop: 0.66, color: [140, 94, 63] },   // medium brown
  { stop: 0.77, color: [111, 70, 47] },   // deep brown
  { stop: 0.88, color: [77, 45, 30] },    // very deep brown
  { stop: 1.00, color: [45, 26, 17] },    // ultra-deep eumelanin
    ];

    // Linear interpolation helper used for gradient color sampling.
    const lerp = (a, b, t) => Math.round(a + (b - a) * t);

    // Converts a normalized lightness score to an RGB shade from gradient stops.
    const shade = (val, maxVal) => {
      const adjustedVal = Math.max(0, val ); 
      const tLinear = maxVal === 0 ? 0 : Math.max(0, Math.min(1, adjustedVal / maxVal));
      const t = Math.pow(tLinear, 1.6); // nonlinear: low melanin drops faster
      for (let i = 1; i < gradientStops.length; i++) {
        const prev = gradientStops[i - 1];
        const next = gradientStops[i];
        if (t <= next.stop) {
          const localT = (t - prev.stop) / (next.stop - prev.stop);
          const color = prev.color.map((c, idx) => lerp(c, next.color[idx], localT));
          return `rgb(${color[0]},${color[1]},${color[2]})`;
        }
      }
      const last = gradientStops[gradientStops.length - 1].color;
      return `rgb(${last[0]},${last[1]},${last[2]})`;
    };

    // Debug helper that checks expected Mendelian ratios for a sample cross.
    const findMendelianCheck = () => {
      for (const snp of snpOrder) {
        const a = normalizeGenotype(skinA[snp]);
        const b = normalizeGenotype(skinB[snp]);
        if (a.length < 2 || b.length < 2) continue;
        if (a[0] !== a[1] && b[0] !== b[1]) {
          const sorted = [a[0], a[1]].sort().join("");
          return `Mendelian check (${a[0]}/${a[1]} × ${b[0]}/${b[1]}): 25% ${a[0]}${a[0]}, 50% ${sorted}, 25% ${a[1]}${a[1]}.`;
        }
      }
      return null;
    };

    const gametesA = buildParentGametes(skinA, snpOrder);
    const gametesB = buildParentGametes(skinB, snpOrder);
    if (gametesA.length === 0 || gametesB.length === 0) return null;
    const resolvedEffectAlleles = snpOrder.reduce((acc, snp) => {
      acc[snp] = resolveEffectAllele(snp, gametesA, gametesB);
      return acc;
    }, {});
    const totalCells = gametesA.length * gametesB.length;
    const showToggle = totalCells > 64;
    const displayGametesA = showToggle && !skinHeatmapExpanded ? gametesA.slice(0, 8) : gametesA;
    const displayGametesB = showToggle && !skinHeatmapExpanded ? gametesB.slice(0, 8) : gametesB;

    const cells = [];
    const maxVal = snpOrder.length * 2;
    displayGametesA.forEach((ga) => {
      displayGametesB.forEach((gb) => {
        const childGenos = buildChildGenos(ga, gb);
        const pLight = pLightFromGenos(childGenos, resolvedEffectAlleles);
        const shiftedLight =
          pLight > 0.7 && pLight < 0.99 ? clamp01(pLight - 0.2) : pLight-.10;
        const valForShade = shiftedLight * maxVal;
        cells.push({ ga, gb, pLight, valForShade });
      });
    });

    const mendelianCheck = findMendelianCheck();

    return (
      <Card className="section-card" sx={{ mb:3 }}>
        <CardContent>
          <Typography variant='h6'>Skin Genotype Heatmap (SLC24A5, MC1R, TYR, OCA2, SLC45A2)</Typography>
          <Typography variant='caption' color="text.secondary">
            Using shared SNPs: {snpOrder.join(", ")}
          </Typography>
          {showToggle && (
            <Button
              size="small"
              variant="outlined"
              onClick={() => setSkinHeatmapExpanded((prev) => !prev)}
              sx={{ mt: 1 }}
            >
              {skinHeatmapExpanded ? "Collapse to 64 cells" : "Expand to all cells"}
            </Button>
          )}
          {mendelianCheck && (
            <Typography variant='caption' color="text.secondary" sx={{ display:"block", mt: 0.5 }}>
              {mendelianCheck}
            </Typography>
          )}
          <div style={{ overflowX:"auto", marginTop:10 }}>
            <div style={{ display:"grid", gridTemplateColumns:`120px repeat(${displayGametesB.length}, 100px)`, gap:4, alignItems:"center" }}>
              <div></div>
              {displayGametesB.map((hb, idx) => (
                <div key={`hb-${idx}`} style={{ textAlign:"center", fontWeight:600 }}>{hb.label}</div>
              ))}
              {displayGametesA.map((ha, rIdx) => (
                <>
                  <div key={`ha-${rIdx}`} style={{ textAlign:"center", fontWeight:600 }}>{ha.label}</div>
                  {displayGametesB.map((hb, cIdx) => {
                    const cell = cells[rIdx * displayGametesB.length + cIdx];
                    const bg = shade(cell.valForShade, maxVal);
                    return (
                      <div key={`cell-${rIdx}-${cIdx}`} style={{
                        background: bg,
                        borderRadius:8,
                        padding:10,
                        textAlign:"center",
                        color:"#111",
                        border:"1px solid rgba(0,0,0,0.08)"
                      }}>
                        <Typography variant='subtitle2'>{(cell.pLight * 100).toFixed(1)}%</Typography>
                      </div>
                    );
                  })}
                </>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  // Builds and renders the eye-color heatmap from shared eye SNP haplotypes.
  const renderEyeHeatmap = () => {
    const eyeA = parentKeySnpsA.eye;
    const eyeB = parentKeySnpsB.eye;
    if (!eyeA || !eyeB) return null;

    // Key SNPs mapped to genes in order: HERC2, OCA2, TYR, SLC45A2, IRF4, TYRP1
    const targetSnps = [
      "rs12913832", // HERC2
      "rs1800407",  // OCA2
      "rs1126809",  // TYR
      "rs16891982", // SLC45A2
      "rs12203592", // IRF4
      "rs1408799",  // TYRP1
    ];

    const geneOrder = ["HERC2", "OCA2", "TYR", "SLC45A2", "IRF4", "TYRP1"];
    const snpGeneMap = {
      rs12913832: "HERC2",
      rs1800407: "OCA2",
      rs1126809: "TYR",
      rs16891982: "SLC45A2",
      rs12203592: "IRF4",
      rs1408799: "TYRP1",
    };

    const snpOrder = targetSnps.filter((snp) => eyeA[snp] && eyeB[snp]);
    if (snpOrder.length === 0) return null;

    // Splits genotype text into normalized allele arrays.
    const allelesFor = (geno) => (geno || "").replace("/", "").replace("|", "").toUpperCase().split("");

    // Generates haplotype strings and probabilities from selected eye SNPs.
    const hapStrings = (eyeSet) => {
      const alleleChoices = snpOrder.map((snp) => allelesFor(eyeSet[snp]));
      const combos = alleleChoices.reduce((acc, alleles) => {
        const next = [];
        acc.forEach((prefix) => {
          alleles.forEach((a, idx) => {
            const label = idx === 0 ? a : a.toLowerCase();
            next.push(prefix + label);
          });
        });
        return next;
      }, [""]);
      return combos;
    };

    const hapA = hapStrings(eyeA);
    const hapB = hapStrings(eyeB);
    const totalCells = hapA.length * hapB.length;
    const showToggle = totalCells > 64;
    const displayHapA = showToggle && !eyeHeatmapExpanded ? hapA.slice(0, 8) : hapA;
    const displayHapB = showToggle && !eyeHeatmapExpanded ? hapB.slice(0, 8) : hapB;
    if (hapA.length === 0 || hapB.length === 0) return null;

    // 3-zone palette with narrow hazel band (0.40-0.52)
    const gradientStops = [
      { stop: 0.0, color: [0x5A, 0x7F, 0xA6] }, // blue
      { stop: 0.20, color: [0x7A, 0x8C, 0x9A] }, // gray-blue
      { stop: 0.40, color: [0x6E, 0x7B, 0x4E] }, // muted hazel edge
      { stop: 0.52, color: [0x6B, 0x4A, 0x2D] }, // light brown / hazel
      { stop: 0.70, color: [0x4A, 0x2E, 0x1F] }, // medium brown
      { stop: 1.0, color: [0x2B, 0x1B, 0x12] }, // dark brown
    ];

    // Linear interpolation helper used by color gradient sampling.
    const lerp = (a, b, t) => Math.round(a + (b - a) * t);
    // Samples an RGB color from a stop-based gradient at normalized position t.
    const sampleGradient = (stops, t) => {
      const clamped = Math.max(0, Math.min(1, t));
      for (let i = 1; i < stops.length; i++) {
        const prev = stops[i - 1];
        const next = stops[i];
        if (clamped <= next.stop) {
          const localT = (clamped - prev.stop) / (next.stop - prev.stop);
          return prev.color.map((c, idx) => lerp(c, next.color[idx], localT));
        }
      }
      return stops[stops.length - 1].color;
    };

    // Alpha blends two RGB colors for subtle score-driven tinting.
    const blend = (base, overlay, alpha) =>
      base.map((v, idx) => Math.round(v * (1 - alpha) + overlay[idx] * alpha));

    // Genotype-specific effects (brownness axis; positive = browner, negative = bluer)
    const genoEffect = {
      // HERC2 baseline (additive, not a gate): AA > AG > GG
      HERC2_rs12913832: { AA: 5.0, AG: 2.5, GG: -4.0 },
      // Other loci modulate after HERC2; non-zero to avoid collapsing to a constant
      OCA2_rs1800407: { CC: 2.0, CT: 1.0, TT: 0 },
      TYR_rs1126809: { AA: 1.0, AG: 0.6, GG: 0 },
      TYRP1_rs1408799: { AA: 0.8, AG: 0.4, GG: 0 },
      IRF4_rs12203592: { CC: 0.8, CT: 0.4, TT: 0 },
      SLC45A2_rs16891982: { CC: -1.2, CG: -0.8, GG: 0 }, // dilution/lightening
    };

    // No extra bias; relying on explicit genotype effects above for ordering
    const aBiasByHerc2 = { AA: 0, AG: 0, GG: 0 };

    // Normalizes genotype ordering so equivalent allele pairs compare consistently.
    const normalizedGenotype = (rowAllele, colAllele) =>
      [rowAllele.toUpperCase(), colAllele.toUpperCase()].sort().join("");

    // Scores an eye-color cell from paired parent haplotypes.
    const scorePair = (rowHap, colHap) => {
      let score = 0;
      let herc2Geno = "GG";
      snpOrder.forEach((snp, idx) => {
        const rowAllele = rowHap[idx] || "G";
        const colAllele = colHap[idx] || "G";
        const genoKey = normalizedGenotype(rowAllele, colAllele);
        if (snp === "rs12913832") herc2Geno = genoKey;
        const effectTable = genoEffect[`${snpGeneMap[snp]}_${snp}`];
        if (effectTable && effectTable[genoKey] !== undefined) {
          score += effectTable[genoKey];
        }
      });
      score += aBiasByHerc2[herc2Geno] || 0;
      return { score, hercGenotype: herc2Geno };
    };

    const cells = [];
    displayHapA.forEach((ha) => {
      displayHapB.forEach((hb) => {
        const { score, hercGenotype } = scorePair(ha, hb);
        const roundedScore = parseFloat(score.toFixed(2)); // ensure identical values map to identical colors
        cells.push({ ha, hb, score: roundedScore, hercGenotype });
      });
    });

    const fixedMinScore = -5.2;
    const fixedMaxScore = 5.0;

    // Converts eye score into display colors/labels for the heatmap cell.
    const shadeEye = (score) => {
      const denom = fixedMaxScore - fixedMinScore;
      const tLinear = Math.max(0, Math.min(1, (score - fixedMinScore) / denom));
      const t = Math.pow(tLinear, 1.6); // nonlinear: low melanin drops faster
      return sampleGradient(gradientStops, t); // higher t -> browner
    };

    return (
      <Card className="section-card" sx={{ mb:3 }}>
        <CardContent>
          <Typography variant='h6'>Eye Genotype Heatmap (HERC2, OCA2, TYR, SLC45A2, IRF4, TYRP1)</Typography>
          <Typography variant='caption' color="text.secondary">
            Using shared SNPs: {snpOrder.join(", ")}
          </Typography>
          {showToggle && (
            <Button
              size="small"
              variant="outlined"
              onClick={() => setEyeHeatmapExpanded((prev) => !prev)}
              sx={{ mt: 1 }}
            >
              {eyeHeatmapExpanded ? "Collapse to 64 cells" : "Expand to all cells"}
            </Button>
          )}
          <div style={{ overflowX:"auto", marginTop:10 }}>
            <div style={{ display:"grid", gridTemplateColumns:`120px repeat(${displayHapB.length}, 100px)`, gap:4, alignItems:"center" }}>
              <div></div>
              {displayHapB.map((hb, idx) => (
                <div key={`hb-eye-${idx}`} style={{ textAlign:"center", fontWeight:600 }}>{hb}</div>
              ))}
              {displayHapA.map((ha, rIdx) => (
                <>
                  <div key={`ha-eye-${rIdx}`} style={{ textAlign:"center", fontWeight:600 }}>{ha}</div>
                  {displayHapB.map((hb, cIdx) => {
                    const cell = cells[rIdx * displayHapB.length + cIdx];
                    const rgb = shadeEye(cell.score);
                    const bg = `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`;
                    return (
                      <div key={`cell-eye-${rIdx}-${cIdx}`} style={{
                        background: bg,
                        borderRadius:8,
                        padding:10,
                        textAlign:"center",
                        color:"#111",
                        border:"1px solid rgba(0,0,0,0.08)"
                      }}>
                        <Typography variant='subtitle2'>{cell.score.toFixed(2)}</Typography>
                      </div>
                    );
                  })}
                </>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  // Builds and renders the hair-color heatmap from parent hair SNP gamete combinations.
  const renderHairHeatmap = () => {
    const hairA = parentKeySnpsA.hair;
    const hairB = parentKeySnpsB.hair;
    if (!hairA || !hairB) return null;

    // MC1R drives red, OCA2/HERC2 modulate blond/brown, others tune depth/brightness
    const targetSnps = [
      "rs1805007", // MC1R
      "rs1805008", // MC1R
      "rs1805009", // MC1R
      "rs12821256", // KITLG
      "rs12913832", // OCA2/HERC2 anchor
      "rs16891982", // SLC45A2
      "rs1042602", // TYR
    ];

    const snpOrder = targetSnps.filter((snp) => hairA[snp] && hairB[snp]);
    if (snpOrder.length === 0) return null;

    // Standardizes genotype strings into a two-allele array.
    const normalizeGenotype = (geno) => {
      const alleles = (geno || "").toUpperCase().match(/[A-Z]/g) || [];
      return alleles.slice(0, 2);
    };

    // Returns possible gamete alleles and probabilities for one SNP.
    const gametesOneSnp = (geno) => {
      const alleles = normalizeGenotype(geno);
      if (alleles.length < 2) return [];
      if (alleles[0] === alleles[1]) {
        return [{ allele: alleles[0], p: 1 }];
      }
      return [
        { allele: alleles[0], p: 0.5 },
        { allele: alleles[1], p: 0.5 },
      ];
    };

    // Builds all parent multi-SNP gametes used for the heatmap grid.
    const buildParentGametes = (hairSet, orderedSnps, maxGametes = Number.POSITIVE_INFINITY) => {
      let combos = [{ allelesBySnp: {}, p: 1 }];
      for (const snp of orderedSnps) {
        const gametes = gametesOneSnp(hairSet[snp]);
        if (gametes.length === 0) return [];
        const next = [];
        combos.forEach((combo) => {
          gametes.forEach((g) => {
            next.push({
              allelesBySnp: { ...combo.allelesBySnp, [snp]: g.allele },
              p: combo.p * g.p,
            });
          });
        });
        combos = next;
      }
      combos.sort((a, b) => {
        if (b.p !== a.p) return b.p - a.p;
        const keyA = orderedSnps.map((snp) => a.allelesBySnp[snp] || "").join("");
        const keyB = orderedSnps.map((snp) => b.allelesBySnp[snp] || "").join("");
        return keyA.localeCompare(keyB);
      });
      const capped = combos.slice(0, maxGametes);
      const totalP = capped.reduce((sum, g) => sum + g.p, 0) || 1;
      return capped.map((g) => ({
        ...g,
        p: g.p / totalP,
        label: orderedSnps.map((snp) => g.allelesBySnp[snp] || "?").join(""),
      }));
    };

    // Combines a parent A and parent B gamete into child SNP genotypes.
    const buildChildGenos = (gameteA, gameteB) => {
      const out = {};
      snpOrder.forEach((snp) => {
        const a1 = (gameteA.allelesBySnp[snp] || "").toUpperCase();
        const a2 = (gameteB.allelesBySnp[snp] || "").toUpperCase();
        if (a1 && a2) {
          out[snp] = [a1, a2].sort().join("");
        }
      });
      return out;
    };

    // Logistic function used by probabilistic score transforms.
    const sigmoid = (x) => 1 / (1 + Math.exp(-x));

    const effectAlleleBySnp = {
      // Placeholder effect alleles used for dosage-based probabilities.
      rs1805007: "T",
      rs1805008: "T",
      rs1805009: "T",
      rs12913832: "A",
      rs12821256: "T",
      rs16891982: "C",
      rs1042602: "A",
    };

    // Counts effect-allele dosage for a specific SNP genotype.
    const dosageForSnp = (childGenos, snp) => {
      const effect = effectAlleleBySnp[snp];
      if (!effect) return 0;
      const geno = (childGenos[snp] || "").toUpperCase();
      return (geno.match(new RegExp(effect, "g")) || []).length;
    };

    const redWeights = {
      rs1805007: 1.2,
      rs1805008: 1.1,
      rs1805009: 1.0,
    };
    const redBias = -2.2;

    const lightWeights = {
      rs12913832: 1.4,
      rs12821256: 1.0,
      rs16891982: 1.1,
      rs1042602: 0.9,
    };
    const lightBias = -1.6;

    // Converts genotype-derived scores into class probabilities (softmax).
    const classProbs = (childGenos) => {
      const redScore =
        redBias +
        Object.keys(redWeights).reduce(
          (sum, snp) => sum + redWeights[snp] * dosageForSnp(childGenos, snp),
          0
        );
      const lightScore =
        lightBias +
        Object.keys(lightWeights).reduce(
          (sum, snp) => sum + lightWeights[snp] * dosageForSnp(childGenos, snp),
          0
        );
      const pigmentScore =
        0.8 * dosageForSnp(childGenos, "rs16891982") +
        0.6 * dosageForSnp(childGenos, "rs1042602");
      const darknessScore = -lightScore + 0.4 * pigmentScore;

      const classScores = {
        black: 1.3 * darknessScore + 0.4 * pigmentScore - 0.9 * redScore,
        brown: 0.9 * darknessScore + 0.2 * pigmentScore - 0.6 * redScore,
        blonde: 1.2 * lightScore - 0.7 * redScore,
        red: 1.3 * redScore + 0.2 * darknessScore - 0.5 * lightScore,
        orange: 1.0 * redScore + 0.4 * lightScore - 0.2 * darknessScore,
        strawberry_blonde: 0.8 * redScore + 0.8 * lightScore - 0.2 * darknessScore,
      };

      const maxScore = Math.max(...Object.values(classScores));
      const expScores = Object.fromEntries(
        Object.entries(classScores).map(([k, v]) => [k, Math.exp(v - maxScore)])
      );
      const total = Object.values(expScores).reduce((sum, v) => sum + v, 0) || 1;
      return Object.fromEntries(
        Object.entries(expScores).map(([k, v]) => [k, v / total])
      );
    };

    // Debug helper for one-SNP Mendelian child genotype distribution.
    const singleSnpChildDistribution = (genoA, genoB) => {
      const dist = {};
      const gA = gametesOneSnp(genoA);
      const gB = gametesOneSnp(genoB);
      gA.forEach((ga) => {
        gB.forEach((gb) => {
          const child = [ga.allele, gb.allele].sort().join("");
          dist[child] = (dist[child] || 0) + ga.p * gb.p;
        });
      });
      return dist;
    };

    const gametesA = buildParentGametes(hairA, snpOrder);
    const gametesB = buildParentGametes(hairB, snpOrder);
    if (gametesA.length === 0 || gametesB.length === 0) return null;

    const totalCells = gametesA.length * gametesB.length;
    const showToggle = totalCells > 64;
    const displayGametesA = showToggle && !hairHeatmapExpanded ? gametesA.slice(0, 8) : gametesA;
    const displayGametesB = showToggle && !hairHeatmapExpanded ? gametesB.slice(0, 8) : gametesB;

    const classColors = {
      black: [224, 190, 120],
      brown: [98, 60, 38],
      blonde: [20, 16, 14],
      red: [170, 60, 35],
      orange: [210, 110, 45],
      strawberry_blonde: [235, 175, 110],
    };
    const brownAnchor = [140, 95, 60];
    const darkBrownAnchor = [70, 45, 30];

    // Color interpolation helpers for probability-based cell tinting.
    const lerp = (a, b, t) => Math.round(a + (b - a) * t);
    const mix = (a, b, t) => a.map((v, idx) => lerp(v, b[idx], clamp01(t)));
    // Tints each class color by confidence to keep uncertain cells muted.
    const probabilityTint = (baseRgb, prob, classKey) => {
      const t = clamp01(prob);
      if (classKey === "black") {
        return mix(darkBrownAnchor, baseRgb, t);
      }
      if (classKey === "blonde") {
        return mix(brownAnchor, baseRgb, t);
      }
      return mix(brownAnchor, baseRgb, t);
    };

    const cells = [];
    displayGametesA.forEach((ga) => {
      displayGametesB.forEach((gb) => {
        const childGenos = buildChildGenos(ga, gb);
        const probs = classProbs(childGenos);
        const topEntry = Object.entries(probs).sort((a, b) => b[1] - a[1])[0];
        const topClass = topEntry[0];
        const topProb = topEntry[1];
        const pPair = ga.p * gb.p;
        cells.push({
          ha: ga.label,
          hb: gb.label,
          pPair,
          probs,
          topClass,
          topProb,
          childGenos,
        });
      });
    });

    const mendelianCheck = singleSnpChildDistribution("A/G", "A/G");

    return (
      <Card className="section-card" sx={{ mb:3 }}>
        <CardContent>
          <Typography variant='h6'>Hair Genotype Heatmap (Most likely hair color)</Typography>
          <Typography variant='caption' color="text.secondary">
            Using shared SNPs: {snpOrder.join(", ")}
          </Typography>
          {showToggle && (
            <Button
              size="small"
              variant="outlined"
              onClick={() => setHairHeatmapExpanded((prev) => !prev)}
              sx={{ mt: 1 }}
            >
              {hairHeatmapExpanded ? "Collapse to 64 cells" : "Expand to all cells"}
            </Button>
          )}
          {debugMode && mendelianCheck && (
            <Typography variant='caption' color="text.secondary" sx={{ display: "block", mt: 0.5 }}>
              Mendelian check (A/G × A/G): AA {(mendelianCheck.AA * 100).toFixed(0)}%, AG {(mendelianCheck.AG * 100).toFixed(0)}%, GG {(mendelianCheck.GG * 100).toFixed(0)}%.
            </Typography>
          )}
          <div style={{ overflowX:"auto", marginTop:10 }}>
            <div style={{ display:"grid", gridTemplateColumns:`120px repeat(${displayGametesB.length}, 100px)`, gap:4, alignItems:"center" }}>
              <div></div>
              {displayGametesB.map((hb, idx) => (
                <div key={`hb-${idx}`} style={{ textAlign:"center", fontWeight:600 }}>{hb.label}</div>
              ))}
              {displayGametesA.map((ha, rIdx) => (
                <>
                  <div key={`ha-${rIdx}`} style={{ textAlign:"center", fontWeight:600 }}>{ha.label}</div>
                  {displayGametesB.map((hb, cIdx) => {
                    const cell = cells[rIdx * displayGametesB.length + cIdx];
                    const baseRgb = classColors[cell.topClass] || [200, 200, 200];
                    const shaded = probabilityTint(baseRgb, cell.topProb, cell.topClass);
                    const bg = `rgb(${shaded[0]},${shaded[1]},${shaded[2]})`;
                    return (
                      <div key={`cell-hair-${rIdx}-${cIdx}`} style={{
                        background: bg,
                        borderRadius:8,
                        padding:10,
                        textAlign:"center",
                        color:"#111",
                        border:"1px solid rgba(0,0,0,0.08)"
                      }}>
                        <Typography variant='caption' color="text.secondary">
                          {(cell.topProb * 100).toFixed(1)}%
                        </Typography>
                      </div>
                    );
                  })}
                </>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  // Renders compact SNP-level Punnett cards for top SNPs in each trait group.
  const snpPunnetts = () => {
    const cards = [];
    const traitSnps = [
      { trait: "Eye color", list: parentKeySnpsA.eye, listB: parentKeySnpsB.eye },
      { trait: "Hair color", list: parentKeySnpsA.hair, listB: parentKeySnpsB.hair },
      { trait: "Skin tone", list: parentKeySnpsA.skin, listB: parentKeySnpsB.skin },
    ];
    traitSnps.forEach(({ trait, list, listB }) => {
      if (!list || !listB) return;
      const snps = Object.keys(list).filter((snp) => listB[snp]).slice(0, 5);
      if (snps.length === 0) return;
      cards.push(
        <Card className="section-card" sx={{ mb:3 }} key={trait}>
          <CardContent>
            <Typography variant='h6'>{trait} genotype Punnetts (top SNPs)</Typography>
            {snps.map((snp) =>
              renderSnpPunnett(
                trait,
                snp,
                list[snp],
                listB[snp],
                (geno) => (geno.includes("A") ? "#6b3b1f" : "#2c7edb")
              )
            )}
          </CardContent>
        </Card>
      );
    });
    return cards;
  };
  // Builds a classic 2x2 Punnett grid for rs12913832 eye genotype inheritance.
  const buildEyePunnett = () => {
    if (!parentEyeA || !parentEyeB) return null;

    const allelesFrom = (geno) => (geno || "").replace("/", "").replace("|", "").toUpperCase().split("");
    const a1 = allelesFrom(parentEyeA);
    const b1 = allelesFrom(parentEyeB);
    if (a1.length < 2 || b1.length < 2) return null;

    const combos = [];
    for (let ia = 0; ia < a1.length; ia++) {
      for (let ib = 0; ib < b1.length; ib++) {
        const childGeno = [a1[ia], b1[ib]].sort().join("");
        combos.push({ childGeno, ia, ib });
      }
    }
    const total = combos.length;
    const colorLabel = (geno) => (geno.includes("A") ? "Brown" : "Blue");
    const alleleLabel = (allele) => (allele === "A" ? "B" : "b");

    // Build matrix 2x2 with headers like visual Punnett
    return (
      <Card className="section-card" sx={{ mb:3 }}>
        <CardContent>
          <Typography variant='h6' gutterBottom>Eye Genotype Punnett (rs12913832)</Typography>
          <Typography variant='body2' color="text.secondary" sx={{ mb:2 }}>
            Parent genotypes: {parentEyeA} × {parentEyeB}
          </Typography>
          <div style={{ display:"grid", gridTemplateColumns:"80px repeat(2, 1fr)", gap:6, alignItems:"center" }}>
            <div></div>
            {b1.map((b, idx) => (
              <div key={`bhead-${idx}`} style={{ textAlign:"center", fontWeight:700, color:b==="A"?"#6b3b1f":"#2c7edb" }}>
                {alleleLabel(b)}
              </div>
            ))}
            {a1.map((a, rowIdx) => (
              <>
                <div key={`ahead-${rowIdx}`} style={{ textAlign:"center", fontWeight:700, color:a==="A"?"#6b3b1f":"#2c7edb" }}>
                  {alleleLabel(a)}
                </div>
                {b1.map((b, colIdx) => {
                  const geno = [a, b].sort().join("");
                  const pct = combos.filter(c => c.childGeno === geno).length / total * 100;
                  const eyeColor = colorLabel(geno) === "Brown" ? "#6b3b1f" : "#2c7edb";
                  return (
                    <div key={`cell-${rowIdx}-${colIdx}`} style={{
                      background:"#f3f4f6",
                      borderRadius:10,
                      padding:10,
                      textAlign:"center",
                      border:"1px solid #e5e7eb"
                    }}>
                      <div style={{
                        display:"flex",
                        justifyContent:"center",
                        alignItems:"center",
                        gap:6,
                        marginBottom:6
                      }}>
                        <div style={{
                          width:38,
                          height:24,
                          borderRadius:"50%",
                          background:"#fff",
                          border:"1px solid #d1d5db",
                          display:"flex",
                          justifyContent:"center",
                          alignItems:"center"
                        }}>
                          <div style={{
                            width:14,
                            height:14,
                            borderRadius:"50%",
                            background: eyeColor,
                            boxShadow:"0 0 0 4px rgba(0,0,0,0.15)"
                          }}></div>
                        </div>
                        <div style={{ fontSize:18, fontWeight:700, color:"#4b5563" }}>
                          {alleleLabel(a)}{alleleLabel(b)}
                        </div>
                      </div>
                      <Typography variant='body2' color="text.secondary" sx={{ lineHeight:1.2 }}>
                        {colorLabel(geno)} • {pct.toFixed(1)}%
                      </Typography>
                    </div>
                  );
                })}
              </>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  };

  const allTraits = [
    { key: "eye_color", label: "Eye color", value: childTraits.eye_color?.result || childTraits.eye_color },
    { key: "hair_color", label: "Hair color", value: childTraits.hair_color?.result || childTraits.hair_color },
    { key: "freckling", label: "Freckling", value: childTraits.freckling },
    { key: "tanning_response", label: "Tanning response", value: childTraits.tanning_response },
    { key: "lactose_tolerance", label: "Lactose tolerance", value: childTraits.lactose_tolerance },
    { key: "caffeine_metabolism", label: "Caffeine metabolism", value: childTraits.caffeine_metabolism },
    { key: "muscle_performance", label: "Muscle performance", value: childTraits.muscle_performance },
    { key: "alcohol_flush", label: "Alcohol flush", value: childTraits.alcohol_flush },
    { key: "nicotine_dependence", label: "Nicotine dependence", value: childTraits.nicotine_dependence },
    { key: "folate_metabolism", label: "Folate metabolism", value: childTraits.folate_metabolism },
  ].filter(t => t.value);

  const comparisonRows = [
    {
      label: "Eye color",
      parentA: normalizeTraitValue(parentA?.traits?.eye_color),
      parentB: normalizeTraitValue(parentB?.traits?.eye_color),
      child: normalizeTraitValue(childTraits.eye_color),
    },
    {
      label: "Hair color",
      parentA: normalizeTraitValue(parentA?.traits?.hair_color),
      parentB: normalizeTraitValue(parentB?.traits?.hair_color),
      child: normalizeTraitValue(childTraits.hair_color),
    },
    {
      label: "Skin tone",
      parentA: normalizeTraitValue(parentA?.traits?.skin_color),
      parentB: normalizeTraitValue(parentB?.traits?.skin_color),
      child: normalizeTraitValue(childTraits.skin_color),
    },
    {
      label: "Freckling",
      parentA: normalizeTraitValue(parentA?.traits?.freckling),
      parentB: normalizeTraitValue(parentB?.traits?.freckling),
      child: normalizeTraitValue(childTraits.freckling),
    },
    {
      label: "Tanning response",
      parentA: normalizeTraitValue(parentA?.traits?.tanning_response),
      parentB: normalizeTraitValue(parentB?.traits?.tanning_response),
      child: normalizeTraitValue(childTraits.tanning_response),
    },
    {
      label: "Muscle performance",
      parentA: normalizeTraitValue(parentA?.traits?.muscle_performance),
      parentB: normalizeTraitValue(parentB?.traits?.muscle_performance),
      child: normalizeTraitValue(childTraits.muscle_performance),
    },
    {
      label: "Caffeine metabolism",
      parentA: normalizeTraitValue(parentA?.traits?.caffeine_metabolism),
      parentB: normalizeTraitValue(parentB?.traits?.caffeine_metabolism),
      child: normalizeTraitValue(childTraits.caffeine_metabolism),
    },
  ];

  const riskComparisonRows = [
    "Alzheimers",
    "Diabetes",
    "HeartDisease",
    "Obesity",
    "Celiac",
    "Hypertension",
    "Hemochromatosis",
  ].map((riskKey) => ({
    label: riskKey,
    parentA: parentA?.health?.risk_summary?.[riskKey] || "N/A",
    parentB: parentB?.health?.risk_summary?.[riskKey] || "N/A",
  }));

  const keySnpComparisonRows = [
    { rsid: "rs12913832", gene: "HERC2/OCA2", parentA: parentA?.key_snps?.eye?.rs12913832 || "N/A", parentB: parentB?.key_snps?.eye?.rs12913832 || "N/A" },
    { rsid: "rs1805007", gene: "MC1R", parentA: parentA?.key_snps?.hair?.rs1805007 || "N/A", parentB: parentB?.key_snps?.hair?.rs1805007 || "N/A" },
    { rsid: "rs1805008", gene: "MC1R", parentA: parentA?.key_snps?.hair?.rs1805008 || "N/A", parentB: parentB?.key_snps?.hair?.rs1805008 || "N/A" },
    { rsid: "rs1426654", gene: "SLC24A5", parentA: parentA?.key_snps?.skin?.rs1426654 || "N/A", parentB: parentB?.key_snps?.skin?.rs1426654 || "N/A" },
    { rsid: "rs16891982", gene: "SLC45A2", parentA: parentA?.key_snps?.skin?.rs16891982 || "N/A", parentB: parentB?.key_snps?.skin?.rs16891982 || "N/A" },
  ];

  // Renders probability chips for a trait's distribution object.
  const renderDistChips = (traitKey) => {
    const dist = distribution[traitKey];
    if (!dist) return null;
    const entries = Object.entries(dist).sort((a,b)=>b[1]-a[1]);
    return (
      <div style={{ marginTop: 6, display:"flex", flexWrap:"wrap", gap:6 }}>
        {entries.map(([k,v])=>(
          <Chip key={k} label={`${k}: ${(v*100).toFixed(1)}%`} size="small" />
        ))}
      </div>
    );
  };

  return (
    <div className='container'>
      <Typography variant='h4' gutterBottom>Child Predictor Results</Typography>
      
      {renderDebugPanel()}

      <Card className="section-card" sx={{ mb:3 }}>
        <CardContent>
          <Typography variant='h6' gutterBottom>Quick Summary</Typography>
          <Typography variant='body2' color="text.secondary" sx={{ mb: 1 }}>
            A plain-language overview of key predictions. These are probabilistic and not medical advice.
          </Typography>
          <Stack spacing={0.5}>
            <Typography variant='body1'>
              • Eye color: {childTraits.eye_color?.result || "N/A"}
            </Typography>
            <Typography variant='body1'>
              • Hair color: {childTraits.hair_color?.result || "N/A"}
            </Typography>
            <Typography variant='body1'>
              • Skin tone: {childTraits.skin_color?.result || "N/A"}
            </Typography>
            {childHeightMale?.predicted_height_cm_mean !== undefined && (
              <Typography variant='body1'>
                Male projected height: {childHeightMale.predicted_height_cm_mean.toFixed(1)} cm (90% range {childHeightMale.predicted_height_cm_ci90.low.toFixed(1)} to {childHeightMale.predicted_height_cm_ci90.high.toFixed(1)} cm), percentile {childHeightMale.percentile.toFixed(1)}%.
              </Typography>
            )}
            {childHeightFemale?.predicted_height_cm_mean !== undefined && (
              <Typography variant='body1'>
                Female projected height: {childHeightFemale.predicted_height_cm_mean.toFixed(1)} cm (90% range {childHeightFemale.predicted_height_cm_ci90.low.toFixed(1)} to {childHeightFemale.predicted_height_cm_ci90.high.toFixed(1)} cm), percentile {childHeightFemale.percentile.toFixed(1)}%.
              </Typography>
            )}
            {child?.child_genome && (
              <Typography variant='body2' sx={{ mt: 1 }}>
                Key SNPs (child genotype):
                <br />
                Eye: rs12913832 {child.child_genome["rs12913832"]?.genotype || "NA"}; rs1800407 {child.child_genome["rs1800407"]?.genotype || "NA"}
                <br />
                Hair: rs1805007 {child.child_genome["rs1805007"]?.genotype || "NA"}; rs1805008 {child.child_genome["rs1805008"]?.genotype || "NA"}; rs12821256 {child.child_genome["rs12821256"]?.genotype || "NA"}
                <br />
                Skin: rs1426654 {child.child_genome["rs1426654"]?.genotype || "NA"}; rs16891982 {child.child_genome["rs16891982"]?.genotype || "NA"}; rs1042602 {child.child_genome["rs1042602"]?.genotype || "NA"}
                {childHeightDetails?.snp_details && childHeightDetails.snp_details.length > 0 && (
                  <>
                    <br />
                    Height SNPs:
                    <br />
                    {childHeightDetails.snp_details.map((d, idx) => (
                      <span key={d.rsid || idx}>
                        {d.rsid}: {d.genotype || "imputed"} (dosage {d.dosage !== undefined ? d.dosage.toFixed(2) : "n/a"}){idx < childHeightDetails.snp_details.length - 1 ? "; " : ""}
                      </span>
                    ))}
                  </>
                )}
              </Typography>
            )}
          </Stack>
          <Typography variant='caption' color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            Many factors (environment, nutrition, health) influence these traits; values are estimates, not guarantees.
          </Typography>
        </CardContent>
      </Card>

      <Card className="section-card" sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant='h6' gutterBottom>Side-by-side comparison</Typography>
          <Typography variant='body2' color="text.secondary" sx={{ mb: 2 }}>
            Compare parent trait calls, risk summaries, and a small set of key SNPs in one place.
          </Typography>

          <Typography variant='subtitle1' sx={{ mb: 1 }}>Trait comparison</Typography>
          <Table size="small" sx={{ mb: 3 }}>
            <TableHead>
              <TableRow>
                <TableCell>Signal</TableCell>
                <TableCell>Parent A</TableCell>
                <TableCell>Parent B</TableCell>
                <TableCell>Predicted child</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {comparisonRows.map((row) => (
                <TableRow key={row.label}>
                  <TableCell>{row.label}</TableCell>
                  <TableCell>{row.parentA}</TableCell>
                  <TableCell>{row.parentB}</TableCell>
                  <TableCell>{row.child}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant='subtitle1' sx={{ mb: 1 }}>Risk summary comparison</Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Risk</TableCell>
                    <TableCell>Parent A</TableCell>
                    <TableCell>Parent B</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {riskComparisonRows.map((row) => (
                    <TableRow key={row.label}>
                      <TableCell>{row.label}</TableCell>
                      <TableCell>{row.parentA}</TableCell>
                      <TableCell>{row.parentB}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant='subtitle1' sx={{ mb: 1 }}>Key SNP comparison</Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Marker</TableCell>
                    <TableCell>Parent A</TableCell>
                    <TableCell>Parent B</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {keySnpComparisonRows.map((row) => (
                    <TableRow key={row.rsid}>
                      <TableCell>{row.gene} ({row.rsid})</TableCell>
                      <TableCell>{row.parentA}</TableCell>
                      <TableCell>{row.parentB}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card className="section-card" sx={{ mb:3 }}>
        <CardContent>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Box>
              <Typography variant='h6'>Height Polygenic Score</Typography>
              <Typography variant='body2' color="text.secondary">
                Compute a height PGS from a single raw DNA file and view the bell-curve card. Below shows the child's simulated height PGS if available.
              </Typography>
            </Box>
            {/* Height tab link removed */}
          </Stack>
          {childHeightMale?.pgs_raw !== undefined && (
            <Box sx={{ mt: 2 }}>
              <HeightPGSCard result={childHeightMale} title="Height Polygenic Score (Male)" />
            </Box>
          )}
          {childHeightFemale?.pgs_raw !== undefined && (
            <Box sx={{ mt: 2 }}>
              <HeightPGSCard result={childHeightFemale} title="Height Polygenic Score (Female)" />
            </Box>
          )}
        </CardContent>
      </Card>

      {/* {punnettBlocks.length > 0 && (
        <Card className="section-card" sx={{ mb:3 }}>
          <CardContent>
            <Typography variant='h6' gutterBottom>Punnett-style view</Typography>
            <Typography variant='body2' color="text.secondary" sx={{ mb: 2 }}>
              Each square reflects the probability for a phenotype outcome, similar to a Punnett grid.
            </Typography>
            <Grid container spacing={2}>
              {punnettBlocks.map((block) => (
                <Grid item xs={12} md={4} key={block.title}>
                  {renderPunnett(block)}
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      )}

      {buildEyePunnett()} */}
      {renderEyeHeatmap()}
      {renderHairHeatmap()}
      {renderSkinHeatmap()}

      <ChildAvatar traits={childTraits || {}} />

      {/* <Card className="section-card" sx={{ mb:3 }}>
        <CardContent>
          <Typography variant='h6' gutterBottom>All Trait Calls</Typography>
          <Grid container spacing={2}>
            {allTraits.map((t) => (
              <Grid item xs={12} sm={6} md={4} key={t.label}>
                <Card variant="outlined" sx={{ borderRadius: 10 }}>
                  <CardContent>
                    <Typography variant='subtitle2' color="text.secondary">{t.label}</Typography>
                    <Typography variant='h6'>{t.value}</Typography>
                    {renderDistChips(t.key)}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card> */}
    </div>
  );
}
