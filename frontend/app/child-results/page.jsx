"use client";
import { useEffect, useState } from 'react';
import { Typography, Card, CardContent, Grid, Stack, Chip, LinearProgress } from '@mui/material';
import ChildAvatar from '@/components/ChildAvatar';

export default function ChildResults() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const raw = sessionStorage.getItem("childData");
    if (raw) setData(JSON.parse(raw));
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
  const parentEyeA = parentA?.key_genotypes?.rs12913832;
  const parentEyeB = parentB?.key_genotypes?.rs12913832;
  const parentKeySnpsA = parentA?.key_snps || {};
  const parentKeySnpsB = parentB?.key_snps || {};

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

  const renderSnpPunnett = (traitLabel, snpId, parentAgeno, parentBgeno, colorMap) => {
    if (!parentAgeno || !parentBgeno) return null;

    const allelesFrom = (geno) => (geno || "").replace("/", "").replace("|", "").toUpperCase().split("");
    const aAlleles = allelesFrom(parentAgeno);
    const bAlleles = allelesFrom(parentBgeno);
    if (aAlleles.length < 2 || bAlleles.length < 2) return null;

    const combos = [];
    for (let ai = 0; ai < aAlleles.length; ai++) {
      for (let bi = 0; bi < bAlleles.length; bi++) {
        const childG = [aAlleles[ai], bAlleles[bi]].sort().join("");
        combos.push(childG);
      }
    }
    const total = combos.length;
    const freq = combos.reduce((acc, g) => {
      acc[g] = (acc[g] || 0) + 1;
      return acc;
    }, {});

    const rows = aAlleles.map((a, rowIdx) =>
      bAlleles.map((b, colIdx) => {
        const geno = [a, b].sort().join("");
        const pct = ((freq[geno] || 0) / total) * 100;
        const labelColor = colorMap?.(geno) || "#4b5563";
        return { geno, pct, labelColor };
      })
    );

    const alleleLabel = (allele) => (allele || "").toUpperCase();

    return (
      <Card className="section-card" sx={{ mb:2 }}>
        <CardContent>
          <Typography variant='subtitle1'>{traitLabel} • {snpId}</Typography>
          <Typography variant='caption' color="text.secondary">Parents: {parentAgeno} × {parentBgeno}</Typography>
          <div style={{ display:"grid", gridTemplateColumns:`80px repeat(${bAlleles.length}, 1fr)`, gap:6, alignItems:"center", marginTop:8 }}>
            <div></div>
            {bAlleles.map((b, idx) => (
              <div key={`bhead-${idx}`} style={{ textAlign:"center", fontWeight:700, color:"#6b3b1f" }}>
                {alleleLabel(b)}
              </div>
            ))}
            {aAlleles.map((a, rIdx) => (
              <>
                <div key={`ahead-${rIdx}`} style={{ textAlign:"center", fontWeight:700, color:"#6b3b1f" }}>
                  {alleleLabel(a)}
                </div>
                {rows[rIdx].map((cell, cIdx) => (
                  <div key={`cell-${rIdx}-${cIdx}`} style={{ background:"#f3f4f6", borderRadius:10, padding:10, textAlign:"center", border:"1px solid #e5e7eb" }}>
                    <Typography variant='subtitle2' sx={{ color: cell.labelColor }}>{cell.geno}</Typography>
                    <Typography variant='body2' color="text.secondary">{cell.pct.toFixed(1)}%</Typography>
                  </div>
                ))}
              </>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  };

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

    const allelesFor = (geno) => (geno || "").replace("/", "").replace("|", "").toUpperCase().split("");

    const hapStrings = (skinSet) => {
      const alleleChoices = snpOrder.map((snp) => allelesFor(skinSet[snp]));
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

    const hapA = hapStrings(skinA).slice(0, 8); // cap to keep grid readable
    const hapB = hapStrings(skinB).slice(0, 8);
    if (hapA.length === 0 || hapB.length === 0) return null;

    const score = (hap) => hap.split("").reduce((acc, ch) => acc + (ch === ch.toUpperCase() ? 1 : 0), 0);
    const gradientStops = [
      { stop: 0, color: [246, 203, 150] }, // soft cream highlight
      { stop: 0.5, color: [140, 78, 42] }, // warm mid-tone amber
      { stop: 1, color: [47, 12, 5] },     // deep espresso
    ];

    const lerp = (a, b, t) => Math.round(a + (b - a) * t);

    const shade = (val, maxVal) => {
      const adjustedVal = Math.max(0, val - 2); // shift mapping down by 2
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

    const cells = [];
    let maxVal = 0;
    hapA.forEach((ha) => {
      hapB.forEach((hb) => {
        const combined = ha + hb;
        const val = score(combined);
        maxVal = Math.max(maxVal, val);
        cells.push({ ha, hb, val });
      });
    });

    return (
      <Card className="section-card" sx={{ mb:3 }}>
        <CardContent>
          <Typography variant='h6'>Skin Genotype Heatmap (SLC24A5, MC1R, TYR, OCA2, SLC45A2)</Typography>
          <Typography variant='caption' color="text.secondary">
            Using shared SNPs: {snpOrder.join(", ")}
          </Typography>
          <div style={{ overflowX:"auto", marginTop:10 }}>
            <div style={{ display:"grid", gridTemplateColumns:`120px repeat(${hapB.length}, 100px)`, gap:4, alignItems:"center" }}>
              <div></div>
              {hapB.map((hb, idx) => (
                <div key={`hb-${idx}`} style={{ textAlign:"center", fontWeight:600 }}>{hb}</div>
              ))}
              {hapA.map((ha, rIdx) => (
                <>
                  <div key={`ha-${rIdx}`} style={{ textAlign:"center", fontWeight:600 }}>{ha}</div>
                  {hapB.map((hb, cIdx) => {
                    const cell = cells[rIdx * hapB.length + cIdx];
                    const bg = shade(cell.val, maxVal || snpOrder.length * 2);
                    return (
                      <div key={`cell-${rIdx}-${cIdx}`} style={{
                        background: bg,
                        borderRadius:8,
                        padding:10,
                        textAlign:"center",
                        color:"#111",
                        border:"1px solid rgba(0,0,0,0.08)"
                      }}>
                        <Typography variant='subtitle2'>{cell.val}</Typography>
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

    const allelesFor = (geno) => (geno || "").replace("/", "").replace("|", "").toUpperCase().split("");

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

    const hapA = hapStrings(eyeA).slice(0, 8);
    const hapB = hapStrings(eyeB).slice(0, 8);
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

    const lerp = (a, b, t) => Math.round(a + (b - a) * t);
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

    const blend = (base, overlay, alpha) =>
      base.map((v, idx) => Math.round(v * (1 - alpha) + overlay[idx] * alpha));

    // Genotype-specific effects (brownness axis; positive = browner, negative = bluer)
    const genoEffect = {
      // HERC2 baseline (additive, not a gate): AA > AG > GG
      HERC2_rs12913832: { AA: 5.0, AG: 2.5, GG: -4.0 },
      // Other loci modulate after HERC2; non-zero to avoid collapsing to a constant
      OCA2_rs1800407: { AA: 2.0, AG: 1.0, GG: 0 },
      TYR_rs1126809: { AA: 1.0, AG: 0.6, GG: 0 },
      TYRP1_rs1408799: { AA: 0.8, AG: 0.4, GG: 0 },
      IRF4_rs12203592: { CC: 0.8, CT: 0.4, TT: 0 },
      SLC45A2_rs16891982: { CC: -1.2, CG: -0.8, GG: 0 }, // dilution/lightening
    };

    // No extra bias; relying on explicit genotype effects above for ordering
    const aBiasByHerc2 = { AA: 0, AG: 0, GG: 0 };

    const normalizedGenotype = (rowAllele, colAllele) =>
      [rowAllele.toUpperCase(), colAllele.toUpperCase()].sort().join("");

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
    let minScore = Infinity;
    let maxScore = -Infinity;
    hapA.forEach((ha) => {
      hapB.forEach((hb) => {
        const { score, hercGenotype } = scorePair(ha, hb);
        const roundedScore = parseFloat(score.toFixed(2)); // ensure identical values map to identical colors
        minScore = Math.min(minScore, roundedScore);
        maxScore = Math.max(maxScore, roundedScore);
        cells.push({ ha, hb, score: roundedScore, hercGenotype });
      });
    });

    const shadeEye = (score) => {
      const denom = maxScore === minScore ? 1 : (maxScore - minScore);
      const tLinear = Math.max(0, Math.min(1, (score - minScore) / denom));
      const t = Math.pow(tLinear, 1.6); // nonlinear: low melanin drops faster
      return sampleGradient(gradientStops, t); // higher t -> browner
    };

    // Debug: show relative scores for HERC2 genotypes holding others neutral
    if (typeof window !== "undefined" && !window.__eyeHeatmapDebugged) {
      window.__eyeHeatmapDebugged = true;
      const baseGenos = {
        HERC2_rs12913832: "GG",
        OCA2_rs1800407: "GG",
        SLC45A2_rs16891982: "GG",
        TYR_rs1126809: "GG",
        IRF4_rs12203592: "CC",
        TYRP1_rs1408799: "GG",
      };
      const computeExplicitScore = (hercGeno) => {
        let s = 0;
        s += genoEffect.HERC2_rs12913832[hercGeno];
        s += aBiasByHerc2[hercGeno] || 0;
        s += genoEffect.OCA2_rs1800407[baseGenos.OCA2_rs1800407];
        s += genoEffect.SLC45A2_rs16891982[baseGenos.SLC45A2_rs16891982];
        s += genoEffect.TYR_rs1126809[baseGenos.TYR_rs1126809];
        s += genoEffect.IRF4_rs12203592[baseGenos.IRF4_rs12203592];
        s += genoEffect.TYRP1_rs1408799[baseGenos.TYRP1_rs1408799];
        return s;
      };
      const testScores = {
        AA: computeExplicitScore("AA"),
        AG: computeExplicitScore("AG"),
        GG: computeExplicitScore("GG"),
      };
      if (!(testScores.AA > testScores.AG && testScores.AG > testScores.GG)) {
        throw new Error(`Eye heatmap HERC2 sanity check failed: ${JSON.stringify(testScores)}`);
      }
      console.log("Eye heatmap HERC2 sample scores (AA > AG > GG):", testScores);
    }

    return (
      <Card className="section-card" sx={{ mb:3 }}>
        <CardContent>
          <Typography variant='h6'>Eye Genotype Heatmap (HERC2, OCA2, TYR, SLC45A2, IRF4, TYRP1)</Typography>
          <Typography variant='caption' color="text.secondary">
            Using shared SNPs: {snpOrder.join(", ")}
          </Typography>
          <div style={{ overflowX:"auto", marginTop:10 }}>
            <div style={{ display:"grid", gridTemplateColumns:`120px repeat(${hapB.length}, 100px)`, gap:4, alignItems:"center" }}>
              <div></div>
              {hapB.map((hb, idx) => (
                <div key={`hb-eye-${idx}`} style={{ textAlign:"center", fontWeight:600 }}>{hb}</div>
              ))}
              {hapA.map((ha, rIdx) => (
                <>
                  <div key={`ha-eye-${rIdx}`} style={{ textAlign:"center", fontWeight:600 }}>{ha}</div>
                  {hapB.map((hb, cIdx) => {
                    const cell = cells[rIdx * hapB.length + cIdx];
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

    const allelesFor = (geno) => (geno || "").replace("/", "").replace("|", "").toUpperCase().split("");

    const hapStrings = (hairSet) => {
      const alleleChoices = snpOrder.map((snp) => allelesFor(hairSet[snp]));
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

    const hapA = hapStrings(hairA).slice(0, 8);
    const hapB = hapStrings(hairB).slice(0, 8);
    if (hapA.length === 0 || hapB.length === 0) return null;

    const baseGradientStops = [
      { stop: 0, color: [15, 12, 12] },     // black
      { stop: 0.15, color: [45, 30, 24] },  // espresso
      { stop: 0.3, color: [85, 55, 40] },   // dark brown
      { stop: 0.45, color: [125, 85, 55] }, // medium brown
      { stop: 0.6, color: [165, 120, 70] }, // light brown
      { stop: 0.75, color: [205, 160, 95] },// dark blond
      { stop: 0.9, color: [230, 200, 125] },// blond
      { stop: 1, color: [238, 232, 215] },  // platinum
    ];

    const pheoGradientStops = [
      { stop: 0, color: [45, 20, 15] },     // dark auburn
      { stop: 0.25, color: [95, 45, 30] },  // mahogany
      { stop: 0.45, color: [145, 55, 35] }, // auburn/chestnut
      { stop: 0.6, color: [185, 80, 40] },  // copper
      { stop: 0.8, color: [215, 120, 60] }, // ginger
      { stop: 1, color: [235, 175, 110] },  // strawberry blond
    ];

    const lerp = (a, b, t) => Math.round(a + (b - a) * t);

    const sampleGradient = (stops, t) => {
      const clamped = Math.max(0, Math.min(1, t));
      for (let i = 1; i < stops.length; i++) {
        const prev = stops[i - 1];
        const next = stops[i];
        if (clamped <= next.stop) {
          const localT = (clamped - prev.stop) / (next.stop - prev.stop);
          const color = prev.color.map((c, idx) => lerp(c, next.color[idx], localT));
          return color;
        }
      }
      return stops[stops.length - 1].color;
    };

    const blend = (base, overlay, alpha) =>
      base.map((v, idx) => Math.round(v * (1 - alpha) + overlay[idx] * alpha));

    const toHex = ([r, g, b]) =>
      "#" +
      [r, g, b]
        .map((v) => v.toString(16).padStart(2, "0"))
        .join("")
        .toUpperCase();

    const geneOrder = ["MC1R", "OCA2/HERC2", "KITLG", "SLC45A2", "TYR"];

    const buildHairColorMap = () => {
      const hairMapping = {};
      const enumerate = (idx = 0, current = []) => {
        if (idx === geneOrder.length) {
          const key = current.join(" | ");
          const ccCount = current.filter((g) => g === "CC").length;
          const tDarkLinear = Math.max(0, Math.min(1, ccCount / geneOrder.length));
          const tDark = Math.pow(tDarkLinear, 1.6); // nonlinear melanin response
          const baseColor = sampleGradient(baseGradientStops, tDark);
          const mc1rIsRed = current[0] === "Tt";
          const pheoColor = sampleGradient(pheoGradientStops, tDark);
          const redBlend = mc1rIsRed ? Math.max(0, Math.min(0.75, 0.35 - 0.1 * tDark)) : 0;
          const finalColor = redBlend > 0 ? blend(baseColor, pheoColor, redBlend) : baseColor;
          hairMapping[key] = toHex(finalColor);
          return;
        }
        for (const state of ["CC", "Tt"]) {
          current[idx] = state;
          enumerate(idx + 1, current);
        }
      };
      enumerate();
      return hairMapping;
    };

    const hairColorMap = buildHairColorMap();

    const baseWeights = {
      rs12913832: -2.2, // OCA2/HERC2 lightens
      rs12821256: -1.6, // KITLG blond dilution
      rs16891982: 2.0,  // SLC45A2 pigment intensity (darker)
      rs1042602: 1.3,   // TYR melanin production
    };

    const mc1rWeights = {
      rs1805007: 1.0,
      rs1805008: 1.0,
      rs1805009: 1.0,
    };

    const alleleActivity = (allele, isModifier) => {
      const active = allele === allele.toUpperCase();
      if (isModifier) {
        return active ? 0.8 : 0.45;
      }
      return active ? 1 : 0.55;
    };

    const snpGeneMap = {
      rs1805007: "MC1R",
      rs1805008: "MC1R",
      rs1805009: "MC1R",
      rs12913832: "OCA2/HERC2",
      rs12821256: "KITLG",
      rs16891982: "SLC45A2",
      rs1042602: "TYR",
    };

    const geneStatesForPair = (rowHap, colHap) => {
      const geneScores = geneOrder.reduce((acc, g) => {
        acc[g] = [];
        return acc;
      }, {});
      snpOrder.forEach((snp, idx) => {
        const gene = snpGeneMap[snp];
        if (!gene) return;
        const rowAllele = rowHap[idx] || "";
        const colAllele = colHap[idx] || "";
        const rowAct = alleleActivity(rowAllele, false);
        const colAct = alleleActivity(colAllele, true);
        geneScores[gene].push(rowAct, colAct);
      });

      return geneOrder.map((gene) => {
        const vals = geneScores[gene];
        if (!vals || vals.length === 0) return "Tt";
        const avg = vals.reduce((a, v) => a + v, 0) / vals.length;
        return avg >= 0.7 ? "CC" : "Tt";
      });
    };

    const baseScore = (rowHap, colHap) =>
      rowHap.split("").reduce((acc, ch, idx) => {
        const snp = snpOrder[idx] || "";
        const w = baseWeights[snp];
        if (!w) return acc;
        const rowActive = alleleActivity(ch, false);
        const colAllele = colHap[idx] || "";
        const colActive = alleleActivity(colAllele, true);
        return acc + w * (rowActive + colActive);
      }, 0);

    const pheoScore = (rowHap, colHap) =>
      rowHap.split("").reduce((acc, ch, idx) => {
        const snp = snpOrder[idx] || "";
        const w = mc1rWeights[snp];
        if (!w) return acc;
        const rowActive = alleleActivity(ch, false);
        const colAllele = colHap[idx] || "";
        const colActive = alleleActivity(colAllele, true);
        return acc + w * (rowActive + colActive);
      }, 0);

    const cells = [];
    hapA.forEach((ha) => {
      hapB.forEach((hb) => {
        const baseVal = baseScore(ha, hb);
        const pheoVal = pheoScore(ha, hb);
        const geneStates = geneStatesForPair(ha, hb);
        const geneKey = geneStates.join(" | ");
        const colorHex = hairColorMap[geneKey] || "#cccccc";
        cells.push({ ha, hb, baseVal, pheoVal, displayVal: baseVal + pheoVal, colorHex });
      });
    });

    return (
      <Card className="section-card" sx={{ mb:3 }}>
        <CardContent>
          <Typography variant='h6'>Hair Genotype Heatmap (MC1R, OCA2/HERC2, KITLG, SLC45A2, TYR)</Typography>
          <Typography variant='caption' color="text.secondary">
            Using shared SNPs: {snpOrder.join(", ")}
          </Typography>
          <div style={{ overflowX:"auto", marginTop:10 }}>
            <div style={{ display:"grid", gridTemplateColumns:`120px repeat(${hapB.length}, 100px)`, gap:4, alignItems:"center" }}>
              <div></div>
              {hapB.map((hb, idx) => (
                <div key={`hb-${idx}`} style={{ textAlign:"center", fontWeight:600 }}>{hb}</div>
              ))}
              {hapA.map((ha, rIdx) => (
                <>
                  <div key={`ha-${rIdx}`} style={{ textAlign:"center", fontWeight:600 }}>{ha}</div>
                  {hapB.map((hb, cIdx) => {
                    const cell = cells[rIdx * hapB.length + cIdx];
                    const bg = cell.colorHex;
                    return (
                      <div key={`cell-hair-${rIdx}-${cIdx}`} style={{
                        background: bg,
                        borderRadius:8,
                        padding:10,
                        textAlign:"center",
                        color:"#111",
                        border:"1px solid rgba(0,0,0,0.08)"
                      }}>
                        <Typography variant='subtitle2'>{cell.displayVal.toFixed(2)}</Typography>
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
    { key: "skin_color", label: "Skin tone", value: childTraits.skin_color?.result || childTraits.skin_color },
    { key: "freckling", label: "Freckling", value: childTraits.freckling },
    { key: "tanning_response", label: "Tanning response", value: childTraits.tanning_response },
    { key: "face_shape", label: "Face shape", value: childTraits.face_shape ? JSON.stringify(childTraits.face_shape) : undefined },
    { key: "lactose_tolerance", label: "Lactose tolerance", value: childTraits.lactose_tolerance },
    { key: "caffeine_metabolism", label: "Caffeine metabolism", value: childTraits.caffeine_metabolism },
    { key: "muscle_performance", label: "Muscle performance", value: childTraits.muscle_performance },
    { key: "alcohol_flush", label: "Alcohol flush", value: childTraits.alcohol_flush },
    { key: "nicotine_dependence", label: "Nicotine dependence", value: childTraits.nicotine_dependence },
    { key: "folate_metabolism", label: "Folate metabolism", value: childTraits.folate_metabolism },
  ].filter(t => t.value);

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

      {punnettBlocks.length > 0 && (
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

      {buildEyePunnett()}
      {renderEyeHeatmap()}
      {renderHairHeatmap()}
      {renderSkinHeatmap()}

      <ChildAvatar traits={childTraits || {}} />

      <Card className="section-card" sx={{ mb:3 }}>
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
      </Card>

      <Card sx={{ mb:3 }}>
        <CardContent>
          <Typography variant='h6'>Parent A Summary</Typography>
          <pre>{JSON.stringify(parentA, null, 2)}</pre>
        </CardContent>
      </Card>

      <Card sx={{ mb:3 }}>
        <CardContent>
          <Typography variant='h6'>Parent B Summary</Typography>
          <pre>{JSON.stringify(parentB, null, 2)}</pre>
        </CardContent>
      </Card>
    </div>
  );
}
