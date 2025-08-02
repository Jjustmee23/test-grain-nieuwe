import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  IconButton,
  FormControl,
  FormControlLabel,
  Checkbox,
  Radio,
  RadioGroup,
  Button,
  LinearProgress,
  Alert,
  Tooltip,
  Divider,
  Paper,
  Select,
  MenuItem,
  InputLabel,
  TextField
} from '@mui/material';
import {
  Factory as FactoryIcon,
  DeviceHub as DeviceIcon,
  Power as PowerIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
  Visibility as ViewIcon,
  Bolt as BoltIcon,
  Lock as LockIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import { useSnackbar } from 'notistack';

interface Factory {
  id: number;
  name: string;
  cityId: number;
  cityName: string;
  status: boolean;
  group: string;
  address: string;
  createdAt: string;
  devices: Device[];
  stats: FactoryStats;
}

interface Device {
  id: string;
  name: string;
  factoryId: number;
  status: boolean;
  serialNumber?: string;
  selectedCounter: string;
  createdAt: string;
}

interface FactoryStats {
  daily: number;
  weekly: number;
  monthly: number;
  yearly: number;
  deviceCount: number;
  onlineDevices: number;
  powerStatus: 'on' | 'off';
  doorStatus: 'open' | 'closed';
  startTime?: string;
  stopTime?: string;
}

interface City {
  id: number;
  name: string;
}

const Dashboard: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const { enqueueSnackbar } = useSnackbar();
  
  const [factories, setFactories] = useState<Factory[]>([]);
  const [cities, setCities] = useState<City[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  // Filters
  const [selectedCities, setSelectedCities] = useState<number[]>([]);
  const [selectedSector, setSelectedSector] = useState<string>('all');
  const [selectedPowerStatus, setSelectedPowerStatus] = useState<string>('all');
  const [selectedDoorStatus, setSelectedDoorStatus] = useState<string>('all');
  const [showFilters, setShowFilters] = useState(false);

  // Summary totals
  const [summaryTotals, setSummaryTotals] = useState({
    daily: 0,
    weekly: 0,
    monthly: 0,
    yearly: 0
  });

  // Fetch factories with devices and stats
  const fetchFactories = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.REACT_APP_API_URL || '/api';
      const response = await fetch(`${apiUrl}/factories/stats/public`, {
        headers: {
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
        calculateSummaryTotals(result.data);
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

  // Fetch cities for filters
  const fetchCities = async () => {
    try {
      const apiUrl = process.env.REACT_APP_API_URL || '/api';
      const response = await fetch(`${apiUrl}/cities/public`, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setCities(result.data);
        }
      }
    } catch (error) {
      console.error('Error fetching cities:', error);
    }
  };

  // Calculate summary totals
  const calculateSummaryTotals = (factories: Factory[]) => {
    const totals = factories.reduce((acc, factory) => ({
      daily: acc.daily + factory.stats.daily,
      weekly: acc.weekly + factory.stats.weekly,
      monthly: acc.monthly + factory.stats.monthly,
      yearly: acc.yearly + factory.stats.yearly
    }), { daily: 0, weekly: 0, monthly: 0, yearly: 0 });

    setSummaryTotals(totals);
  };

  // Filter factories based on selected filters
  const getFilteredFactories = () => {
    return factories.filter(factory => {
      // City filter
      if (selectedCities.length > 0 && !selectedCities.includes(factory.cityId)) {
        return false;
      }

      // Sector filter
      if (selectedSector !== 'all' && factory.group !== selectedSector) {
        return false;
      }

      // Power status filter
      if (selectedPowerStatus !== 'all' && factory.stats.powerStatus !== selectedPowerStatus) {
        return false;
      }

      // Door status filter
      if (selectedDoorStatus !== 'all' && factory.stats.doorStatus !== selectedDoorStatus) {
        return false;
      }

      return true;
    });
  };

  // Handle city selection
  const handleCityChange = (cityId: number) => {
    setSelectedCities(prev => 
      prev.includes(cityId) 
        ? prev.filter(id => id !== cityId)
        : [...prev, cityId]
    );
  };

  // Handle "All Cities" selection
  const handleAllCitiesChange = (checked: boolean) => {
    if (checked) {
      setSelectedCities(cities.map(city => city.id));
    } else {
      setSelectedCities([]);
    }
  };

  // Refresh data
  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchFactories();
    setRefreshing(false);
    enqueueSnackbar('Data refreshed successfully', { variant: 'success' });
  };

  useEffect(() => {
    fetchFactories();
    fetchCities();
  }, []);

  const filteredFactories = getFilteredFactories();

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <LinearProgress sx={{ width: '50%' }} />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Welcome back, {user?.name || 'User'}! Monitor your mill production in real-time.
          </Typography>
        </Box>
        <Box display="flex" gap={1}>
          <Button
            variant="outlined"
            startIcon={<FilterIcon />}
            onClick={() => setShowFilters(!showFilters)}
          >
            Filters
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={refreshing}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      {showFilters && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Filter Options
          </Typography>
          <Grid container spacing={3}>
            {/* Cities Filter */}
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" gutterBottom>
                Select Cities
              </Typography>
              <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={selectedCities.length === cities.length}
                      indeterminate={selectedCities.length > 0 && selectedCities.length < cities.length}
                      onChange={(e) => handleAllCitiesChange(e.target.checked)}
                    />
                  }
                  label="All Cities"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={selectedCities.length === 0}
                      onChange={(e) => setSelectedCities([])}
                    />
                  }
                  label="Unselect All Cities"
                />
                <Divider sx={{ my: 1 }} />
                {cities.map((city) => (
                  <FormControlLabel
                    key={city.id}
                    control={
                      <Checkbox
                        checked={selectedCities.includes(city.id)}
                        onChange={() => handleCityChange(city.id)}
                      />
                    }
                    label={city.name}
                  />
                ))}
              </Box>
            </Grid>

            {/* Sector Filter */}
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" gutterBottom>
                Filter by Sector
              </Typography>
              <RadioGroup
                value={selectedSector}
                onChange={(e) => setSelectedSector(e.target.value)}
              >
                <FormControlLabel value="all" control={<Radio />} label="All Sectors" />
                <FormControlLabel value="private" control={<Radio />} label="Private" />
                <FormControlLabel value="government" control={<Radio />} label="Government" />
                <FormControlLabel value="commercial" control={<Radio />} label="Commercial" />
              </RadioGroup>
            </Grid>

            {/* Power Status Filter */}
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" gutterBottom>
                Filter by Power Status
              </Typography>
              <RadioGroup
                value={selectedPowerStatus}
                onChange={(e) => setSelectedPowerStatus(e.target.value)}
              >
                <FormControlLabel value="all" control={<Radio />} label="All Power Status" />
                <FormControlLabel value="on" control={<Radio />} label="Power ON" />
                <FormControlLabel value="off" control={<Radio />} label="Power OFF" />
              </RadioGroup>
            </Grid>

            {/* Door Status Filter */}
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" gutterBottom>
                Filter by Door Status
              </Typography>
              <RadioGroup
                value={selectedDoorStatus}
                onChange={(e) => setSelectedDoorStatus(e.target.value)}
              >
                <FormControlLabel value="all" control={<Radio />} label="All Door Status" />
                <FormControlLabel value="open" control={<Radio />} label="Door Open" />
                <FormControlLabel value="closed" control={<Radio />} label="Door Closed" />
              </RadioGroup>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Summary Totals */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Daily Total
              </Typography>
              <Typography variant="h4">
                {summaryTotals.daily.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Weekly Total
              </Typography>
              <Typography variant="h4">
                {summaryTotals.weekly.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Monthly Total
              </Typography>
              <Typography variant="h4">
                {summaryTotals.monthly.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Yearly Total
              </Typography>
              <Typography variant="h4">
                {summaryTotals.yearly.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Factories Grid */}
      <Box>
        <Typography variant="h5" gutterBottom>
          Factories ({filteredFactories.length})
        </Typography>
        <Grid container spacing={3}>
          {filteredFactories.map((factory) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={factory.id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  {/* Factory Header */}
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        {factory.name}
                      </Typography>
                      <Chip
                        label="Active"
                        color="success"
                        size="small"
                        icon={<CheckCircleIcon />}
                      />
                    </Box>
                    <FactoryIcon color="primary" />
                  </Box>

                  {/* Status Indicators */}
                  <Box display="flex" gap={1} mb={2}>
                    <Chip
                      icon={<BoltIcon />}
                      label={`Power: ${factory.stats.powerStatus === 'on' ? 'On' : 'Off'}`}
                      color={factory.stats.powerStatus === 'on' ? 'success' : 'default'}
                      size="small"
                    />
                    <Chip
                      icon={<LockIcon />}
                      label={`Door: ${factory.stats.doorStatus === 'open' ? 'Open' : 'Closed'}`}
                      color={factory.stats.doorStatus === 'open' ? 'warning' : 'default'}
                      size="small"
                    />
                  </Box>

                  {/* Production Stats */}
                  <Box mb={2}>
                    <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                      Production Metrics
                    </Typography>
                    <Grid container spacing={1}>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="textSecondary">
                          Daily: {factory.stats.daily.toLocaleString()}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="textSecondary">
                          Weekly: {factory.stats.weekly.toLocaleString()}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="textSecondary">
                          Monthly: {factory.stats.monthly.toLocaleString()}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="textSecondary">
                          Yearly: {factory.stats.yearly.toLocaleString()}
                        </Typography>
                      </Grid>
                    </Grid>
                  </Box>

                  {/* Device Info */}
                  <Box mb={2}>
                    <Typography variant="body2" color="textSecondary">
                      Devices: {factory.stats.onlineDevices}/{factory.stats.deviceCount} Online
                    </Typography>
                  </Box>

                  {/* Time Info */}
                  <Box mb={2}>
                    <Typography variant="body2" color="textSecondary">
                      Start Time: {factory.stats.startTime || '--'}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Stop Time: {factory.stats.stopTime || '--'}
                    </Typography>
                  </Box>

                  {/* Action Button */}
                  <Button
                    variant="contained"
                    startIcon={<ViewIcon />}
                    fullWidth
                    size="small"
                  >
                    View Statistics
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {filteredFactories.length === 0 && (
          <Alert severity="info">
            No factories match the selected filters. Try adjusting your filter criteria.
          </Alert>
        )}
      </Box>
    </Box>
  );
};

export default Dashboard; 