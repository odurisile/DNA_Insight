"use client";
import { useState } from 'react';
import { uploadSingleDNA } from '@/lib/api';
import { Button, Typography, CircularProgress, Card, CardContent, Stack, Chip } from '@mui/material';
import UploadFileIcon from "@mui/icons-material/UploadFile";
import VerifiedIcon from "@mui/icons-material/Verified";
import { useRouter } from 'next/navigation';

export default function UploadPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [file, setFile] = useState(null);

  async function handleUpload() {
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    const data = await uploadSingleDNA(formData);
    sessionStorage.setItem("reportData", JSON.stringify(data));
    setLoading(false);
    router.push("/report");
  }

  return (
    <div className='container'>
      <Card className="section-card">
        <CardContent sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <Typography variant='h5'>Upload your raw DNA file</Typography>
          <Typography variant='body1' color="text.secondary">
            23andMe, Ancestry, MyHeritage, or FTDNA text/CSV. We will surface Promethease-style variant
            evidence alongside a calm, 23andMe-like summary — including the genotype behind every call.
          </Typography>

          <Stack direction="row" spacing={1}>
            <Chip icon={<VerifiedIcon />} label="Genotype-backed traits" />
            <Chip icon={<UploadFileIcon />} label="No data leaves your browser" variant="outlined" />
          </Stack>

          <input 
            type='file' 
            accept='.txt,.csv' 
            onChange={(e)=>setFile(e.target.files[0])}
            style={{ marginTop: 10 }}
          />

          <Button 
            startIcon={loading ? null : <UploadFileIcon />}
            variant='contained' 
            sx={{ mt:2, alignSelf: "flex-start" }} 
            disabled={!file || loading} 
            onClick={handleUpload}
          >
            {loading ? <CircularProgress size={24}/> : "Analyze & show genotypes"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
