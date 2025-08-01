import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Divider,
  LinearProgress,
  Alert,
  Button,
  Tooltip
} from '@mui/material';
import {
  Factory as FactoryIcon,
  DeviceHub as DeviceIcon,
  LocalShipping as BatchIcon,
  Power as PowerIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Notifications as NotificationsIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { RootState } from '../store';

interface SystemStatus {
  factories: {
    total: number;
    active: number;
    inactive: number;
  };
  devices: {
    total: number;
    online: number;
    offline: number;
    maintenance: number;
  };
  batches: {
    total: number;
    active: number;
    completed: number;
    pending: number;
  };
  power: {
    totalConsumption: number;
    averageVoltage: number;
    activeEvents: number;
  };
}

interface RecentActivity {
  id: number;
  type: 'batch' | 'power' | 'device' | 'system';
  message: string;
  timestamp: string;
  severity: 'info' | 'warning' | 'error' | 'success';
}

const Dashboard: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    factories: { total: 0, active: 0, inactive: 0 },
    devices: { total: 0, online: 0, offline: 0, maintenance: 0 },
    batches: { total: 0, active: 0, completed: 0, pending: 0 },
    power: { totalConsumption: 0, averageVoltage: 0, activeEvents: 0 }
  });
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);

  // Mock data - replace with API calls
  useEffect(() => {
    const mockSystemStatus: SystemStatus = {
      factories: { total: 3, active: 2, inactive: 1 },
      devices: { total: 26, online: 22, offline: 3, maintenance: 1 },
      batches: { total: 111, active: 8, completed: 98, pending: 5 },
      power: { totalConsumption: 124.1, averageVoltage: 219.8, activeEvents: 2 }
    };

    const mockRecentActivity: RecentActivity[] = [
      {
        id: 1,
        type: 'batch',
        message: 'Batch-2024-001 completed successfully',
        timestamp: new Date(Date.now() - 300000).toISOString(),
        severity: 'success'
      },
      {
        id: 2,
        type: 'power',
        message: 'Power loss detected on Device-002',
        timestamp: new Date(Date.now() - 600000).toISOString(),
        severity: 'error'
      },
      {
        id: 3,
        type: 'device',
        message: 'Device-003 went offline',
        timestamp: new Date(Date.now() - 900000).toISOString(),
        severity: 'warning'
      },
      {
        id: 4,
        type: 'system',
        message: 'System backup completed',
        timestamp: new Date(Date.now() - 1200000).toISOString(),
        severity: 'info'
      },
      {
        id: 5,
        type: 'batch',
        message: 'New batch Batch-2024-012 started',
        timestamp: new Date(Date.now() - 1500000).toISOString(),
        severity: 'info'
      }
    ];

    setTimeout(() => {
      setSystemStatus(mockSystemStatus);
      setRecentActivity(mockRecentActivity);
      setLoading(false);
    }, 1000);
  }, []);

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'success': return <CheckCircleIcon color="success" />;
      case 'warning': return <WarningIcon color="warning" />;
      case 'error': return <ErrorIcon color="error" />;
      default: return <CheckCircleIcon color="info" />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diff = now.getTime() - time.getTime();
    const minutes = Math.floor(diff / 60000);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  const getActivityTypeIcon = (type: string) => {
    switch (type) {
      case 'batch': return <BatchIcon />;
      case 'power': return <PowerIcon />;
      case 'device': return <DeviceIcon />;
      case 'system': return <TimelineIcon />;
      default: return <NotificationsIcon />;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <LinearProgress sx={{ width: '50%' }} />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Welcome back, {user?.name || 'User'}! Here's what's happening with your mills today.
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => window.location.reload()}
        >
          Refresh
        </Button>
      </Box>

      {/* System Overview Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Factories
                  </Typography>
                  <Typography variant="h4">
                    {systemStatus.factories.total}
                  </Typography>
                  <Box display="flex" alignItems="center" mt={1}>
                    <CheckCircleIcon color="success" sx={{ mr: 1, fontSize: 'small' }} />
                    <Typography variant="body2" color="success.main">
                      {systemStatus.factories.active} Active
                    </Typography>
                  </Box>
                </Box>
                <FactoryIcon color="primary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    IoT Devices
                  </Typography>
                  <Typography variant="h4">
                    {systemStatus.devices.total}
                  </Typography>
                  <Box display="flex" alignItems="center" mt={1}>
                    <CheckCircleIcon color="success" sx={{ mr: 1, fontSize: 'small' }} />
                    <Typography variant="body2" color="success.main">
                      {systemStatus.devices.online} Online
                    </Typography>
                  </Box>
                </Box>
                <DeviceIcon color="primary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Active Batches
                  </Typography>
                  <Typography variant="h4" color="primary.main">
                    {systemStatus.batches.active}
                  </Typography>
                  <Box display="flex" alignItems="center" mt={1}>
                    <TrendingUpIcon color="success" sx={{ mr: 1, fontSize: 'small' }} />
                    <Typography variant="body2" color="success.main">
                      {systemStatus.batches.completed} Completed
                    </Typography>
                  </Box>
                </Box>
                <BatchIcon color="primary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Power Consumption
                  </Typography>
                  <Typography variant="h4">
                    {systemStatus.power.totalConsumption} kW
                  </Typography>
                  <Box display="flex" alignItems="center" mt={1}>
                    <PowerIcon color="primary" sx={{ mr: 1, fontSize: 'small' }} />
                    <Typography variant="body2" color="text.secondary">
                      {systemStatus.power.averageVoltage}V Avg
                    </Typography>
                  </Box>
                </Box>
                <PowerIcon color="primary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alerts and Status */}
      {systemStatus.power.activeEvents > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>{systemStatus.power.activeEvents} active power events</strong> detected. 
            Please check the Power Management section for details.
          </Typography>
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* System Health */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Health Overview
              </Typography>
              <List>
                <ListItem>
                  <ListItemIcon>
                    <FactoryIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Factories Status"
                    secondary={`${systemStatus.factories.active}/${systemStatus.factories.total} Active`}
                  />
                  <ListItemSecondaryAction>
                    <Chip
                      label={`${Math.round((systemStatus.factories.active / systemStatus.factories.total) * 100)}%`}
                      color={systemStatus.factories.active === systemStatus.factories.total ? 'success' : 'warning'}
                      size="small"
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemIcon>
                    <DeviceIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Device Connectivity"
                    secondary={`${systemStatus.devices.online}/${systemStatus.devices.total} Online`}
                  />
                  <ListItemSecondaryAction>
                    <Chip
                      label={`${Math.round((systemStatus.devices.online / systemStatus.devices.total) * 100)}%`}
                      color={systemStatus.devices.online / systemStatus.devices.total > 0.8 ? 'success' : 'warning'}
                      size="small"
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemIcon>
                    <BatchIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Batch Processing"
                    secondary={`${systemStatus.batches.active} Active, ${systemStatus.batches.pending} Pending`}
                  />
                  <ListItemSecondaryAction>
                    <Chip
                      label="Active"
                      color="primary"
                      size="small"
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemIcon>
                    <PowerIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Power Status"
                    secondary={`${systemStatus.power.totalConsumption} kW, ${systemStatus.power.averageVoltage}V Avg`}
                  />
                  <ListItemSecondaryAction>
                    <Chip
                      label={systemStatus.power.activeEvents > 0 ? 'Warning' : 'Normal'}
                      color={systemStatus.power.activeEvents > 0 ? 'warning' : 'success'}
                      size="small"
                    />
                  </ListItemSecondaryAction>
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Activity
              </Typography>
              <List>
                {recentActivity.map((activity) => (
                  <ListItem key={activity.id}>
                    <ListItemIcon>
                      {getActivityTypeIcon(activity.type)}
                    </ListItemIcon>
                    <ListItemText
                      primary={activity.message}
                      secondary={formatTimestamp(activity.timestamp)}
                    />
                    <ListItemSecondaryAction>
                      {getSeverityIcon(activity.severity)}
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
              <Box mt={2}>
                <Button variant="outlined" fullWidth>
                  View All Activity
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<FactoryIcon />}
                    sx={{ py: 2 }}
                  >
                    Manage Factories
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<DeviceIcon />}
                    sx={{ py: 2 }}
                  >
                    Monitor Devices
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<BatchIcon />}
                    sx={{ py: 2 }}
                  >
                    View Batches
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<PowerIcon />}
                    sx={{ py: 2 }}
                  >
                    Power Management
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard; 