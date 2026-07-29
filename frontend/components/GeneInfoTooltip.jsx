"use client";

import { Link, Stack, Tooltip, Typography } from "@mui/material";

const GENE_DETAILS = {
  HERC2: "Regulates pigmentation partly by controlling OCA2 expression; variants near HERC2 strongly influence eye color.",
  OCA2: "Encodes a melanosomal protein involved in melanin production and variation in eye, skin, and hair color.",
  MC1R: "Controls melanocyte pigment signaling; variants are associated with red hair and differences in skin pigmentation.",
  SLC24A5: "Encodes a melanosomal ion exchanger with a major role in human skin pigmentation.",
  SLC45A2: "Helps regulate melanosome function and contributes to skin, hair, and eye pigmentation.",
  APOE: "Encodes a lipid-transport protein; common variants influence cholesterol handling and Alzheimer disease risk.",
  ABO: "Encodes a glycosyltransferase that determines the A, B, AB, or O blood group.",
  RHD: "Encodes the RhD red-cell antigen used to classify blood as Rh positive or Rh negative.",
  HFE: "Helps regulate iron absorption; some variants are associated with hereditary hemochromatosis.",
  LCT: "Encodes lactase, the enzyme that digests lactose.",
};

function splitGenes(gene) {
  return String(gene || "").split("/").map((value) => value.trim()).filter(Boolean);
}

export default function GeneInfoTooltip({ gene, snps = [], children }) {
  const genes = splitGenes(gene);
  const uniqueSnps = [...new Set(snps.filter(Boolean))];
  const title = (
    <Stack spacing={0.75} sx={{ maxWidth: 360, p: 0.5 }}>
      {genes.map((symbol) => (
        <div key={symbol}>
          <Link
            href={`https://www.ncbi.nlm.nih.gov/gene/?term=${encodeURIComponent(`${symbol}[sym] AND human[orgn]`)}`}
            target="_blank"
            rel="noopener noreferrer"
            color="inherit"
            fontWeight={700}
          >
            {symbol}
          </Link>
          <Typography variant="caption" display="block">
            {GENE_DETAILS[symbol] || "A gene represented in this report's supported variant panel."}
          </Typography>
        </div>
      ))}
      {uniqueSnps.length > 0 && (
        <div>
          <Typography variant="caption" fontWeight={700}>SNPs</Typography>
          <Stack direction="row" gap={1} flexWrap="wrap">
            {uniqueSnps.map((rsid) => (
              <Link
                key={rsid}
                href={`https://www.ncbi.nlm.nih.gov/snp/${encodeURIComponent(rsid)}`}
                target="_blank"
                rel="noopener noreferrer"
                color="inherit"
                onClick={(event) => event.stopPropagation()}
              >
                {rsid}
              </Link>
            ))}
          </Stack>
        </div>
      )}
    </Stack>
  );

  return (
    <Tooltip title={title} arrow enterTouchDelay={0} leaveDelay={250}>
      <span style={{ cursor: "help", textDecoration: "underline dotted", textUnderlineOffset: 3 }}>
        {children || gene}
      </span>
    </Tooltip>
  );
}
