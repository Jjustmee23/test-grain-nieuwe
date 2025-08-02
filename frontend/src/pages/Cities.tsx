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
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Switch,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
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
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingCity, setEditingCity] = useState<City | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    status: true
  });
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [cityToDelete, setCityToDelete] = useState<City | null>(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedCity, setSelectedCity] = useState<City | null>(null);

  const { enqueueSnackbar } = useSnackbar();

  const API_BASE = process.env.REACT_APP_API_URL || '/api';

  useEffect(() => {
    fetchCities();
  }, []);

  const fetchCities = async () => {
    try {
      setLoading(true);
      
      // Mock data for now
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

  const handleCreateCity = async () => {
    try {
      const newCity: City = {
        id: Math.max(...cities.map(c => c.id)) + 1,
        name: formData.name,
        status: formData.status,
        createdAt: new Date().toISOString(),
        factories: [],
        _count: { factories: 0 }
      };

      setCities([...cities, newCity]);
      enqueueSnackbar('City created successfully', { variant: 'success' });
      setDialogOpen(false);
      setFormData({ name: '', status: true });
    } catch (err) {
      enqueueSnackbar(err instanceof Error ? err.message : 'Failed to create city', { variant: 'error' });
    }
  };

  const handleUpdateCity = async () => {
    if (!editingCity) return;

    try {
      const updatedCities = cities.map(city => 
        city.id === editingCity.id 
          ? { ...city, name: formData.name, status: formData.status }
          : city
      );

      setCities(updatedCities);
      enqueueSnackbar('City updated successfully', { variant: 'success' });
      setDialogOpen(false);
      setEditingCity(null);
      setFormData({ name: '', status: true });
    } catch (err) {
      enqueueSnackbar(err instanceof Error ? err.message : 'Failed to update city', { variant: 'error' });
    }
  };

  const handleDeleteCity = async () => {
    if (!cityToDelete) return;

    try {
      const updatedCities = cities.filter(city => city.id !== cityToDelete.id);
      setCities(updatedCities);
      enqueueSnackbar('City deleted successfully', { variant: 'success' });
      setDeleteDialogOpen(false);
      setCityToDelete(null);
    } catch (err) {
      enqueueSnackbar(err instanceof Error ? err.message : 'Failed to delete city', { variant: 'error' });
    }
  };

  const openCreateDialog = () => {
    setEditingCity(null);
    setFormData({ name: '', status: true });
    setDialogOpen(true);
  };

  const openEditDialog = (city: City) => {
    setEditingCity(city);
    setFormData({ name: city.name, status: city.status });
    setDialogOpen(true);
  };

  const openDeleteDialog = (city: City) => {
    setCityToDelete(city);
    setDeleteDialogOpen(true);
  };

  const openViewDialog = (city: City) => {
    setSelectedCity(city);
    setViewDialogOpen(true);
  };

  const handleSubmit = () => {
    if (editingCity) {
      handleUpdateCity();
    } else {
      handleCreateCity();
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
          onClick={openCreateDialog}
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
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                    <Typography variant="h6" gutterBottom>
                      🏙️ {city.name}
                    </Typography>
                    <Box display="flex" gap={1}>
                      <Tooltip title="View Details">
                        <IconButton
                          size="small"
                          onClick={() => openViewDialog(city)}
                          color="primary"
                        >
                          <ViewIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit City">
                        <IconButton
                          size="small"
                          onClick={() => openEditDialog(city)}
                          color="primary"
                        >
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete City">
                        <IconButton
                          size="small"
                          onClick={() => openDeleteDialog(city)}
                          color="error"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </Box>
                  
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

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingCity ? 'Edit City' : 'Create New City'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="City Name"
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <FormControlLabel
            control={
              <Switch
                checked={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.checked })}
              />
            }
            label="Active"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingCity ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete City</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{cityToDelete?.name}"?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleDeleteCity} 
            color="error" 
            variant="contained"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* View City Details Dialog */}
      <Dialog open={viewDialogOpen} onClose={() => setViewDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          City Details: {selectedCity?.name}
        </DialogTitle>
        <DialogContent>
          {selectedCity && (
            <Box>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        City Information
                      </Typography>
                      <Typography><strong>Name:</strong> {selectedCity.name}</Typography>
                      <Typography><strong>Status:</strong> 
                        <Chip 
                          label={selectedCity.status ? 'Active' : 'Inactive'} 
                          color={selectedCity.status ? 'success' : 'default'} 
                          size="small" 
                          sx={{ ml: 1 }}
                        />
                      </Typography>
                      <Typography><strong>Created:</strong> {new Date(selectedCity.createdAt).toLocaleString()}</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Statistics
                      </Typography>
                      <Box display="flex" alignItems="center" gap={1} mb={1}>
                        <BusinessIcon color="primary" />
                        <Typography>{selectedCity._count?.factories || 0} Factories</Typography>
                      </Box>
                      <Box display="flex" alignItems="center" gap={1} mb={1}>
                        <DeviceIcon color="secondary" />
                        <Typography>
                          {selectedCity.factories.reduce((sum, f) => sum + (f._count?.devices || 0), 0)} Devices
                        </Typography>
                      </Box>
                      <Box display="flex" alignItems="center" gap={1}>
                        <AssessmentIcon color="info" />
                        <Typography>
                          {selectedCity.factories.reduce((sum, f) => sum + (f._count?.batches || 0), 0)} Batches
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

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