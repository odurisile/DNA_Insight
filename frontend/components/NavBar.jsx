"use client";
import Link from "next/link";
import { AppBar, Toolbar, Button, Typography } from "@mui/material";

export default function NavBar() {
  return (
    <AppBar
      position="sticky"
      color="transparent"
      elevation={0}
      sx={{
        backdropFilter: "blur(10px)",
        backgroundColor: "rgba(255,255,255,0.78)",
        borderBottom: "1px solid #e5e7eb",
        boxShadow: "0 12px 25px rgba(15, 23, 42, 0.06)"
      }}
    >
      <Toolbar sx={{ display: "flex", gap: "14px", py: 1 }}>
        <Link href="/" style={{ textDecoration: "none", color: "inherit", flexGrow: 1 }}>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            DNA Insight
          </Typography>
        </Link>
        <Link href="/"><Button color="primary" variant="text">Home</Button></Link>
        <Link href="/upload"><Button color="primary" variant="text">Upload DNA</Button></Link>
        <Link href="/parents"><Button color="primary" variant="text">Parents & Child</Button></Link>
      </Toolbar>
    </AppBar>
  );
}
