"use client";
import { Button, Card, CardContent, Typography, Grid, Chip, Stack } from "@mui/material";
import Link from "next/link";
import ScienceIcon from "@mui/icons-material/Science";
import GroupsIcon from "@mui/icons-material/Groups";
import RocketLaunchIcon from "@mui/icons-material/RocketLaunch";

export default function Home() {
  const tiles = [
    {
      title: "Personal Genome Report",
      description: "Upload 23andMe/Ancestry data for trait and health layers with genotype evidence.",
      href: "/upload",
      icon: <ScienceIcon sx={{ color: "#ff5c8a" }} />,
      cta: "Upload & Analyze"
    },
    {
      title: "Family / Child Predictor",
      description: "Blend two genomes to see predicted child traits with variant-level transparency.",
      href: "/parents",
      icon: <GroupsIcon color="primary" />,
      cta: "Predict Together"
    }
  ];

  return (
    <div className='container'>
      <div className="hero">
        <div className="hero-content">
          <Typography variant="h3" component="h1">
            Genome Studio
          </Typography>
          <Typography variant="h6" sx={{ maxWidth: 620, opacity: 0.9 }}>
            Dive into variant-level evidence while keeping the calm, friendly surface of a consumer report.
            Every trait and risk call can be traced back to the genotype that drives it.
          </Typography>
          <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
            <Link href="/upload">
              <Button variant="contained" color="primary">Upload my genome</Button>
            </Link>
            <Link href="/parents">
              <Button variant="outlined" color="inherit">Predict a child</Button>
            </Link>
          </Stack>
        </div>
      </div>

      <Grid container spacing={2} sx={{ mt: 3 }}>
        {tiles.map(tile => (
          <Grid item xs={12} md={4} key={tile.title}>
            <Card className="section-card" sx={{ height: "100%" }}>
              <CardContent sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
                <Chip icon={tile.icon} label="Variant-aware" size="small" sx={{ width: "fit-content" }} />
                <Typography variant="h6">{tile.title}</Typography>
                <Typography variant="body2" color="text.secondary">{tile.description}</Typography>
                <div style={{ flexGrow: 1 }} />
                <Link href={tile.href}>
                  <Button variant="text" color="primary">{tile.cta}</Button>
                </Link>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </div>
  );
}
