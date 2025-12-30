"use client";
import { createTheme } from "@mui/material/styles";
const theme = createTheme({
  palette: {
    primary: { main: "#1fb37b" },
    secondary: { main: "#ff5c8a" },
    background: { default: "#f5f7fb" },
    text: {
      primary: "#0f172a",
      secondary: "#4b5563"
    }
  },
  typography: {
    fontFamily: '"Space Grotesk","DM Sans","Helvetica Neue",sans-serif',
    h4: { fontWeight: 700 },
    h5: { fontWeight: 700 },
    button: { fontWeight: 700, textTransform: "none" }
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 14,
          paddingInline: 16
        }
      }
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16
        }
      }
    }
  }
});
export default theme;
