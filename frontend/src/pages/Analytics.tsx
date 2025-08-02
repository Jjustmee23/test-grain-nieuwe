import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Chip,
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
  Tooltip
} from '@mui/material';
import {
  Analytics as AnalyticsIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Factory as FactoryIcon,
  LocalShipping as BatchIcon,
  Power as PowerIcon
} from '@mui/icons-material';

interface ProductionData {
  date: string;
  factory: string;
  wheatProcessed: number;
  flourProduced: number;
  efficiency: number;
  powerConsumption: number;
  batches: number;
}

interface FactoryComparison {
  factory: string;
  totalProduction: number;
  efficiency: number;
  uptime: number;
  powerEfficiency: number;
  batchCount: number;
}

const Analytics: React.FC = () => {
  const [productionData, setProductionData] = useState<ProductionData[]>([]);
  const [factoryComparison, setFactoryComparison] = useState<FactoryComparison[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTimeframe, setSelectedTimeframe] = useState('7d');
  const [selectedFactory, setSelectedFactory] = useState('all');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Mock data - replace with API calls
  useEffect(() => {
    const mockProductionData: ProductionData[] = Array.from({ length: 30 }, (_, i) => ({
      date: new Date(Date.now() - (29 - i) * 24 * 3600000).toLocaleDateString(),
      factory: ['Baghdad Central Mill', 'Basra Grain Factory', 'Mosul Processing Plant'][Math.floor(Math.random() * 3)],
      wheatProcessed: 800 + Math.random() * 400,
      flourProduced: 680 + Math.random() * 340,
      efficiency: 85 + Math.random() * 10,
      powerConsumption: 40 + Math.random() * 20,
      batches: 3 + Math.floor(Math.random() * 5)
    }));

    const mockFactoryComparison: FactoryComparison[] = [
      {
        factory: 'Baghdad Central Mill',
        totalProduction: 12500,
        efficiency: 87.5,
        uptime: 94.2,
        powerEfficiency: 92.1,
        batchCount: 45
      },
      {
        factory: 'Basra Grain Factory',
        totalProduction: 9800,
        efficiency: 89.3,
        uptime: 96.8,
        powerEfficiency: 94.7,
        batchCount: 38
      },
      {
        factory: 'Mosul Processing Plant',
        totalProduction: 7200,
        efficiency: 82.1,
        uptime: 88.5,
        powerEfficiency: 87.3,
        batchCount: 28
      }
    ];

    setTimeout(() => {
      setProductionData(mockProductionData);
      setFactoryComparison(mockFactoryComparison);
      setLoading(false);
    }, 1000);
  }, []);

  const getEfficiencyColor = (efficiency: number) => {
    if (efficiency >= 90) return 'success';
    if (efficiency >= 80) return 'warning';
    return 'error';
  };

  const getUptimeColor = (uptime: number) => {
    if (uptime >= 95) return 'success';
    if (uptime >= 85) return 'warning';
    return 'error';
  };

  const calculateTotals = () => {
    const totalWheat = productionData.reduce((sum, d) => sum + d.wheatProcessed, 0);
    const totalFlour = productionData.reduce((sum, d) => sum + d.flourProduced, 0);
    const avgEfficiency = productionData.reduce((sum, d) => sum + d.efficiency, 0) / productionData.length;
    const totalPower = productionData.reduce((sum, d) => sum + d.powerConsumption, 0);
    
    return { totalWheat, totalFlour, avgEfficiency, totalPower };
  };

  const handleExport = (format: 'csv' | 'pdf' | 'excel') => {
    // Mock export functionality
    console.log(`Exporting data in ${format} format`);
    alert(`Exporting data in ${format.toUpperCase()} format`);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const totals = calculateTotals();

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Production Analytics
        </Typography>
        <Box>
          <FormControl size="small" sx={{ mr: 2 }}>
            <Select
              value={selectedTimeframe}
              onChange={(e) => setSelectedTimeframe(e.target.value)}
            >
              <MenuItem value="1d">Last Day</MenuItem>
              <MenuItem value="7d">Last 7 Days</MenuItem>
              <MenuItem value="30d">Last 30 Days</MenuItem>
              <MenuItem value="90d">Last 90 Days</MenuItem>
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ mr: 2 }}>
            <Select
              value={selectedFactory}
              onChange={(e) => setSelectedFactory(e.target.value)}
            >
              <MenuItem value="all">All Factories</MenuItem>
              <MenuItem value="baghdad">Baghdad Central Mill</MenuItem>
              <MenuItem value="basra">Basra Grain Factory</MenuItem>
              <MenuItem value="mosul">Mosul Processing Plant</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => window.location.reload()}
            sx={{ mr: 1 }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            onClick={() => handleExport('csv')}
          >
            Export
          </Button>
        </Box>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Wheat Processed
              </Typography>
              <Typography variant="h4">
                {totals.totalWheat.toLocaleString()} kg
              </Typography>
              <Box display="flex" alignItems="center" mt={1}>
                <TrendingUpIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="body2" color="success.main">
                  +12.5% vs last period
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Flour Produced
              </Typography>
              <Typography variant="h4" color="primary.main">
                {totals.totalFlour.toLocaleString()} kg
              </Typography>
              <Box display="flex" alignItems="center" mt={1}>
                <TrendingUpIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="body2" color="success.main">
                  +8.3% vs last period
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Average Efficiency
              </Typography>
              <Typography variant="h4">
                {totals.avgEfficiency.toFixed(1)}%
              </Typography>
              <Box display="flex" alignItems="center" mt={1}>
                <TrendingUpIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="body2" color="success.main">
                  +2.1% vs last period
                </Typography>
              </Box>
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
                {totals.totalPower.toFixed(0)} kW
              </Typography>
              <Box display="flex" alignItems="center" mt={1}>
                <TrendingDownIcon color="error" sx={{ mr: 1 }} />
                <Typography variant="body2" color="error.main">
                  -5.2% vs last period
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Factory Comparison */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Factory Performance Comparison
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Factory</TableCell>
                  <TableCell align="right">Total Production (kg)</TableCell>
                  <TableCell align="right">Efficiency (%)</TableCell>
                  <TableCell align="right">Uptime (%)</TableCell>
                  <TableCell align="right">Power Efficiency (%)</TableCell>
                  <TableCell align="right">Batch Count</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {factoryComparison.map((factory) => (
                  <TableRow key={factory.factory}>
                    <TableCell>
                      <Box display="flex" alignItems="center">
                        <FactoryIcon sx={{ mr: 1, color: 'primary.main' }} />
                        {factory.factory}
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      {factory.totalProduction.toLocaleString()}
                    </TableCell>
                    <TableCell align="right">
                      <Chip
                        label={`${factory.efficiency.toFixed(1)}%`}
                        color={getEfficiencyColor(factory.efficiency) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Chip
                        label={`${factory.uptime.toFixed(1)}%`}
                        color={getUptimeColor(factory.uptime) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="right">
                      {factory.powerEfficiency.toFixed(1)}%
                    </TableCell>
                    <TableCell align="right">
                      {factory.batchCount}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Production Data Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Daily Production Data
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Date</TableCell>
                  <TableCell>Factory</TableCell>
                  <TableCell align="right">Wheat Processed (kg)</TableCell>
                  <TableCell align="right">Flour Produced (kg)</TableCell>
                  <TableCell align="right">Efficiency (%)</TableCell>
                  <TableCell align="right">Power (kW)</TableCell>
                  <TableCell align="right">Batches</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {productionData
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((data, index) => (
                    <TableRow key={index}>
                      <TableCell>{data.date}</TableCell>
                      <TableCell>{data.factory}</TableCell>
                      <TableCell align="right">
                        {data.wheatProcessed.toLocaleString()}
                      </TableCell>
                      <TableCell align="right">
                        {data.flourProduced.toLocaleString()}
                      </TableCell>
                      <TableCell align="right">
                        <Chip
                          label={`${data.efficiency.toFixed(1)}%`}
                          color={getEfficiencyColor(data.efficiency) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">
                        {data.powerConsumption.toFixed(1)}
                      </TableCell>
                      <TableCell align="right">
                        {data.batches}
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            rowsPerPageOptions={[10, 25, 50]}
            component="div"
            count={productionData.length}
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

      {/* Export Options */}
      <Box mt={3} display="flex" gap={2}>
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={() => handleExport('csv')}
        >
          Export CSV
        </Button>
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={() => handleExport('excel')}
        >
          Export Excel
        </Button>
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={() => handleExport('pdf')}
        >
          Export PDF
        </Button>
      </Box>
    </Box>
  );
};

export default Analytics; 