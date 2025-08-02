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
  Alert,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider
} from '@mui/material';
import {
  Power as PowerIcon,
  PowerOff as PowerOffIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Refresh as RefreshIcon,
  Timeline as TimelineIcon,
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  Visibility as ViewIcon,
  Bolt as BoltIcon
} from '@mui/icons-material';


interface PowerEvent {
  id: number;
  deviceId: number;
  deviceName: string;
  factoryName: string;
  eventType: 'power_loss' | 'power_restore' | 'voltage_fluctuation' | 'overload';
  timestamp: string;
  voltage: number;
  duration?: number; // in minutes
  description: string;
  resolved: boolean;
}

interface PowerData {
  timestamp: string;
  voltage: number;
  current: number;
  power: number;
  deviceId: number;
}

interface Device {
  id: number;
  name: string;
  factoryName: string;
  status: 'online' | 'offline';
  currentVoltage: number;
  lastUpdate: string;
  powerConsumption: number;
}

const PowerManagement: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [powerEvents, setPowerEvents] = useState<PowerEvent[]>([]);
  const [powerData, setPowerData] = useState<PowerData[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTimeframe, setSelectedTimeframe] = useState('24h');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Mock data - replace with API calls
  useEffect(() => {
    const mockDevices: Device[] = [
      {
        id: 1,
        name: 'Device-001',
        factoryName: 'Baghdad Central Mill',
        status: 'online',
        currentVoltage: 220.5,
        lastUpdate: new Date().toISOString(),
        powerConsumption: 45.2
      },
      {
        id: 2,
        name: 'Device-002',
        factoryName: 'Baghdad Central Mill',
        status: 'offline',
        currentVoltage: 0,
        lastUpdate: new Date(Date.now() - 3600000).toISOString(),
        powerConsumption: 0
      },
      {
        id: 3,
        name: 'Device-003',
        factoryName: 'Basra Grain Factory',
        status: 'online',
        currentVoltage: 218.7,
        lastUpdate: new Date().toISOString(),
        powerConsumption: 38.9
      }
    ];

    const mockPowerEvents: PowerEvent[] = [
      {
        id: 1,
        deviceId: 2,
        deviceName: 'Device-002',
        factoryName: 'Baghdad Central Mill',
        eventType: 'power_loss',
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        voltage: 0,
        duration: 60,
        description: 'Power loss detected - checking backup systems',
        resolved: false
      },
      {
        id: 2,
        deviceId: 1,
        deviceName: 'Device-001',
        factoryName: 'Baghdad Central Mill',
        eventType: 'voltage_fluctuation',
        timestamp: new Date(Date.now() - 7200000).toISOString(),
        voltage: 235.2,
        description: 'Voltage spike detected - monitoring closely',
        resolved: true
      },
      {
        id: 3,
        deviceId: 3,
        deviceName: 'Device-003',
        factoryName: 'Basra Grain Factory',
        eventType: 'power_restore',
        timestamp: new Date(Date.now() - 10800000).toISOString(),
        voltage: 220.1,
        description: 'Power restored after maintenance',
        resolved: true
      }
    ];

    const mockPowerData: PowerData[] = Array.from({ length: 24 }, (_, i) => ({
      timestamp: new Date(Date.now() - (23 - i) * 3600000).toLocaleTimeString(),
      voltage: 220 + Math.random() * 10 - 5,
      current: 20 + Math.random() * 10,
      power: 4400 + Math.random() * 1000,
      deviceId: 1
    }));

    setTimeout(() => {
      setDevices(mockDevices);
      setPowerEvents(mockPowerEvents);
      setPowerData(mockPowerData);
      setLoading(false);
    }, 1000);
  }, []);

  const getEventTypeColor = (eventType: string) => {
    switch (eventType) {
      case 'power_loss': return 'error';
      case 'power_restore': return 'success';
      case 'voltage_fluctuation': return 'warning';
      case 'overload': return 'error';
      default: return 'default';
    }
  };

  const getEventTypeIcon = (eventType: string) => {
    switch (eventType) {
      case 'power_loss': return <PowerOffIcon />;
      case 'power_restore': return <PowerIcon />;
      case 'voltage_fluctuation': return <WarningIcon />;
      case 'overload': return <WarningIcon />;
      default: return <PowerIcon />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getVoltageStatus = (voltage: number) => {
    if (voltage === 0) return { status: 'No Power', color: 'error' };
    if (voltage < 200) return { status: 'Low Voltage', color: 'warning' };
    if (voltage > 250) return { status: 'High Voltage', color: 'warning' };
    return { status: 'Normal', color: 'success' };
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
          Power Management
        </Typography>
        <Box>
          <FormControl size="small" sx={{ mr: 2 }}>
            <Select
              value={selectedTimeframe}
              onChange={(e) => setSelectedTimeframe(e.target.value)}
            >
              <MenuItem value="1h">Last Hour</MenuItem>
              <MenuItem value="24h">Last 24 Hours</MenuItem>
              <MenuItem value="7d">Last 7 Days</MenuItem>
              <MenuItem value="30d">Last 30 Days</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => window.location.reload()}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} mb={3}>
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
                Total Power Consumption
              </Typography>
              <Typography variant="h4">
                {devices.reduce((sum, d) => sum + d.powerConsumption, 0).toFixed(1)} kW
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active Power Events
              </Typography>
              <Typography variant="h4" color="warning.main">
                {powerEvents.filter(e => !e.resolved).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Average Voltage
              </Typography>
              <Typography variant="h4">
                {(devices.reduce((sum, d) => sum + d.currentVoltage, 0) / devices.filter(d => d.currentVoltage > 0).length).toFixed(1)}V
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Power Chart */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Power Consumption Over Time
          </Typography>
          <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'grey.100' }}>
            <Typography variant="body2" color="text.secondary">
              Chart will be displayed here (Recharts integration pending)
            </Typography>
          </Box>
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        {/* Devices Status */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Device Power Status
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Device</TableCell>
                      <TableCell>Factory</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Voltage</TableCell>
                      <TableCell>Power (kW)</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {devices.map((device) => {
                      const voltageStatus = getVoltageStatus(device.currentVoltage);
                      return (
                        <TableRow key={device.id}>
                          <TableCell>
                            <Box display="flex" alignItems="center">
                              {device.status === 'online' ? <PowerIcon color="success" /> : <PowerOffIcon color="error" />}
                              <Typography sx={{ ml: 1 }}>{device.name}</Typography>
                            </Box>
                          </TableCell>
                          <TableCell>{device.factoryName}</TableCell>
                          <TableCell>
                            <Chip
                              label={device.status}
                              color={device.status === 'online' ? 'success' : 'error'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={`${device.currentVoltage}V`}
                              color={voltageStatus.color as any}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>{device.powerConsumption.toFixed(1)}</TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Power Events */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Power Events
              </Typography>
              <List>
                {powerEvents.slice(0, 5).map((event) => (
                  <React.Fragment key={event.id}>
                    <ListItem>
                      <ListItemIcon>
                        {getEventTypeIcon(event.eventType)}
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box display="flex" justifyContent="space-between" alignItems="center">
                            <Typography variant="body2">
                              {event.deviceName} - {event.factoryName}
                            </Typography>
                            <Chip
                              label={event.eventType.replace('_', ' ')}
                              color={getEventTypeColor(event.eventType) as any}
                              size="small"
                            />
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="caption" display="block">
                              {formatTimestamp(event.timestamp)}
                            </Typography>
                            <Typography variant="body2">
                              {event.description}
                            </Typography>
                            {event.voltage > 0 && (
                              <Typography variant="caption" color="textSecondary">
                                Voltage: {event.voltage}V
                              </Typography>
                            )}
                          </Box>
                        }
                      />
                    </ListItem>
                    <Divider />
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Power Events Table */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            All Power Events
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Device</TableCell>
                  <TableCell>Factory</TableCell>
                  <TableCell>Event Type</TableCell>
                  <TableCell>Timestamp</TableCell>
                  <TableCell>Voltage</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Description</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {powerEvents
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((event) => (
                    <TableRow key={event.id}>
                      <TableCell>{event.deviceName}</TableCell>
                      <TableCell>{event.factoryName}</TableCell>
                      <TableCell>
                        <Chip
                          icon={getEventTypeIcon(event.eventType)}
                          label={event.eventType.replace('_', ' ')}
                          color={getEventTypeColor(event.eventType) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{formatTimestamp(event.timestamp)}</TableCell>
                      <TableCell>{event.voltage}V</TableCell>
                      <TableCell>{event.duration ? `${event.duration} min` : 'N/A'}</TableCell>
                      <TableCell>
                        <Chip
                          icon={event.resolved ? <CheckCircleIcon /> : <CancelIcon />}
                          label={event.resolved ? 'Resolved' : 'Active'}
                          color={event.resolved ? 'success' : 'error'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" noWrap>
                          {event.description}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            rowsPerPageOptions={[5, 10, 25]}
            component="div"
            count={powerEvents.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={(event, newPage) => setPage(newPage)}
            onRowsPerPageChange={(event) => {
              setRowsPerPage(parseInt(event.target.value, 10));
              setPage(0);
            }}
          />
        </CardContent>
      </Card>
    </Box>
  );
};

export default PowerManagement; 