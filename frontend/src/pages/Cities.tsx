import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Grid,
  Chip
} from '@mui/material';
import {
  Add as AddIcon,
  Business as BusinessIcon,
  DeviceHub as DeviceIcon,
  Assessment as AssessmentIcon
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';

interface City {
  id: number;
  name: string;
  status: boolean;
  createdAt: string;
  factories: Factory[];
  _count?: {
    factories: number;
  };
}

interface Factory {
  id: number;
  name: string;
  status: boolean;
  devices: Device[];
  _count: {
    devices: number;
    batches: number;
  };
}

interface Device {
  id: string;
  name: string;
  status: boolean;
}

const Cities: React.FC = () => {
  const [cities, setCities] = useState<City[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { enqueueSnackbar } = useSnackbar();

  const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:3002';

  useEffect(() => {
    fetchCities();
  }, []);

  const fetchCities = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // For now, let's create mock data since we don't have authentication set up
      const mockCities = [
        {
          id: 1,
          name: 'Amsterdam',
          status: true,
          createdAt: new Date().toISOString(),
          factories: [],
          _count: { factories: 0 }
        },
        {
          id: 2,
          name: 'Rotterdam',
          status: true,
          createdAt: new Date().toISOString(),
          factories: [],
          _count: { factories: 0 }
        },
        {
          id: 3,
          name: 'Den Haag',
          status: true,
          createdAt: new Date().toISOString(),
          factories: [],
          _count: { factories: 0 }
        }
      ];

      setCities(mockCities);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch cities');
      enqueueSnackbar('Failed to fetch cities', { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          🏙️ Cities Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => enqueueSnackbar('Add City feature coming soon!', { variant: 'info' })}
        >
          Add City
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {cities.length === 0 ? (
        <Card>
          <CardContent>
            <Typography variant="h6" color="text.secondary" align="center">
              No cities found
            </Typography>
            <Typography variant="body2" color="text.secondary" align="center">
              Create your first city to start managing factories and devices
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {cities.map((city) => (
            <Grid item xs={12} md={6} lg={4} key={city.id}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    🏙️ {city.name}
                  </Typography>
                  
                  <Box display="flex" alignItems="center" gap={1} mb={2}>
                    <Chip
                      label={city.status ? 'Active' : 'Inactive'}
                      color={city.status ? 'success' : 'default'}
                      size="small"
                    />
                  </Box>

                  <Box display="flex" alignItems="center" gap={1} mb={1}>
                    <BusinessIcon color="primary" fontSize="small" />
                    <Typography variant="body2">
                      {city._count?.factories || 0} Factories
                    </Typography>
                  </Box>

                  <Box display="flex" alignItems="center" gap={1} mb={1}>
                    <DeviceIcon color="secondary" fontSize="small" />
                    <Typography variant="body2">
                      {city.factories.reduce((sum, f) => sum + (f._count?.devices || 0), 0)} Devices
                    </Typography>
                  </Box>

                  <Box display="flex" alignItems="center" gap={1} mb={2}>
                    <AssessmentIcon color="info" fontSize="small" />
                    <Typography variant="body2">
                      {city.factories.reduce((sum, f) => sum + (f._count?.batches || 0), 0)} Batches
                    </Typography>
                  </Box>

                  <Typography variant="caption" color="text.secondary">
                    Created: {new Date(city.createdAt).toLocaleDateString()}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      <Box mt={4}>
        <Typography variant="h5" gutterBottom>
          🏭 City-Factory-Device System Overview
        </Typography>
        <Paper sx={{ p: 3 }}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    🏙️ Cities
                  </Typography>
                  <Typography variant="body2">
                    Manage cities and their associated factories. Each city can have multiple factories.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    🏭 Factories
                  </Typography>
                  <Typography variant="body2">
                    Factories are linked to cities and contain multiple devices for production monitoring.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    📱 Devices
                  </Typography>
                  <Typography variant="body2">
                    UC300 devices collect real-time data and are assigned to specific factories.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Paper>
      </Box>
    </Box>
  );
};

export default Cities; 