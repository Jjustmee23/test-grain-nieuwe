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
  Cancel as CancelIcon
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';

interface Factory {
  id: number;
  name: string;
  city: string;
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
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingFactory, setEditingFactory] = useState<Factory | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [formData, setFormData] = useState({
    name: '',
    city: '',
    group: '',
    address: '',
    phone: '',
    email: ''
  });

  // Mock data - replace with API calls
  useEffect(() => {
    const mockFactories: Factory[] = [
      {
        id: 1,
        name: 'Baghdad Central Mill',
        city: 'Baghdad',
        status: true,
        group: 'Government',
        address: '123 Industrial Zone, Baghdad',
        phone: '+964 123 456 789',
        email: 'baghdad@mill.com',
        createdAt: '2024-01-15',
        deviceCount: 8,
        activeBatches: 3
      },
      {
        id: 2,
        name: 'Basra Grain Factory',
        city: 'Basra',
        status: true,
        group: 'Private',
        address: '456 Port Road, Basra',
        phone: '+964 987 654 321',
        email: 'basra@mill.com',
        createdAt: '2024-02-20',
        deviceCount: 12,
        activeBatches: 5
      },
      {
        id: 3,
        name: 'Mosul Processing Plant',
        city: 'Mosul',
        status: false,
        group: 'Commercial',
        address: '789 Northern District, Mosul',
        phone: '+964 555 123 456',
        email: 'mosul@mill.com',
        createdAt: '2024-03-10',
        deviceCount: 6,
        activeBatches: 0
      }
    ];

    setTimeout(() => {
      setFactories(mockFactories);
      setLoading(false);
    }, 1000);
  }, []);

  const handleOpenDialog = (factory?: Factory) => {
    if (factory) {
      setEditingFactory(factory);
      setFormData({
        name: factory.name,
        city: factory.city,
        group: factory.group,
        address: factory.address,
        phone: factory.phone,
        email: factory.email
      });
    } else {
      setEditingFactory(null);
      setFormData({
        name: '',
        city: '',
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

  const handleSubmit = () => {
    if (editingFactory) {
      // Update existing factory
      setFactories(prev => prev.map(f => 
        f.id === editingFactory.id 
          ? { ...f, ...formData }
          : f
      ));
      enqueueSnackbar('Factory updated successfully', { variant: 'success' });
    } else {
      // Add new factory
      const newFactory: Factory = {
        id: Math.max(...factories.map(f => f.id)) + 1,
        ...formData,
        status: true,
        createdAt: new Date().toISOString().split('T')[0],
        deviceCount: 0,
        activeBatches: 0
      };
      setFactories(prev => [...prev, newFactory]);
      enqueueSnackbar('Factory added successfully', { variant: 'success' });
    }
    handleCloseDialog();
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
                        {factory.city}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={factory.group} 
                        size="small"
                        color={factory.group === 'Government' ? 'primary' : 'secondary'}
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
              <TextField
                fullWidth
                label="City"
                value={formData.city}
                onChange={(e) => setFormData({ ...formData, city: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Group</InputLabel>
                <Select
                  value={formData.group}
                  label="Group"
                  onChange={(e) => setFormData({ ...formData, group: e.target.value })}
                >
                  <MenuItem value="Government">Government</MenuItem>
                  <MenuItem value="Private">Private</MenuItem>
                  <MenuItem value="Commercial">Commercial</MenuItem>
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
          <Button onClick={handleSubmit} variant="contained">
            {editingFactory ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Factories; 