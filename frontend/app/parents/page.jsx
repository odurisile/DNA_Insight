"use client";

import Link from "next/link";
import { useState } from "react";
import {
  Alert,
  Button,
  Card,
  CardContent,
  Checkbox,
  FormControlLabel,
  Stack,
  Typography,
} from "@mui/material";
import { useRouter } from "next/navigation";
import { uploadParentsDNA } from "@/lib/api";
import { AnalysisProgress, ConfidenceGuide, DemoGenomeButton, SelectedFileNotice, SessionNotice } from "@/components/AnalysisUX";

export default function ParentsUploadPage() {
  const router = useRouter();
  const [files, setFiles] = useState({ p1: null, p2: null });
  const [loading, setLoading] = useState(false);
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState("");

  async function handleUpload() {
    if (!files.p1 || !files.p2) return;

    setLoading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("file1", files.p1);
      formData.append("file2", files.p2);

      const data = await uploadParentsDNA(formData);
      const compact = {
        parentA: {
          traits: data.parentA?.traits,
          health: data.parentA?.health,
          key_genotypes: data.parentA?.key_genotypes,
          key_snps: data.parentA?.key_snps,
        },
        parentB: {
          traits: data.parentB?.traits,
          health: data.parentB?.health,
          key_genotypes: data.parentB?.key_genotypes,
          key_snps: data.parentB?.key_snps,
        },
        child: {
          child_traits: data.child?.child_traits,
          child_health: data.child?.child_health,
          child_trait_distribution: data.child?.child_trait_distribution,
          child_height_pgs: data.child?.child_height_pgs,
        },
      };
      sessionStorage.setItem("childData", JSON.stringify(compact));
      router.push("/child-results");
    } catch (err) {
      setError(err.message || "Parent upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container">
      <Card className="section-card">
        <CardContent sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <Typography variant="h4" gutterBottom>
            Upload Parent DNA
          </Typography>
          <Typography variant="body2" color="text.secondary">
            This comparison flow is informational only. It produces probabilistic trait estimates for a simulated child profile and should not be treated as medical or reproductive advice.
          </Typography>

          <Stack spacing={1}>
            <Typography>Parent A</Typography>
            <input
              aria-label="Choose Parent A raw DNA file"
              type="file"
              accept=".txt,.csv,.tsv"
              onChange={(e) => {
                setFiles({ ...files, p1: e.target.files[0] || null });
                setError("");
              }}
            />
            <DemoGenomeButton
              disabled={loading}
              label="Use sample for Parent A"
              onLoad={(sample, sampleError) => {
                setFiles((current) => ({ ...current, p1: sample }));
                setError(sampleError?.message || "");
              }}
            />
            <SelectedFileNotice file={files.p1} />
          </Stack>

          <Stack spacing={1}>
            <Typography>Parent B</Typography>
            <input
              aria-label="Choose Parent B raw DNA file"
              type="file"
              accept=".txt,.csv,.tsv"
              onChange={(e) => {
                setFiles({ ...files, p2: e.target.files[0] || null });
                setError("");
              }}
            />
            <DemoGenomeButton
              disabled={loading}
              label="Use sample for Parent B"
              onLoad={(sample, sampleError) => {
                setFiles((current) => ({ ...current, p2: sample }));
                setError(sampleError?.message || "");
              }}
            />
            <SelectedFileNotice file={files.p2} />
          </Stack>

          <FormControlLabel
            control={<Checkbox checked={consent} onChange={(e) => setConsent(e.target.checked)} />}
            label="I have permission to analyze both files and understand this feature is a non-medical prediction demo."
          />

          <Typography variant="body2" color="text.secondary">
            Review the <Link href="/privacy">privacy policy</Link> and <Link href="/terms">terms</Link> before uploading genetic data.
          </Typography>

          {error && <Alert severity="error">{error}</Alert>}
          <SessionNotice />
          <ConfidenceGuide />

          <Button
            variant="contained"
            sx={{ mt: 1, alignSelf: "flex-start" }}
            disabled={!files.p1 || !files.p2 || !consent || loading}
            onClick={handleUpload}
          >
            {loading ? "Simulating…" : "Predict child"}
          </Button>
          <AnalysisProgress active={loading} message="Comparing both genomes and simulating child outcomes…" />
        </CardContent>
      </Card>
    </div>
  );
}
