"use client";
import { useState } from 'react';
import { uploadParentsDNA } from '@/lib/api';
import { Button, Typography, CircularProgress } from '@mui/material';
import { useRouter } from 'next/navigation';

export default function ParentsUploadPage() {
  const router = useRouter();
  const [files, setFiles] = useState({ p1:null, p2:null });
  const [loading, setLoading] = useState(false);

  async function handleUpload() {
    if (!files.p1 || !files.p2) return;

    setLoading(true);
    const formData = new FormData();
    formData.append("file1", files.p1);
    formData.append("file2", files.p2);

    const data = await uploadParentsDNA(formData);
    // Compact payload to avoid quota issues (drop raw genomes)
    const compact = {
      parentA: {
        traits: data.parentA?.traits,
        health: data.parentA?.health,
        key_genotypes: data.parentA?.key_genotypes,
        key_snps: data.parentA?.key_snps
      },
      parentB: {
        traits: data.parentB?.traits,
        health: data.parentB?.health,
        key_genotypes: data.parentB?.key_genotypes,
        key_snps: data.parentB?.key_snps
      },
      child: {
        child_traits: data.child?.child_traits,
        child_health: data.child?.child_health,
        child_trait_distribution: data.child?.child_trait_distribution
      }
    };
    sessionStorage.setItem("childData", JSON.stringify(compact));
    setLoading(false);
    router.push("/child-results");
  }

  return (
    <div className='container'>
      <Typography variant='h4' gutterBottom>Upload Parent DNA</Typography>

      <Typography>Parent A</Typography>
      <input type='file' accept='.txt,.csv'
        onChange={(e)=>setFiles({...files, p1:e.target.files[0]})}
      />

      <Typography sx={{ mt:2 }}>Parent B</Typography>
      <input type='file' accept='.txt,.csv'
        onChange={(e)=>setFiles({...files, p2:e.target.files[0]})}
      />

      <Button 
        variant='contained' 
        sx={{ mt:3 }}
        disabled={!files.p1 || !files.p2 || loading}
        onClick={handleUpload}
      >
        {loading ? <CircularProgress size={24}/> : "Predict Child"}
      </Button>
    </div>
  );
}
