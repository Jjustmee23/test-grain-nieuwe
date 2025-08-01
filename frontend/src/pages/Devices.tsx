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
  Tooltip
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

interface Device {
  id: number;
  name: string;
  factoryId: number;
  factoryName: string;
  status: 'online' | 'offline' | 'maintenance';
  signalStrength: number;
  lastSeen: string;
  counter1: number;
  counter2: number;
  counter3: number;
  counter4: number;
  ain1: number; // Power value
  ain2: number;
  ain3: number;
  ain4: number;
  ain5: number;
  ain6: number;
  ain7: number;
  ain8: number;
  din: string; // Door status
  temperature: number;
  humidity: number;
  createdAt: string;
}

const Devices: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingDevice, setEditingDevice] = useState<Device | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [formData, setFormData] = useState({
    name: '',
    factoryId: '',
    status: 'online'
  });

  // Mock data - replace with API calls
  useEffect(() => {
    const mockDevices: Device[] = [
      {
        id: 1,
        name: 'Device-001',
        factoryId: 1,
        factoryName: 'Baghdad Central Mill',
        status: 'online',
        signalStrength: 85,
        lastSeen: new Date().toISOString(),
        counter1: 1250,
        counter2: 890,
        counter3: 567,
        counter4: 234,
        ain1: 220.5, // Power voltage
        ain2: 45.2,
        ain3: 78.9,
        ain4: 12.3,
        ain5: 95.7,
        ain6: 33.1,
        ain7: 67.8,
        ain8: 89.4,
        din: 'closed',
        temperature: 42.5,
        humidity: 65.2,
        createdAt: '2024-01-15'
      },
      {
        id: 2,
        name: 'Device-002',
        factoryId: 1,
        factoryName: 'Baghdad Central Mill',
        status: 'offline',
        signalStrength: 0,
        lastSeen: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
        counter1: 980,
        counter2: 456,
        counter3: 789,
        counter4: 123,
        ain1: 0,
        ain2: 0,
        ain3: 0,
        ain4: 0,
        ain5: 0,
        ain6: 0,
        ain7: 0,
        ain8: 0,
        din: 'unknown',
        temperature: 0,
        humidity: 0,
        createdAt: '2024-01-16'
      },
      {
        id: 3,
        name: 'Device-003',
        factoryId: 2,
        factoryName: 'Basra Grain Factory',
        status: 'online',
        signalStrength: 92,
        lastSeen: new Date().toISOString(),
        counter1: 2100,
        counter2: 1500,
        counter3: 890,
        counter4: 456,
        ain1: 218.7,
        ain2: 48.9,
        ain3: 82.1,
        ain4: 15.6,
        ain5: 91.3,
        ain6: 37.8,
        ain7: 71.2,
        ain8: 93.5,
        din: 'open',
        temperature: 38.9,
        humidity: 58.7,
        createdAt: '2024-02-20'
      }
    ];

    setTimeout(() => {
      setDevices(mockDevices);
      setLoading(false);
    }, 1000);
  }, []);

  const handleOpenDialog = (device?: Device) => {
    if (device) {
      setEditingDevice(device);
      setFormData({
        name: device.name,
        factoryId: device.factoryId.toString(),
        status: device.status
      });
    } else {
      setEditingDevice(null);
      setFormData({
        name: '',
        factoryId: '',
        status: 'online'
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingDevice(null);
  };

  const handleSubmit = () => {
    if (editingDevice) {
      setDevices(prev => prev.map(d => 
        d.id === editingDevice.id 
          ? { 
              ...d, 
              name: formData.name,
              factoryId: parseInt(formData.factoryId),
              status: formData.status as 'online' | 'offline' | 'maintenance'
            }
          : d
      ));
    } else {
      const newDevice: Device = {
        id: Math.max(...devices.map(d => d.id)) + 1,
        name: formData.name,
        factoryId: parseInt(formData.factoryId),
        factoryName: 'New Factory', // This would come from API
        status: formData.status as 'online' | 'offline' | 'maintenance',
        signalStrength: 0,
        lastSeen: new Date().toISOString(),
        counter1: 0,
        counter2: 0,
        counter3: 0,
        counter4: 0,
        ain1: 0,
        ain2: 0,
        ain3: 0,
        ain4: 0,
        ain5: 0,
        ain6: 0,
        ain7: 0,
        ain8: 0,
        din: 'unknown',
        temperature: 0,
        humidity: 0,
        createdAt: new Date().toISOString().split('T')[0]
      };
      setDevices(prev => [...prev, newDevice]);
    }
    handleCloseDialog();
  };

  const handleDelete = (id: number) => {
    setDevices(prev => prev.filter(d => d.id !== id));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'success';
      case 'offline': return 'error';
      case 'maintenance': return 'warning';
      default: return 'default';
    }
  };

  const getSignalIcon = (signalStrength: number) => {
    if (signalStrength === 0) return <NoSignalIcon />;
    if (signalStrength > 80) return <SignalIcon />;
    return <SignalIcon />;
  };

  const formatLastSeen = (lastSeen: string) => {
    const now = new Date();
    const last = new Date(lastSeen);
    const diff = now.getTime() - last.getTime();
    const minutes = Math.floor(diff / 60000);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
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
                {devices.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Online Devices
              </Typography>
              <Typography variant="h4" color="success.main">
                {devices.filter(d => d.status === 'online').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Average Signal
              </Typography>
              <Typography variant="h4">
                {Math.round(devices.reduce((sum, d) => sum + d.signalStrength, 0) / devices.length)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Production
              </Typography>
              <Typography variant="h4" color="primary.main">
                {devices.reduce((sum, d) => sum + d.counter1 + d.counter2 + d.counter3 + d.counter4, 0)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Devices Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Device</TableCell>
                <TableCell>Factory</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Signal</TableCell>
                <TableCell>Power (AIN1)</TableCell>
                <TableCell>Temperature</TableCell>
                <TableCell>Door Status</TableCell>
                <TableCell>Last Seen</TableCell>
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
                        {device.name}
                      </Box>
                    </TableCell>
                    <TableCell>{device.factoryName}</TableCell>
                    <TableCell>
                      <Chip
                        icon={device.status === 'online' ? <CheckCircleIcon /> : <CancelIcon />}
                        label={device.status}
                        color={getStatusColor(device.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center">
                        {getSignalIcon(device.signalStrength)}
                        <Typography variant="body2" sx={{ ml: 1 }}>
                          {device.signalStrength}%
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {device.ain1 > 0 ? `${device.ain1}V` : 'N/A'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {device.temperature > 0 ? `${device.temperature}°C` : 'N/A'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={device.din}
                        size="small"
                        color={device.din === 'open' ? 'error' : 'success'}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {formatLastSeen(device.lastSeen)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Tooltip title="Refresh Data">
                        <IconButton size="small" color="primary">
                          <RefreshIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit Device">
                        <IconButton
                          size="small"
                          onClick={() => handleOpenDialog(device)}
                          color="primary"
                        >
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Device Settings">
                        <IconButton size="small" color="secondary">
                          <SettingsIcon />
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

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingDevice ? 'Edit Device' : 'Add New Device'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
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
                >
                  <MenuItem value={1}>Baghdad Central Mill</MenuItem>
                  <MenuItem value={2}>Basra Grain Factory</MenuItem>
                  <MenuItem value={3}>Mosul Processing Plant</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={formData.status}
                  label="Status"
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                >
                  <MenuItem value="online">Online</MenuItem>
                  <MenuItem value="offline">Offline</MenuItem>
                  <MenuItem value="maintenance">Maintenance</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingDevice ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Devices; 