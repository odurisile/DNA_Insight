import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    primary: { main: "#6c8cff" },
    secondary: { main: "#ffb8d1" },
    background: { default: "#f5f6fb" },
  },

  typography: {
    fontFamily: "Inter, Roboto, sans-serif",
  },

  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          transition: "all 0.25s ease",
          "&:hover": {
            transform: "translateY(-4px)",
            boxShadow: "0 6px 24px rgba(0,0,0,0.1)",
          },
        },
      },
    },

    MuiLinearProgress: {
      styleOverrides: {
        bar: {
          transition: "width 0.8s ease",
        },
      },
    },
  },
});

export default theme;
