"use client";

import { Card, CardContent, Stack, Typography } from "@mui/material";

export default function PrivacyPage() {
  return (
    <div className="container">
      <Card className="section-card">
        <CardContent>
          <Stack spacing={2}>
            <Typography variant="h4">Privacy Policy</Typography>
            <Typography variant="body1" color="text.secondary">
              This project processes uploaded genotype files to generate research-oriented trait, risk, and ancestry-style outputs.
            </Typography>
            <Typography variant="body2">
              Uploaded files are sent to the backend for analysis and are deleted immediately after processing, including when processing fails. Genetic data is sensitive. Do not upload files you do not own or have permission to analyze.
            </Typography>
            <Typography variant="body2">
              This repository does not yet provide account-based retention controls, deletion workflows, or a production data-governance guarantee. Use it only in environments where you control storage and access.
            </Typography>
            <Typography variant="body2">
              Before any public launch, replace this page with a deployment-specific privacy policy that explains storage duration, third-party services, deletion rights, and contact details.
            </Typography>
          </Stack>
        </CardContent>
      </Card>
    </div>
  );
}
