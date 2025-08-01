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
  Stepper,
  Step,
  StepLabel
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  LocalShipping as BatchIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Pending as PendingIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Visibility as ViewIcon,
  ThumbUp as ApproveIcon
} from '@mui/icons-material';

interface Batch {
  id: number;
  name: string;
  factoryId: number;
  factoryName: string;
  status: 'pending' | 'approved' | 'in_process' | 'completed' | 'cancelled';
  wheatQuantity: number;
  expectedFlour: number;
  actualFlour: number;
  wasteFactor: number;
  startDate: string;
  endDate?: string;
  progress: number;
  bagCount: number;
  operator: string;
  notes: string;
  createdAt: string;
}

const Batches: React.FC = () => {
  const [batches, setBatches] = useState<Batch[]>([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [viewDialog, setViewDialog] = useState(false);
  const [selectedBatch, setSelectedBatch] = useState<Batch | null>(null);
  const [editingBatch, setEditingBatch] = useState<Batch | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [formData, setFormData] = useState({
    name: '',
    factoryId: '',
    wheatQuantity: '',
    expectedFlour: '',
    wasteFactor: '',
    operator: '',
    notes: ''
  });

  // Mock data - replace with API calls
  useEffect(() => {
    const mockBatches: Batch[] = [
      {
        id: 1,
        name: 'Batch-2024-001',
        factoryId: 1,
        factoryName: 'Baghdad Central Mill',
        status: 'in_process',
        wheatQuantity: 1000,
        expectedFlour: 850,
        actualFlour: 680,
        wasteFactor: 0.15,
        startDate: '2024-01-15T08:00:00',
        progress: 80,
        bagCount: 136,
        operator: 'Ahmed Hassan',
        notes: 'Standard wheat processing batch',
        createdAt: '2024-01-15'
      },
      {
        id: 2,
        name: 'Batch-2024-002',
        factoryId: 1,
        factoryName: 'Baghdad Central Mill',
        status: 'completed',
        wheatQuantity: 1500,
        expectedFlour: 1275,
        actualFlour: 1275,
        wasteFactor: 0.15,
        startDate: '2024-01-14T06:00:00',
        endDate: '2024-01-14T18:00:00',
        progress: 100,
        bagCount: 255,
        operator: 'Mohammed Ali',
        notes: 'High-quality wheat batch',
        createdAt: '2024-01-14'
      },
      {
        id: 3,
        name: 'Batch-2024-003',
        factoryId: 2,
        factoryName: 'Basra Grain Factory',
        status: 'pending',
        wheatQuantity: 800,
        expectedFlour: 680,
        actualFlour: 0,
        wasteFactor: 0.15,
        startDate: '',
        progress: 0,
        bagCount: 0,
        operator: 'Fatima Zahra',
        notes: 'Pending approval',
        createdAt: '2024-01-16'
      }
    ];

    setTimeout(() => {
      setBatches(mockBatches);
      setLoading(false);
    }, 1000);
  }, []);

  const handleOpenDialog = (batch?: Batch) => {
    if (batch) {
      setEditingBatch(batch);
      setFormData({
        name: batch.name,
        factoryId: batch.factoryId.toString(),
        wheatQuantity: batch.wheatQuantity.toString(),
        expectedFlour: batch.expectedFlour.toString(),
        wasteFactor: batch.wasteFactor.toString(),
        operator: batch.operator,
        notes: batch.notes
      });
    } else {
      setEditingBatch(null);
      setFormData({
        name: '',
        factoryId: '',
        wheatQuantity: '',
        expectedFlour: '',
        wasteFactor: '',
        operator: '',
        notes: ''
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingBatch(null);
  };

  const handleViewBatch = (batch: Batch) => {
    setSelectedBatch(batch);
    setViewDialog(true);
  };

  const handleCloseViewDialog = () => {
    setViewDialog(false);
    setSelectedBatch(null);
  };

  const handleSubmit = () => {
    if (editingBatch) {
      setBatches(prev => prev.map(b => 
        b.id === editingBatch.id 
          ? { 
              ...b, 
              name: formData.name,
              factoryId: parseInt(formData.factoryId),
              wheatQuantity: parseFloat(formData.wheatQuantity),
              expectedFlour: parseFloat(formData.expectedFlour),
              wasteFactor: parseFloat(formData.wasteFactor),
              operator: formData.operator,
              notes: formData.notes
            }
          : b
      ));
    } else {
      const newBatch: Batch = {
        id: Math.max(...batches.map(b => b.id)) + 1,
        name: formData.name,
        factoryId: parseInt(formData.factoryId),
        factoryName: 'New Factory', // This would come from API
        status: 'pending',
        wheatQuantity: parseFloat(formData.wheatQuantity),
        expectedFlour: parseFloat(formData.expectedFlour),
        actualFlour: 0,
        wasteFactor: parseFloat(formData.wasteFactor),
        startDate: '',
        progress: 0,
        bagCount: 0,
        operator: formData.operator,
        notes: formData.notes,
        createdAt: new Date().toISOString().split('T')[0]
      };
      setBatches(prev => [...prev, newBatch]);
    }
    handleCloseDialog();
  };

  const handleDelete = (id: number) => {
    setBatches(prev => prev.filter(b => b.id !== id));
  };

  const handleStatusChange = (id: number, newStatus: Batch['status']) => {
    setBatches(prev => prev.map(b => {
      if (b.id === id) {
        const updated = { ...b, status: newStatus };
        if (newStatus === 'in_process' && !b.startDate) {
          updated.startDate = new Date().toISOString();
        }
        if (newStatus === 'completed' && !b.endDate) {
          updated.endDate = new Date().toISOString();
          updated.progress = 100;
        }
        return updated;
      }
      return b;
    }));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'warning';
      case 'approved': return 'info';
      case 'in_process': return 'primary';
      case 'completed': return 'success';
      case 'cancelled': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return <PendingIcon />;
      case 'approved': return <CheckCircleIcon />;
      case 'in_process': return <PlayIcon />;
      case 'completed': return <CheckCircleIcon />;
      case 'cancelled': return <CancelIcon />;
      default: return <PendingIcon />;
    }
  };

  const steps = ['Pending', 'Approved', 'In Process', 'Completed'];

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
          Batch Processing Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Create Batch
        </Button>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Batches
              </Typography>
              <Typography variant="h4">
                {batches.length}
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
                {batches.filter(b => b.status === 'in_process').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Wheat Processed
              </Typography>
              <Typography variant="h4">
                {batches.reduce((sum, b) => sum + b.wheatQuantity, 0)} kg
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Flour Produced
              </Typography>
              <Typography variant="h4" color="success.main">
                {batches.reduce((sum, b) => sum + b.actualFlour, 0)} kg
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Batches Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Batch Name</TableCell>
                <TableCell>Factory</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Wheat (kg)</TableCell>
                <TableCell>Expected Flour (kg)</TableCell>
                <TableCell>Actual Flour (kg)</TableCell>
                <TableCell>Progress</TableCell>
                <TableCell>Operator</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {batches
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((batch) => (
                  <TableRow key={batch.id}>
                    <TableCell>
                      <Box display="flex" alignItems="center">
                        <BatchIcon sx={{ mr: 1, color: 'primary.main' }} />
                        {batch.name}
                      </Box>
                    </TableCell>
                    <TableCell>{batch.factoryName}</TableCell>
                    <TableCell>
                      <Chip
                        icon={getStatusIcon(batch.status)}
                        label={batch.status.replace('_', ' ')}
                        color={getStatusColor(batch.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{batch.wheatQuantity}</TableCell>
                    <TableCell>{batch.expectedFlour}</TableCell>
                    <TableCell>{batch.actualFlour}</TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center">
                        <LinearProgress
                          variant="determinate"
                          value={batch.progress}
                          sx={{ width: 60, mr: 1 }}
                        />
                        <Typography variant="body2">
                          {batch.progress}%
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>{batch.operator}</TableCell>
                    <TableCell>{batch.createdAt}</TableCell>
                    <TableCell>
                      <Tooltip title="View Details">
                        <IconButton
                          size="small"
                          onClick={() => handleViewBatch(batch)}
                          color="primary"
                        >
                          <ViewIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit Batch">
                        <IconButton
                          size="small"
                          onClick={() => handleOpenDialog(batch)}
                          color="primary"
                        >
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      {batch.status === 'pending' && (
                        <Tooltip title="Approve Batch">
                          <IconButton
                            size="small"
                            onClick={() => handleStatusChange(batch.id, 'approved')}
                            color="success"
                          >
                            <ApproveIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                      {batch.status === 'approved' && (
                        <Tooltip title="Start Processing">
                          <IconButton
                            size="small"
                            onClick={() => handleStatusChange(batch.id, 'in_process')}
                            color="primary"
                          >
                            <PlayIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                      {batch.status === 'in_process' && (
                        <Tooltip title="Complete Batch">
                          <IconButton
                            size="small"
                            onClick={() => handleStatusChange(batch.id, 'completed')}
                            color="success"
                          >
                            <CheckCircleIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                      <Tooltip title="Delete Batch">
                        <IconButton
                          size="small"
                          onClick={() => handleDelete(batch.id)}
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
          count={batches.length}
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
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingBatch ? 'Edit Batch' : 'Create New Batch'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Batch Name"
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
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Wheat Quantity (kg)"
                type="number"
                value={formData.wheatQuantity}
                onChange={(e) => setFormData({ ...formData, wheatQuantity: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Expected Flour (kg)"
                type="number"
                value={formData.expectedFlour}
                onChange={(e) => setFormData({ ...formData, expectedFlour: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Waste Factor"
                type="number"
                inputProps={{ step: 0.01, min: 0, max: 1 }}
                value={formData.wasteFactor}
                onChange={(e) => setFormData({ ...formData, wasteFactor: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Operator"
                value={formData.operator}
                onChange={(e) => setFormData({ ...formData, operator: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Notes"
                multiline
                rows={3}
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingBatch ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Batch Details Dialog */}
      <Dialog open={viewDialog} onClose={handleCloseViewDialog} maxWidth="md" fullWidth>
        <DialogTitle>Batch Details - {selectedBatch?.name}</DialogTitle>
        <DialogContent>
          {selectedBatch && (
            <Box>
              <Stepper activeStep={steps.indexOf(selectedBatch.status.replace('_', ' '))} sx={{ mb: 3 }}>
                {steps.map((label) => (
                  <Step key={label}>
                    <StepLabel>{label}</StepLabel>
                  </Step>
                ))}
              </Stepper>
              
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="textSecondary">Factory</Typography>
                  <Typography variant="body1">{selectedBatch.factoryName}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="textSecondary">Status</Typography>
                  <Chip
                    icon={getStatusIcon(selectedBatch.status)}
                    label={selectedBatch.status.replace('_', ' ')}
                    color={getStatusColor(selectedBatch.status) as any}
                    size="small"
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="subtitle2" color="textSecondary">Wheat Quantity</Typography>
                  <Typography variant="body1">{selectedBatch.wheatQuantity} kg</Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="subtitle2" color="textSecondary">Expected Flour</Typography>
                  <Typography variant="body1">{selectedBatch.expectedFlour} kg</Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="subtitle2" color="textSecondary">Actual Flour</Typography>
                  <Typography variant="body1">{selectedBatch.actualFlour} kg</Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="subtitle2" color="textSecondary">Waste Factor</Typography>
                  <Typography variant="body1">{(selectedBatch.wasteFactor * 100).toFixed(1)}%</Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="subtitle2" color="textSecondary">Bag Count</Typography>
                  <Typography variant="body1">{selectedBatch.bagCount} bags</Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="subtitle2" color="textSecondary">Progress</Typography>
                  <Typography variant="body1">{selectedBatch.progress}%</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="textSecondary">Operator</Typography>
                  <Typography variant="body1">{selectedBatch.operator}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="textSecondary">Start Date</Typography>
                  <Typography variant="body1">
                    {selectedBatch.startDate ? new Date(selectedBatch.startDate).toLocaleString() : 'Not started'}
                  </Typography>
                </Grid>
                {selectedBatch.endDate && (
                  <Grid item xs={12} sm={6}>
                    <Typography variant="subtitle2" color="textSecondary">End Date</Typography>
                    <Typography variant="body1">
                      {new Date(selectedBatch.endDate).toLocaleString()}
                    </Typography>
                  </Grid>
                )}
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="textSecondary">Notes</Typography>
                  <Typography variant="body1">{selectedBatch.notes}</Typography>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseViewDialog}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Batches; 