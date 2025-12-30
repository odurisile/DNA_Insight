"use client";
import { CssBaseline, ThemeProvider } from "@mui/material";
import theme from "@/theme";
import NavBar from "@/components/NavBar";

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <NavBar />
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
