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
  CircularProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  LinearProgress,
  Alert,
  Tooltip,
  FormGroup,
  FormControlLabel,
  Checkbox
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  DeviceHub as DeviceIcon,
  SignalCellular4Bar as SignalIcon,
  SignalCellular0Bar as NoSignalIcon,
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';

interface Factory {
  id: number;
  name: string;
  status: boolean;
  group: string;
  address: string;
  createdAt: string;
}

interface Device {
  id: string;
  name: string;
  factoryId: number;
  factoryName: string;
  status: boolean;
  serialNumber?: string;
  selectedCounter: string;
  createdAt: string;
}

const Devices: React.FC = () => {
  const { enqueueSnackbar } = useSnackbar();
  const [devices, setDevices] = useState<Device[]>([]);
  const [newDevices, setNewDevices] = useState<any[]>([]);
  const [factories, setFactories] = useState<Factory[]>([]);
  const [loading, setLoading] = useState(true);
  const [factoriesLoading, setFactoriesLoading] = useState(false);
  const [openDialog, setOpenDialog] = useState(false);
  const [configureDialogOpen, setConfigureDialogOpen] = useState(false);
  const [editingDevice, setEditingDevice] = useState<Device | null>(null);
  const [configuringDevice, setConfiguringDevice] = useState<any>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [formData, setFormData] = useState({
    id: '',
    name: '',
    factoryId: '',
    serialNumber: '',
    selectedCounter: 'counter_1',
    activeCounters: {
      counter_1: true,
      counter_2: false,
      counter_3: false,
      counter_4: false
    }
  });

  const [configureFormData, setConfigureFormData] = useState({
    name: '',
    factoryId: '',
    serialNumber: '',
    selectedCounter: 'counter_1',
    activeCounters: {
      counter_1: true,
      counter_2: false,
      counter_3: false,
      counter_4: false
    }
  });

  // Fetch factories from API
  const fetchFactories = async () => {
    try {
      setFactoriesLoading(true);
      const token = localStorage.getItem('accessToken');
      if (!token) {
        enqueueSnackbar('Authentication required', { variant: 'error' });
        return;
      }

      const apiUrl = process.env.REACT_APP_API_URL || '/api';
      const response = await fetch(`${apiUrl}/factories`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        if (response.status === 401) {
          enqueueSnackbar('Authentication failed. Please login again.', { variant: 'error' });
          return;
        }
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
      setFactoriesLoading(false);
    }
  };

  // Fetch devices from API
  const fetchDevices = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('accessToken');
      if (!token) {
        enqueueSnackbar('Authentication required', { variant: 'error' });
        return;
      }

      const apiUrl = process.env.REACT_APP_API_URL || '/api';
      const response = await fetch(`${apiUrl}/devices`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        if (response.status === 401) {
          enqueueSnackbar('Authentication failed. Please login again.', { variant: 'error' });
          return;
        }
        throw new Error('Failed to fetch devices');
      }

      const result = await response.json();
      if (result.success) {
        // Filter configured devices (devices with names)
        const configuredDevices = result.data.filter((device: any) => device.name && device.name.trim() !== '');
        setDevices(configuredDevices);
      } else {
        throw new Error(result.message || 'Failed to fetch devices');
      }
    } catch (error) {
      console.error('Error fetching devices:', error);
      enqueueSnackbar('Failed to load devices', { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  // Fetch new devices from API
  const fetchNewDevices = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      if (!token) {
        enqueueSnackbar('Authentication required', { variant: 'error' });
        return;
      }

      const apiUrl = process.env.REACT_APP_API_URL || '/api';
      const response = await fetch(`${apiUrl}/devices`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        if (response.status === 401) {
          enqueueSnackbar('Authentication failed. Please login again.', { variant: 'error' });
          return;
        }
        throw new Error('Failed to fetch new devices');
      }

      const result = await response.json();
      if (result.success) {
        // Filter new devices (devices without names)
        const newDevicesList = result.data.filter((device: any) => !device.name || device.name.trim() === '');
        setNewDevices(newDevicesList);
      } else {
        throw new Error(result.message || 'Failed to fetch new devices');
      }
    } catch (error) {
      console.error('Error fetching new devices:', error);
      enqueueSnackbar('Failed to load new devices', { variant: 'error' });
    }
  };

  // Create device via API
  const createDevice = async (deviceData: any) => {
    try {
      const token = localStorage.getItem('accessToken');
      if (!token) {
        enqueueSnackbar('Authentication required', { variant: 'error' });
        return;
      }

      const apiUrl = process.env.REACT_APP_API_URL || '/api';
      const response = await fetch(`${apiUrl}/devices`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          id: deviceData.id,
          name: deviceData.name,
          factoryId: parseInt(deviceData.factoryId),
          serialNumber: deviceData.serialNumber,
          selectedCounter: deviceData.selectedCounter
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to create device');
      }

      const result = await response.json();
      if (result.success) {
        enqueueSnackbar('Device created successfully', { variant: 'success' });
        fetchDevices(); // Refresh the list
        return result.data;
      } else {
        throw new Error(result.message || 'Failed to create device');
      }
    } catch (error) {
      console.error('Error creating device:', error);
      enqueueSnackbar(error instanceof Error ? error.message : 'Failed to create device', { variant: 'error' });
      throw error;
    }
  };

  // Configure device function
  const configureDevice = async (deviceId: string, deviceData: any) => {
    try {
      const token = localStorage.getItem('accessToken');
      if (!token) {
        enqueueSnackbar('Authentication required', { variant: 'error' });
        return;
      }

      const apiUrl = process.env.REACT_APP_API_URL || '/api';
      const response = await fetch(`${apiUrl}/devices/${deviceId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: deviceData.name,
          factoryId: parseInt(deviceData.factoryId),
          serialNumber: deviceData.serialNumber,
          selectedCounter: deviceData.selectedCounter
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to configure device');
      }

      const result = await response.json();
      if (result.success) {
        enqueueSnackbar('Device configured successfully', { variant: 'success' });
        
        // Refresh both lists
        fetchDevices();
        fetchNewDevices();
        
        return result.data;
      } else {
        throw new Error(result.message || 'Failed to configure device');
      }
    } catch (error) {
      console.error('Error configuring device:', error);
      enqueueSnackbar(error instanceof Error ? error.message : 'Failed to configure device', { variant: 'error' });
      throw error;
    }
  };

  useEffect(() => {
    fetchFactories();
    fetchDevices();
    fetchNewDevices();
  }, []);

  // Handle configure device dialog
  const handleOpenConfigureDialog = (device: any) => {
    setConfiguringDevice(device);
    setConfigureFormData({
      name: '',
      factoryId: '',
      serialNumber: device.serialNumber || '',
      selectedCounter: 'counter_1',
      activeCounters: {
        counter_1: true,
        counter_2: false,
        counter_3: false,
        counter_4: false
      }
    });
    setConfigureDialogOpen(true);
  };

  const handleCloseConfigureDialog = () => {
    setConfigureDialogOpen(false);
    setConfiguringDevice(null);
  };

  const handleConfigureCounterChange = (counter: string, checked: boolean) => {
    setConfigureFormData(prev => ({
      ...prev,
      activeCounters: {
        ...prev.activeCounters,
        [counter]: checked
      },
      selectedCounter: prev.selectedCounter === counter && !checked 
        ? Object.keys(prev.activeCounters).find(c => c !== counter && prev.activeCounters[c as keyof typeof prev.activeCounters]) || 'counter_1'
        : prev.selectedCounter
    }));
  };

  const handleConfigureSubmit = async () => {
    if (!configuringDevice) return;

    try {
      await configureDevice(configuringDevice.id, configureFormData);
      handleCloseConfigureDialog();
    } catch (error) {
      // Error is already handled in configureDevice function
    }
  };

  const handleOpenDialog = (device?: Device) => {
    if (device) {
      setEditingDevice(device);
      setFormData({
        id: device.id,
        name: device.name,
        factoryId: device.factoryId.toString(),
        serialNumber: device.serialNumber || '',
        selectedCounter: device.selectedCounter,
        activeCounters: {
          counter_1: device.selectedCounter === 'counter_1',
          counter_2: device.selectedCounter === 'counter_2',
          counter_3: device.selectedCounter === 'counter_3',
          counter_4: device.selectedCounter === 'counter_4'
        }
      });
    } else {
      setEditingDevice(null);
      setFormData({
        id: '',
        name: '',
        factoryId: '',
        serialNumber: '',
        selectedCounter: 'counter_1',
        activeCounters: {
          counter_1: true,
          counter_2: false,
          counter_3: false,
          counter_4: false
        }
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingDevice(null);
  };

  const handleCounterChange = (counter: string, checked: boolean) => {
    setFormData(prev => ({
      ...prev,
      activeCounters: {
        ...prev.activeCounters,
        [counter]: checked
      },
      // If the selected counter is unchecked, switch to the first active counter
      selectedCounter: prev.selectedCounter === counter && !checked 
        ? Object.keys(prev.activeCounters).find(c => c !== counter && prev.activeCounters[c as keyof typeof prev.activeCounters]) || 'counter_1'
        : prev.selectedCounter
    }));
  };

  const handleSubmit = async () => {
    try {
      if (editingDevice) {
        // Update existing device (mock for now)
        setDevices(prev => prev.map(d => 
          d.id === editingDevice.id 
            ? { 
                ...d, 
                name: formData.name,
                factoryId: parseInt(formData.factoryId),
                serialNumber: formData.serialNumber,
                selectedCounter: formData.selectedCounter
              }
            : d
        ));
        enqueueSnackbar('Device updated successfully', { variant: 'success' });
      } else {
        // Create new device via API
        await createDevice(formData);
      }
      handleCloseDialog();
    } catch (error) {
      // Error is already handled in createDevice function
    }
  };

  const handleDelete = (id: string) => {
    setDevices(prev => prev.filter(d => d.id !== id));
    enqueueSnackbar('Device deleted successfully', { variant: 'success' });
  };

  const getStatusColor = (status: boolean) => {
    return status ? 'success' : 'error';
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
          IoT Devices Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Add Device
        </Button>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Devices
              </Typography>
              <Typography variant="h4">
                {devices.length + newDevices.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Configured Devices
              </Typography>
              <Typography variant="h4" color="success.main">
                {devices.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                New Devices
              </Typography>
              <Typography variant="h4" color="warning.main">
                {newDevices.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Factories
              </Typography>
              <Typography variant="h4" color="primary.main">
                {factories.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* New Devices Section */}
      {newDevices.length > 0 && (
        <Box mb={4}>
          <Typography variant="h5" gutterBottom color="warning.main">
            New Devices ({newDevices.length})
          </Typography>
          <Alert severity="info" sx={{ mb: 2 }}>
            These devices have been detected via MQTT but need to be configured with a name and factory assignment.
          </Alert>
          <Paper>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Device ID (Serial Number)</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>First Seen</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {newDevices.map((device) => (
                    <TableRow key={device.id}>
                      <TableCell>
                        <Box display="flex" alignItems="center">
                          <DeviceIcon sx={{ mr: 1, color: 'warning.main' }} />
                          <Typography variant="body2" fontWeight="bold">
                            {device.id}
                          </Typography>
                        </Box>
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
                        <Typography variant="body2">
                          {new Date(device.createdAt).toLocaleDateString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          variant="contained"
                          color="primary"
                          onClick={() => handleOpenConfigureDialog(device)}
                        >
                          Configure
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Box>
      )}

      {/* Configured Devices Section */}
      <Box>
        <Typography variant="h5" gutterBottom>
          Configured Devices ({devices.length})
        </Typography>
        <Paper>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Device ID</TableCell>
                  <TableCell>Device Name</TableCell>
                  <TableCell>Factory</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Selected Counter</TableCell>
                  <TableCell>Serial Number</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {devices
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((device) => (
                    <TableRow key={device.id}>
                      <TableCell>
                        <Box display="flex" alignItems="center">
                          <DeviceIcon sx={{ mr: 1, color: 'primary.main' }} />
                          {device.id}
                        </Box>
                      </TableCell>
                      <TableCell>{device.name}</TableCell>
                      <TableCell>{device.factoryName}</TableCell>
                      <TableCell>
                        <Chip
                          icon={device.status ? <CheckCircleIcon /> : <CancelIcon />}
                          label={device.status ? 'Online' : 'Offline'}
                          color={getStatusColor(device.status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={device.selectedCounter}
                          size="small"
                          color="primary"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {device.serialNumber || 'N/A'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {new Date(device.createdAt).toLocaleDateString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Tooltip title="Edit Device">
                          <IconButton
                            size="small"
                            onClick={() => handleOpenDialog(device)}
                            color="primary"
                          >
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete Device">
                          <IconButton
                            size="small"
                            onClick={() => handleDelete(device.id)}
                            color="error"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            rowsPerPageOptions={[5, 10, 25]}
            component="div"
            count={devices.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={(event, newPage) => setPage(newPage)}
            onRowsPerPageChange={(event) => {
              setRowsPerPage(parseInt(event.target.value, 10));
              setPage(0);
            }}
          />
        </Paper>
      </Box>

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingDevice ? 'Edit Device' : 'Add New Device'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Device ID"
                value={formData.id}
                onChange={(e) => setFormData({ ...formData, id: e.target.value })}
                disabled={!!editingDevice} // Can't change ID when editing
                helperText="Unique device identifier"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Device Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Factory</InputLabel>
                <Select
                  value={formData.factoryId}
                  label="Factory"
                  onChange={(e) => setFormData({ ...formData, factoryId: e.target.value })}
                  disabled={factoriesLoading}
                >
                  {factoriesLoading ? (
                    <MenuItem disabled>
                      <CircularProgress size={20} sx={{ mr: 1 }} />
                      Loading factories...
                    </MenuItem>
                  ) : (
                    factories.map((factory) => (
                      <MenuItem key={factory.id} value={factory.id}>
                        {factory.name}
                      </MenuItem>
                    ))
                  )}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Serial Number"
                value={formData.serialNumber}
                onChange={(e) => setFormData({ ...formData, serialNumber: e.target.value })}
                helperText="Optional device serial number"
              />
            </Grid>
            
            {/* Counter Selection Section */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Counter Configuration
              </Typography>
              <Alert severity="info" sx={{ mb: 2 }}>
                Select which counters this device will use. The primary counter (selected counter) is used for data collection.
              </Alert>
              
              <FormGroup row>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={formData.activeCounters.counter_1}
                      onChange={(e) => handleCounterChange('counter_1', e.target.checked)}
                    />
                  }
                  label="Counter 1"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={formData.activeCounters.counter_2}
                      onChange={(e) => handleCounterChange('counter_2', e.target.checked)}
                    />
                  }
                  label="Counter 2"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={formData.activeCounters.counter_3}
                      onChange={(e) => handleCounterChange('counter_3', e.target.checked)}
                    />
                  }
                  label="Counter 3"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={formData.activeCounters.counter_4}
                      onChange={(e) => handleCounterChange('counter_4', e.target.checked)}
                    />
                  }
                  label="Counter 4"
                />
              </FormGroup>
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Primary Counter</InputLabel>
                <Select
                  value={formData.selectedCounter}
                  label="Primary Counter"
                  onChange={(e) => setFormData({ ...formData, selectedCounter: e.target.value })}
                >
                  {Object.entries(formData.activeCounters).map(([counter, active]) => (
                    active && (
                      <MenuItem key={counter} value={counter}>
                        {counter.replace('_', ' ').toUpperCase()}
                      </MenuItem>
                    )
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained"
            disabled={!formData.id || !formData.name || !formData.factoryId || !Object.values(formData.activeCounters).some(Boolean)}
          >
            {editingDevice ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Configure Device Dialog */}
      <Dialog open={configureDialogOpen} onClose={handleCloseConfigureDialog} maxWidth="md" fullWidth>
        <DialogTitle>Configure New Device</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Device Name"
                value={configureFormData.name}
                onChange={(e) => setConfigureFormData({ ...configureFormData, name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Factory</InputLabel>
                <Select
                  value={configureFormData.factoryId}
                  label="Factory"
                  onChange={(e) => setConfigureFormData({ ...configureFormData, factoryId: e.target.value })}
                  disabled={factoriesLoading}
                >
                  {factoriesLoading ? (
                    <MenuItem disabled>
                      <CircularProgress size={20} sx={{ mr: 1 }} />
                      Loading factories...
                    </MenuItem>
                  ) : (
                    factories.map((factory) => (
                      <MenuItem key={factory.id} value={factory.id}>
                        {factory.name}
                      </MenuItem>
                    ))
                  )}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Serial Number"
                value={configureFormData.serialNumber}
                onChange={(e) => setConfigureFormData({ ...configureFormData, serialNumber: e.target.value })}
              />
            </Grid>
            
            {/* Counter Selection Section */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Counter Configuration
              </Typography>
              <Alert severity="info" sx={{ mb: 2 }}>
                Select which counters this device will use. The primary counter (selected counter) is used for data collection.
              </Alert>
              
              <FormGroup row>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={configureFormData.activeCounters.counter_1}
                      onChange={(e) => handleConfigureCounterChange('counter_1', e.target.checked)}
                    />
                  }
                  label="Counter 1"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={configureFormData.activeCounters.counter_2}
                      onChange={(e) => handleConfigureCounterChange('counter_2', e.target.checked)}
                    />
                  }
                  label="Counter 2"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={configureFormData.activeCounters.counter_3}
                      onChange={(e) => handleConfigureCounterChange('counter_3', e.target.checked)}
                    />
                  }
                  label="Counter 3"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={configureFormData.activeCounters.counter_4}
                      onChange={(e) => handleConfigureCounterChange('counter_4', e.target.checked)}
                    />
                  }
                  label="Counter 4"
                />
              </FormGroup>
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Primary Counter</InputLabel>
                <Select
                  value={configureFormData.selectedCounter}
                  label="Primary Counter"
                  onChange={(e) => setConfigureFormData({ ...configureFormData, selectedCounter: e.target.value })}
                >
                  {Object.entries(configureFormData.activeCounters).map(([counter, active]) => (
                    active && (
                      <MenuItem key={counter} value={counter}>
                        {counter.replace('_', ' ').toUpperCase()}
                      </MenuItem>
                    )
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseConfigureDialog}>Cancel</Button>
          <Button 
            onClick={handleConfigureSubmit} 
            variant="contained"
            disabled={!configureFormData.name || !configureFormData.factoryId || !Object.values(configureFormData.activeCounters).some(Boolean)}
          >
            Configure
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Devices; 