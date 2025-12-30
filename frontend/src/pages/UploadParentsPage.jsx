import React, { useState } from "react";
import { Box, Typography, Button, LinearProgress, Card, CardContent } from "@mui/material";
import { useLocation, useNavigate } from "react-router-dom";

export default function UploadParentsPage() {
  const navigate = useNavigate();
  const location = useLocation();

  // Mode passed from ChildOptionsPage
  const mode = location.state?.mode || "fast";

  const [parent1, setParent1] = useState(null);
  const [parent2, setParent2] = useState(null);

  const [uploading, setUploading] = useState(false);

  const handleUpload = async (e, setParent) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:5000/upload_parent", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (data.status === "ok") {
        const count = Object.keys(data.genotypes).length;

        setParent({
          fileName: file.name,
          snpCount: count,
          genotypes: data.genotypes,
        });
      } else {
        alert("Error: " + data.message);
      }
    } catch (err) {
      alert("Upload failed: " + err);
    }

    setUploading(false);
  };

  const canContinue = parent1 && parent2;

  const handleNext = () => {
    navigate("/childResults", {
      state: {
        parent1: parent1.genotypes,
        parent2: parent2.genotypes,
        mode,
      },
    });
  };

  return (
    <Box
      sx={{
        width: "100%",
        minHeight: "100vh",
        bgcolor: "#fafaff",
        p: 4,
      }}
    >
      {/* Title */}
      <Typography variant="h4" sx={{ mb: 4, fontWeight: 700 }}>
        Upload Parent DNA Files
      </Typography>

      {/* Parent upload cards */}
      <Box sx={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
        
        {/* Parent 1 */}
        <Card sx={{ width: 350, boxShadow: 3, borderRadius: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
              Parent 1
            </Typography>

            <Button variant="contained" component="label">
              Upload DNA
              <input hidden type="file" accept=".txt,.zip" onChange={(e) => handleUpload(e, setParent1)} />
            </Button>

            {uploading && <LinearProgress sx={{ mt: 2 }} />}

            {parent1 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="body1"><strong>File:</strong> {parent1.fileName}</Typography>
                <Typography variant="body2" sx={{ color: "#666" }}>
                  SNPs parsed: {parent1.snpCount}
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>

        {/* Parent 2 */}
        <Card sx={{ width: 350, boxShadow: 3, borderRadius: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
              Parent 2
            </Typography>

            <Button variant="contained" component="label">
              Upload DNA
              <input hidden type="file" accept=".txt,.zip" onChange={(e) => handleUpload(e, setParent2)} />
            </Button>

            {uploading && <LinearProgress sx={{ mt: 2 }} />}

            {parent2 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="body1"><strong>File:</strong> {parent2.fileName}</Typography>
                <Typography variant="body2" sx={{ color: "#666" }}>
                  SNPs parsed: {parent2.snpCount}
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>

      {/* Continue Button */}
      <Box sx={{ mt: 6 }}>
        <Button
          variant="contained"
          color="primary"
          disabled={!canContinue}
          onClick={handleNext}
          sx={{
            px: 4,
            py: 1.5,
            fontSize: "1.1rem",
            borderRadius: 3,
            boxShadow: 3
          }}
        >
          Continue to Results →
        </Button>
      </Box>
    </Box>
  );
}
