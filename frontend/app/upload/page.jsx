"use client";

import Link from "next/link";
import { useState } from "react";
import {
  Alert,
  Button,
  Checkbox,
  CircularProgress,
  Card,
  CardContent,
  Chip,
  FormControlLabel,
  Stack,
  Typography,
} from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import VerifiedIcon from "@mui/icons-material/Verified";
import { useRouter } from "next/navigation";
import { uploadSingleDNA } from "@/lib/api";

export default function UploadPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [file, setFile] = useState(null);
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState("");

  async function handleUpload() {
    if (!file) return;

    setLoading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const data = await uploadSingleDNA(formData);
      sessionStorage.setItem("reportData", JSON.stringify(data));
      router.push("/report");
    } catch (err) {
      setError(err.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container">
      <Card className="section-card">
        <CardContent sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <Typography variant="h5">Upload your raw DNA file</Typography>
          <Typography variant="body1" color="text.secondary">
            23andMe, Ancestry, MyHeritage, or FTDNA text/CSV. The file is uploaded to the backend for analysis
            and report generation, and each major call is tied back to supporting genotype evidence.
          </Typography>

          <Stack direction="row" spacing={1}>
            <Chip icon={<VerifiedIcon />} label="Genotype-backed traits" />
            <Chip icon={<UploadFileIcon />} label="Processed on the server for analysis" variant="outlined" />
          </Stack>

          <input
            type="file"
            accept=".txt,.csv,.tsv"
            onChange={(e) => {
              setFile(e.target.files[0] || null);
              setError("");
            }}
            style={{ marginTop: 10 }}
          />

          <FormControlLabel
            control={<Checkbox checked={consent} onChange={(e) => setConsent(e.target.checked)} />}
            label="I understand this upload contains sensitive genetic data and the generated report is informational, not medical advice."
          />

          <Typography variant="body2" color="text.secondary">
            Review the <Link href="/privacy">privacy policy</Link> and <Link href="/terms">terms</Link> before uploading genetic data.
          </Typography>

          {error && <Alert severity="error">{error}</Alert>}

          <Alert severity="warning">
            Upload only files you own or have permission to analyze.
          </Alert>

          <Button
            startIcon={loading ? null : <UploadFileIcon />}
            variant="contained"
            sx={{ mt: 2, alignSelf: "flex-start" }}
            disabled={!file || !consent || loading}
            onClick={handleUpload}
          >
            {loading ? <CircularProgress size={24} /> : "Analyze and show genotypes"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
