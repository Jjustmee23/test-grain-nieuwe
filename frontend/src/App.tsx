import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box, Container, useTheme, useMediaQuery } from '@mui/material';
import { HelmetProvider } from 'react-helmet-async';
import { SnackbarProvider } from 'notistack';

import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Cities from './pages/Cities';
import Factories from './pages/Factories';
import Devices from './pages/Devices';
import Batches from './pages/Batches';
import PowerManagement from './pages/PowerManagement';
import Analytics from './pages/Analytics';
import Support from './pages/Support';
import Profile from './pages/Profile';
import Settings from './pages/Settings';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  return (
    <HelmetProvider>
      <SnackbarProvider maxSnack={3}>
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
          <Header />
          <Box sx={{ display: 'flex', flexGrow: 1 }}>
            <Container 
              component="main" 
              sx={{ 
                flexGrow: 1, 
                py: 3,
                ml: isMobile ? 0 : '250px', // Account for permanent drawer
                width: isMobile ? '100%' : 'calc(100% - 250px)'
              }}
            >
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route
                  path="/"
                  element={
                    <ProtectedRoute>
                      <Dashboard />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/cities"
                  element={
                    <ProtectedRoute>
                      <Cities />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/factories"
                  element={
                    <ProtectedRoute>
                      <Factories />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/devices"
                  element={
                    <ProtectedRoute>
                      <Devices />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/batches"
                  element={
                    <ProtectedRoute>
                      <Batches />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/power"
                  element={
                    <ProtectedRoute>
                      <PowerManagement />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/analytics"
                  element={
                    <ProtectedRoute>
                      <Analytics />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/support"
                  element={
                    <ProtectedRoute>
                      <Support />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/profile"
                  element={
                    <ProtectedRoute>
                      <Profile />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/settings"
                  element={
                    <ProtectedRoute>
                      <Settings />
                    </ProtectedRoute>
                  }
                />
              </Routes>
            </Container>
          </Box>
        </Box>
      </SnackbarProvider>
    </HelmetProvider>
  );
}

export default App; 