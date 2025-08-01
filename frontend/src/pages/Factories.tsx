import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  LocationOn as LocationIcon,
  Factory as FactoryIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  DeviceHub as DeviceIcon
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';

interface City {
  id: number;
  name: string;
  status: boolean;
  createdAt: string;
}

interface Factory {
  id: number;
  name: string;
  city: City;
  status: boolean;
  group: string;
  address: string;
  phone: string;
  email: string;
  createdAt: string;
  deviceCount: number;
  activeBatches: number;
}

const Factories: React.FC = () => {
  const { enqueueSnackbar } = useSnackbar();
  const [factories, setFactories] = useState<Factory[]>([]);
  const [cities, setCities] = useState<City[]>([]);
  const [loading, setLoading] = useState(true);
  const [citiesLoading, setCitiesLoading] = useState(false);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingFactory, setEditingFactory] = useState<Factory | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [formData, setFormData] = useState({
    name: '',
    cityId: '',
    group: '',
    address: '',
    phone: '',
    email: ''
  });

  // Devices management state
  const [devicesDialogOpen, setDevicesDialogOpen] = useState(false);
  const [selectedFactory, setSelectedFactory] = useState<Factory | null>(null);
  const [factoryDevices, setFactoryDevices] = useState<any[]>([]);
  const [deviceFormData, setDeviceFormData] = useState({
    id: '',
    name: '',
    serialNumber: '',
    selectedCounter: 'counter_1'
  });

  // Fetch cities from API
  const fetchCities = async () => {
    try {
      setCitiesLoading(true);
      const response = await fetch('/api/cities', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch cities');
      }

      const result = await response.json();
      if (result.success) {
        setCities(result.data);
      } else {
        throw new Error(result.message || 'Failed to fetch cities');
      }
    } catch (error) {
      console.error('Error fetching cities:', error);
      enqueueSnackbar('Failed to load cities', { variant: 'error' });
    } finally {
      setCitiesLoading(false);
    }
  };

  // Fetch factories from API
  const fetchFactories = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/factories', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch factories');
      }

      const result = await response.json();
      if (result.success) {
        setFactories(result.data);
      } else {
        throw new Error(result.message || 'Failed to fetch factories');
      }
    } catch (error) {
      console.error('Error fetching factories:', error);
      enqueueSnackbar('Failed to load factories', { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  // Create factory via API
  const createFactory = async (factoryData: any) => {
    try {
      const response = await fetch('/api/factories', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: factoryData.name,
          cityId: parseInt(factoryData.cityId),
          group: factoryData.group,
          address: factoryData.address
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to create factory');
      }

      const result = await response.json();
      if (result.success) {
        enqueueSnackbar('Factory created successfully', { variant: 'success' });
        fetchFactories(); // Refresh the list
        return result.data;
      } else {
        throw new Error(result.message || 'Failed to create factory');
      }
    } catch (error) {
      console.error('Error creating factory:', error);
      enqueueSnackbar(error instanceof Error ? error.message : 'Failed to create factory', { variant: 'error' });
      throw error;
    }
  };

  useEffect(() => {
    fetchCities();
    fetchFactories();
  }, []);

  const handleOpenDialog = (factory?: Factory) => {
    if (factory) {
      setEditingFactory(factory);
      setFormData({
        name: factory.name,
        cityId: factory.city.id.toString(),
        group: factory.group,
        address: factory.address,
        phone: factory.phone,
        email: factory.email
      });
    } else {
      setEditingFactory(null);
      setFormData({
        name: '',
        cityId: '',
        group: '',
        address: '',
        phone: '',
        email: ''
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingFactory(null);
  };

  const handleSubmit = async () => {
    try {
      if (editingFactory) {
        // Update existing factory (mock for now)
        setFactories(prev => prev.map(f => 
          f.id === editingFactory.id 
            ? { ...f, ...formData, city: cities.find(c => c.id === parseInt(formData.cityId)) || f.city }
            : f
        ));
        enqueueSnackbar('Factory updated successfully', { variant: 'success' });
      } else {
        // Create new factory via API
        await createFactory(formData);
      }
      handleCloseDialog();
    } catch (error) {
      // Error is already handled in createFactory function
    }
  };

  const handleDelete = (id: number) => {
    setFactories(prev => prev.filter(f => f.id !== id));
    enqueueSnackbar('Factory deleted successfully', { variant: 'success' });
  };

  const handleToggleStatus = (id: number) => {
    setFactories(prev => prev.map(f => 
      f.id === id ? { ...f, status: !f.status } : f
    ));
    enqueueSnackbar('Factory status updated', { variant: 'info' });
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Devices management functions
  const handleOpenDevicesDialog = async (factory: Factory) => {
    setSelectedFactory(factory);
    setDevicesDialogOpen(true);
    
    // Fetch devices for this factory
    try {
      const response = await fetch(`/api/devices/factory/${factory.id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setFactoryDevices(result.data);
        }
      }
    } catch (error) {
      console.error('Error fetching factory devices:', error);
      enqueueSnackbar('Failed to load factory devices', { variant: 'error' });
    }
  };

  const handleCloseDevicesDialog = () => {
    setDevicesDialogOpen(false);
    setSelectedFactory(null);
    setFactoryDevices([]);
    setDeviceFormData({
      id: '',
      name: '',
      serialNumber: '',
      selectedCounter: 'counter_1'
    });
  };

  const handleAddDevice = async () => {
    if (!selectedFactory) return;

    try {
      const response = await fetch('/api/devices', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          id: deviceFormData.id,
          name: deviceFormData.name,
          factoryId: selectedFactory.id,
          serialNumber: deviceFormData.serialNumber,
          selectedCounter: deviceFormData.selectedCounter
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to create device');
      }

      const result = await response.json();
      if (result.success) {
        enqueueSnackbar('Device added successfully', { variant: 'success' });
        
        // Add the new device to the list
        setFactoryDevices(prev => [...prev, result.data]);
        
        // Reset form
        setDeviceFormData({
          id: '',
          name: '',
          serialNumber: '',
          selectedCounter: 'counter_1'
        });
      } else {
        throw new Error(result.message || 'Failed to create device');
      }
    } catch (error) {
      console.error('Error adding device:', error);
      enqueueSnackbar(error instanceof Error ? error.message : 'Failed to add device', { variant: 'error' });
    }
  };

  const handleRemoveDevice = async (deviceId: string) => {
    try {
      const response = await fetch(`/api/devices/${deviceId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        enqueueSnackbar('Device removed successfully', { variant: 'success' });
        setFactoryDevices(prev => prev.filter(d => d.id !== deviceId));
      } else {
        throw new Error('Failed to remove device');
      }
    } catch (error) {
      console.error('Error removing device:', error);
      enqueueSnackbar('Failed to remove device', { variant: 'error' });
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
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Factories Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Add Factory
        </Button>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Factories
              </Typography>
              <Typography variant="h4">
                {factories.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active Factories
              </Typography>
              <Typography variant="h4" color="success.main">
                {factories.filter(f => f.status).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Devices
              </Typography>
              <Typography variant="h4">
                {factories.reduce((sum, f) => sum + f.deviceCount, 0)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active Batches
              </Typography>
              <Typography variant="h4" color="primary.main">
                {factories.reduce((sum, f) => sum + f.activeBatches, 0)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Factories Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>City</TableCell>
                <TableCell>Group</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Devices</TableCell>
                <TableCell>Active Batches</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {factories
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((factory) => (
                  <TableRow key={factory.id}>
                    <TableCell>
                      <Box display="flex" alignItems="center">
                        <FactoryIcon sx={{ mr: 1, color: 'primary.main' }} />
                        {factory.name}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center">
                        <LocationIcon sx={{ mr: 1, fontSize: 'small' }} />
                        {factory.city.name}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={factory.group} 
                        size="small"
                        color={factory.group === 'government' ? 'primary' : 'secondary'}
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        icon={factory.status ? <CheckCircleIcon /> : <CancelIcon />}
                        label={factory.status ? 'Active' : 'Inactive'}
                        color={factory.status ? 'success' : 'error'}
                        size="small"
                        onClick={() => handleToggleStatus(factory.id)}
                        sx={{ cursor: 'pointer' }}
                      />
                    </TableCell>
                    <TableCell>{factory.deviceCount}</TableCell>
                    <TableCell>{factory.activeBatches}</TableCell>
                    <TableCell>{factory.createdAt}</TableCell>
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog(factory)}
                        color="primary"
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDevicesDialog(factory)}
                        color="secondary"
                      >
                        <DeviceIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(factory.id)}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={factories.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingFactory ? 'Edit Factory' : 'Add New Factory'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Factory Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>City</InputLabel>
                <Select
                  value={formData.cityId}
                  label="City"
                  onChange={(e) => setFormData({ ...formData, cityId: e.target.value })}
                  disabled={citiesLoading}
                >
                  {citiesLoading ? (
                    <MenuItem disabled>
                      <CircularProgress size={20} sx={{ mr: 1 }} />
                      Loading cities...
                    </MenuItem>
                  ) : (
                    cities.map((city) => (
                      <MenuItem key={city.id} value={city.id}>
                        {city.name}
                      </MenuItem>
                    ))
                  )}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Group</InputLabel>
                <Select
                  value={formData.group}
                  label="Group"
                  onChange={(e) => setFormData({ ...formData, group: e.target.value })}
                >
                  <MenuItem value="government">Government</MenuItem>
                  <MenuItem value="private">Private</MenuItem>
                  <MenuItem value="commercial">Commercial</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Address"
                multiline
                rows={2}
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Phone"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained"
            disabled={!formData.name || !formData.cityId || !formData.group}
          >
            {editingFactory ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Manage Devices Dialog */}
      <Dialog open={devicesDialogOpen} onClose={handleCloseDevicesDialog} maxWidth="lg" fullWidth>
        <DialogTitle>
          Manage Devices - {selectedFactory?.name}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Add New Device
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={3}>
                <TextField
                  fullWidth
                  label="Device ID"
                  value={deviceFormData.id}
                  onChange={(e) => setDeviceFormData({ ...deviceFormData, id: e.target.value })}
                  helperText="Unique device identifier"
                />
              </Grid>
              <Grid item xs={12} sm={3}>
                <TextField
                  fullWidth
                  label="Device Name"
                  value={deviceFormData.name}
                  onChange={(e) => setDeviceFormData({ ...deviceFormData, name: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={3}>
                <TextField
                  fullWidth
                  label="Serial Number"
                  value={deviceFormData.serialNumber}
                  onChange={(e) => setDeviceFormData({ ...deviceFormData, serialNumber: e.target.value })}
                  helperText="Optional"
                />
              </Grid>
              <Grid item xs={12} sm={3}>
                <FormControl fullWidth>
                  <InputLabel>Primary Counter</InputLabel>
                  <Select
                    value={deviceFormData.selectedCounter}
                    label="Primary Counter"
                    onChange={(e) => setDeviceFormData({ ...deviceFormData, selectedCounter: e.target.value })}
                  >
                    <MenuItem value="counter_1">Counter 1</MenuItem>
                    <MenuItem value="counter_2">Counter 2</MenuItem>
                    <MenuItem value="counter_3">Counter 3</MenuItem>
                    <MenuItem value="counter_4">Counter 4</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
            <Box sx={{ mt: 2 }}>
              <Button 
                variant="contained" 
                onClick={handleAddDevice}
                disabled={!deviceFormData.id || !deviceFormData.name}
              >
                Add Device
              </Button>
            </Box>
          </Box>

          <Typography variant="h6" gutterBottom>
            Factory Devices ({factoryDevices.length})
          </Typography>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Device ID</TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>Serial Number</TableCell>
                  <TableCell>Primary Counter</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {factoryDevices.map((device) => (
                  <TableRow key={device.id}>
                    <TableCell>{device.id}</TableCell>
                    <TableCell>{device.name}</TableCell>
                    <TableCell>{device.serialNumber || 'N/A'}</TableCell>
                    <TableCell>
                      <Chip label={device.selectedCounter} size="small" color="primary" />
                    </TableCell>
                    <TableCell>
                      <Chip
                        icon={device.status ? <CheckCircleIcon /> : <CancelIcon />}
                        label={device.status ? 'Online' : 'Offline'}
                        color={device.status ? 'success' : 'error'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() => handleRemoveDevice(device.id)}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDevicesDialog}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Factories; 