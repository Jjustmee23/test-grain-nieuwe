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
  Divider,
  TextareaAutosize
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Support as SupportIcon,
  PriorityHigh as PriorityHighIcon,
  SignalCellular2Bar as PriorityMediumIcon,
  SignalCellular0Bar as PriorityLowIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Pending as PendingIcon,
  Visibility as ViewIcon,
  Comment as CommentIcon,
  Email as EmailIcon,
  Phone as PhoneIcon
} from '@mui/icons-material';

interface SupportTicket {
  id: number;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'new' | 'in_progress' | 'resolved' | 'closed';
  category: string;
  factoryId: number;
  factoryName: string;
  submittedBy: string;
  assignedTo?: string;
  createdAt: string;
  updatedAt: string;
  comments: Comment[];
}

interface Comment {
  id: number;
  ticketId: number;
  author: string;
  content: string;
  timestamp: string;
  isInternal: boolean;
}

const Support: React.FC = () => {
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [viewDialog, setViewDialog] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState<SupportTicket | null>(null);
  const [editingTicket, setEditingTicket] = useState<SupportTicket | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    category: '',
    factoryId: '',
    assignedTo: ''
  });

  // Mock data - replace with API calls
  useEffect(() => {
    const mockTickets: SupportTicket[] = [
      {
        id: 1,
        title: 'Device connectivity issue',
        description: 'Device-002 has been offline for the past 2 hours. Need immediate assistance to restore connectivity.',
        priority: 'high',
        status: 'in_progress',
        category: 'Technical',
        factoryId: 1,
        factoryName: 'Baghdad Central Mill',
        submittedBy: 'Ahmed Hassan',
        assignedTo: 'Technical Team',
        createdAt: '2024-01-15T10:30:00',
        updatedAt: '2024-01-15T14:20:00',
        comments: [
          {
            id: 1,
            ticketId: 1,
            author: 'Technical Team',
            content: 'Investigating the connectivity issue. Checking network configuration.',
            timestamp: '2024-01-15T11:00:00',
            isInternal: true
          },
          {
            id: 2,
            ticketId: 1,
            author: 'Ahmed Hassan',
            content: 'Thank you for the update. Please let me know when it\'s resolved.',
            timestamp: '2024-01-15T11:15:00',
            isInternal: false
          }
        ]
      },
      {
        id: 2,
        title: 'Power fluctuation detected',
        description: 'Unusual power fluctuations detected in Device-001. Voltage readings are inconsistent.',
        priority: 'urgent',
        status: 'new',
        category: 'Power',
        factoryId: 1,
        factoryName: 'Baghdad Central Mill',
        submittedBy: 'Mohammed Ali',
        createdAt: '2024-01-15T15:45:00',
        updatedAt: '2024-01-15T15:45:00',
        comments: []
      },
      {
        id: 3,
        title: 'Batch processing error',
        description: 'Batch-2024-003 failed to start. Error message indicates insufficient wheat quantity.',
        priority: 'medium',
        status: 'resolved',
        category: 'Production',
        factoryId: 2,
        factoryName: 'Basra Grain Factory',
        submittedBy: 'Fatima Zahra',
        assignedTo: 'Production Team',
        createdAt: '2024-01-14T09:20:00',
        updatedAt: '2024-01-14T16:30:00',
        comments: [
          {
            id: 3,
            ticketId: 3,
            author: 'Production Team',
            content: 'Issue resolved. Wheat quantity was incorrectly entered. Batch has been restarted.',
            timestamp: '2024-01-14T16:30:00',
            isInternal: false
          }
        ]
      }
    ];

    setTimeout(() => {
      setTickets(mockTickets);
      setLoading(false);
    }, 1000);
  }, []);

  const handleOpenDialog = (ticket?: SupportTicket) => {
    if (ticket) {
      setEditingTicket(ticket);
      setFormData({
        title: ticket.title,
        description: ticket.description,
        priority: ticket.priority,
        category: ticket.category,
        factoryId: ticket.factoryId.toString(),
        assignedTo: ticket.assignedTo || ''
      });
    } else {
      setEditingTicket(null);
      setFormData({
        title: '',
        description: '',
        priority: 'medium',
        category: '',
        factoryId: '',
        assignedTo: ''
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingTicket(null);
  };

  const handleViewTicket = (ticket: SupportTicket) => {
    setSelectedTicket(ticket);
    setViewDialog(true);
  };

  const handleCloseViewDialog = () => {
    setViewDialog(false);
    setSelectedTicket(null);
  };

  const handleSubmit = () => {
    if (editingTicket) {
      setTickets(prev => prev.map(t => 
        t.id === editingTicket.id 
          ? { 
              ...t, 
              title: formData.title,
              description: formData.description,
              priority: formData.priority as 'low' | 'medium' | 'high' | 'urgent',
              category: formData.category,
              factoryId: parseInt(formData.factoryId),
              assignedTo: formData.assignedTo || undefined,
              updatedAt: new Date().toISOString()
            }
          : t
      ));
    } else {
      const newTicket: SupportTicket = {
        id: Math.max(...tickets.map(t => t.id)) + 1,
        title: formData.title,
        description: formData.description,
        priority: formData.priority as 'low' | 'medium' | 'high' | 'urgent',
        status: 'new',
        category: formData.category,
        factoryId: parseInt(formData.factoryId),
        factoryName: 'New Factory', // This would come from API
        submittedBy: 'Current User', // This would come from auth
        assignedTo: formData.assignedTo || undefined,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        comments: []
      };
      setTickets(prev => [...prev, newTicket]);
    }
    handleCloseDialog();
  };

  const handleDelete = (id: number) => {
    setTickets(prev => prev.filter(t => t.id !== id));
  };

  const handleStatusChange = (id: number, newStatus: SupportTicket['status']) => {
    setTickets(prev => prev.map(t => 
      t.id === id 
        ? { ...t, status: newStatus, updatedAt: new Date().toISOString() }
        : t
    ));
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'urgent': return <PriorityHighIcon />;
      case 'high': return <PriorityHighIcon />;
      case 'medium': return <PriorityMediumIcon />;
      case 'low': return <PriorityLowIcon />;
      default: return <PriorityMediumIcon />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'new': return 'info';
      case 'in_progress': return 'warning';
      case 'resolved': return 'success';
      case 'closed': return 'default';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'new': return <PendingIcon />;
      case 'in_progress': return <PendingIcon />;
      case 'resolved': return <CheckCircleIcon />;
      case 'closed': return <CancelIcon />;
      default: return <PendingIcon />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
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
          Support Ticket Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Create Ticket
        </Button>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Tickets
              </Typography>
              <Typography variant="h4">
                {tickets.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Open Tickets
              </Typography>
              <Typography variant="h4" color="warning.main">
                {tickets.filter(t => t.status === 'new' || t.status === 'in_progress').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Urgent Tickets
              </Typography>
              <Typography variant="h4" color="error.main">
                {tickets.filter(t => t.priority === 'urgent').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Resolved Today
              </Typography>
              <Typography variant="h4" color="success.main">
                {tickets.filter(t => t.status === 'resolved' && new Date(t.updatedAt).toDateString() === new Date().toDateString()).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tickets Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Ticket</TableCell>
                <TableCell>Category</TableCell>
                <TableCell>Priority</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Factory</TableCell>
                <TableCell>Submitted By</TableCell>
                <TableCell>Assigned To</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {tickets
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((ticket) => (
                  <TableRow key={ticket.id}>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight="bold">
                          #{ticket.id} - {ticket.title}
                        </Typography>
                        <Typography variant="caption" color="textSecondary" noWrap>
                          {ticket.description.substring(0, 50)}...
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip label={ticket.category} size="small" />
                    </TableCell>
                    <TableCell>
                      <Chip
                        icon={getPriorityIcon(ticket.priority)}
                        label={ticket.priority}
                        color={getPriorityColor(ticket.priority) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        icon={getStatusIcon(ticket.status)}
                        label={ticket.status.replace('_', ' ')}
                        color={getStatusColor(ticket.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{ticket.factoryName}</TableCell>
                    <TableCell>{ticket.submittedBy}</TableCell>
                    <TableCell>{ticket.assignedTo || 'Unassigned'}</TableCell>
                    <TableCell>{formatTimestamp(ticket.createdAt)}</TableCell>
                    <TableCell>
                      <Tooltip title="View Details">
                        <IconButton
                          size="small"
                          onClick={() => handleViewTicket(ticket)}
                          color="primary"
                        >
                          <ViewIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit Ticket">
                        <IconButton
                          size="small"
                          onClick={() => handleOpenDialog(ticket)}
                          color="primary"
                        >
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete Ticket">
                        <IconButton
                          size="small"
                          onClick={() => handleDelete(ticket.id)}
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
          count={tickets.length}
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
          {editingTicket ? 'Edit Support Ticket' : 'Create New Support Ticket'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Title"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                multiline
                rows={4}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Priority</InputLabel>
                <Select
                  value={formData.priority}
                  label="Priority"
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                >
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="urgent">Urgent</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  value={formData.category}
                  label="Category"
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                >
                  <MenuItem value="Technical">Technical</MenuItem>
                  <MenuItem value="Power">Power</MenuItem>
                  <MenuItem value="Production">Production</MenuItem>
                  <MenuItem value="General">General</MenuItem>
                </Select>
              </FormControl>
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
              <TextField
                fullWidth
                label="Assign To"
                value={formData.assignedTo}
                onChange={(e) => setFormData({ ...formData, assignedTo: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingTicket ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Ticket Details Dialog */}
      <Dialog open={viewDialog} onClose={handleCloseViewDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          Support Ticket #{selectedTicket?.id} - {selectedTicket?.title}
        </DialogTitle>
        <DialogContent>
          {selectedTicket && (
            <Box>
              <Grid container spacing={2} mb={3}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="textSecondary">Priority</Typography>
                  <Chip
                    icon={getPriorityIcon(selectedTicket.priority)}
                    label={selectedTicket.priority}
                    color={getPriorityColor(selectedTicket.priority) as any}
                    size="small"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="textSecondary">Status</Typography>
                  <Chip
                    icon={getStatusIcon(selectedTicket.status)}
                    label={selectedTicket.status.replace('_', ' ')}
                    color={getStatusColor(selectedTicket.status) as any}
                    size="small"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="textSecondary">Category</Typography>
                  <Typography variant="body1">{selectedTicket.category}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="textSecondary">Factory</Typography>
                  <Typography variant="body1">{selectedTicket.factoryName}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="textSecondary">Submitted By</Typography>
                  <Typography variant="body1">{selectedTicket.submittedBy}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="textSecondary">Assigned To</Typography>
                  <Typography variant="body1">{selectedTicket.assignedTo || 'Unassigned'}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="textSecondary">Description</Typography>
                  <Typography variant="body1">{selectedTicket.description}</Typography>
                </Grid>
              </Grid>

              <Divider sx={{ my: 2 }} />

              <Typography variant="h6" gutterBottom>
                Comments ({selectedTicket.comments.length})
              </Typography>
              <List>
                {selectedTicket.comments.map((comment) => (
                  <ListItem key={comment.id}>
                    <ListItemIcon>
                      <CommentIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Typography variant="body2" fontWeight="bold">
                            {comment.author}
                          </Typography>
                          <Chip
                            label={comment.isInternal ? 'Internal' : 'Public'}
                            size="small"
                            color={comment.isInternal ? 'secondary' : 'primary'}
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" sx={{ mt: 1 }}>
                            {comment.content}
                          </Typography>
                          <Typography variant="caption" color="textSecondary">
                            {formatTimestamp(comment.timestamp)}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
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

export default Support; 