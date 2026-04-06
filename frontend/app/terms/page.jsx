"use client";

import { Card, CardContent, Stack, Typography } from "@mui/material";

export default function TermsPage() {
  return (
    <div className="container">
      <Card className="section-card">
        <CardContent>
          <Stack spacing={2}>
            <Typography variant="h4">Terms of Use</Typography>
            <Typography variant="body1" color="text.secondary">
              This application is a software demo for informational and research-oriented genetic interpretation.
            </Typography>
            <Typography variant="body2">
              It does not provide medical advice, diagnosis, treatment recommendations, reproductive counseling, or clinical-grade reporting.
            </Typography>
            <Typography variant="body2">
              By using the app, you confirm that you have permission to analyze any uploaded genotype files and that you understand the outputs are probabilistic estimates with technical and scientific limits.
            </Typography>
            <Typography variant="body2">
              Before any commercial launch, replace this page with formal legal terms covering refunds, liability limits, governing law, eligibility, and data handling commitments.
            </Typography>
          </Stack>
        </CardContent>
      </Card>
    </div>
  );
}
