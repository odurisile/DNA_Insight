import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider, CssBaseline } from "@mui/material";

import theme from "./theme";

import ChildOptionsPage from "./pages/ChildOptionsPage";
import UploadParentsPage from "./pages/UploadParentsPage";
import ManualPartnerPage from "./pages/ManualPartnerPage";
import PartnerSimulationPage from "./pages/PartnerSimulationPage";
import ChildResultsPage from "./pages/ChildResultsPage";

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />

      <BrowserRouter>
        <Routes>

          {/* Home → choose prediction mode */}
          <Route path="/" element={<Navigate to="/childOptions" />} />

          <Route path="/childOptions" element={<ChildOptionsPage />} />

          {/* Parent DNA uploads */}
          <Route path="/uploadParents" element={<UploadParentsPage />} />

          {/* Manual partner traits */}
          <Route path="/manualPartner" element={<ManualPartnerPage />} />

          {/* Population-based partner simulation */}
          <Route path="/simulatePartner" element={<PartnerSimulationPage />} />

          {/* Results page */}
          <Route path="/childResults" element={<ChildResultsPage />} />

        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}
