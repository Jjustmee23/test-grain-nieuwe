import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  TextField,
  Avatar,
  Divider,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  Person as PersonIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  LocationOn as LocationIcon,
  Business as BusinessIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { RootState } from '../store';

const Profile: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const [editing, setEditing] = useState(false);
  const [openPasswordDialog, setOpenPasswordDialog] = useState(false);
  const [profileData, setProfileData] = useState({
    name: user?.name || 'John Doe',
    email: user?.email || 'john.doe@example.com',
    phone: '+964 123 456 789',
    location: 'Baghdad, Iraq',
    department: 'Operations',
    role: 'Factory Manager',
    language: 'English',
    timezone: 'Asia/Baghdad',
    notifications: {
      email: true,
      sms: false,
      push: true,
      powerAlerts: true,
      batchUpdates: true,
      systemAlerts: true
    }
  });

  const handleSave = () => {
    // Mock save functionality
    console.log('Saving profile data:', profileData);
    setEditing(false);
  };

  const handleCancel = () => {
    setEditing(false);
  };

  const handlePasswordChange = () => {
    setOpenPasswordDialog(false);
    // Mock password change functionality
    console.log('Password changed');
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          User Profile
        </Typography>
        {!editing ? (
          <Button
            variant="contained"
            startIcon={<EditIcon />}
            onClick={() => setEditing(true)}
          >
            Edit Profile
          </Button>
        ) : (
          <Box>
            <Button
              variant="outlined"
              startIcon={<CancelIcon />}
              onClick={handleCancel}
              sx={{ mr: 1 }}
            >
              Cancel
            </Button>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSave}
            >
              Save Changes
            </Button>
          </Box>
        )}
      </Box>

      <Grid container spacing={3}>
        {/* Profile Information */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Personal Information
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Full Name"
                    value={profileData.name}
                    onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
                    disabled={!editing}
                    InputProps={{
                      startAdornment: <PersonIcon sx={{ mr: 1, color: 'text.secondary' }} />
                    }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Email"
                    type="email"
                    value={profileData.email}
                    onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                    disabled={!editing}
                    InputProps={{
                      startAdornment: <EmailIcon sx={{ mr: 1, color: 'text.secondary' }} />
                    }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Phone"
                    value={profileData.phone}
                    onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
                    disabled={!editing}
                    InputProps={{
                      startAdornment: <PhoneIcon sx={{ mr: 1, color: 'text.secondary' }} />
                    }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Location"
                    value={profileData.location}
                    onChange={(e) => setProfileData({ ...profileData, location: e.target.value })}
                    disabled={!editing}
                    InputProps={{
                      startAdornment: <LocationIcon sx={{ mr: 1, color: 'text.secondary' }} />
                    }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Department"
                    value={profileData.department}
                    onChange={(e) => setProfileData({ ...profileData, department: e.target.value })}
                    disabled={!editing}
                    InputProps={{
                      startAdornment: <BusinessIcon sx={{ mr: 1, color: 'text.secondary' }} />
                    }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Role"
                    value={profileData.role}
                    onChange={(e) => setProfileData({ ...profileData, role: e.target.value })}
                    disabled={!editing}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Preferences */}
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Preferences
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Language</InputLabel>
                    <Select
                      value={profileData.language}
                      label="Language"
                      onChange={(e) => setProfileData({ ...profileData, language: e.target.value })}
                      disabled={!editing}
                    >
                      <MenuItem value="English">English</MenuItem>
                      <MenuItem value="Arabic">Arabic</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Timezone</InputLabel>
                    <Select
                      value={profileData.timezone}
                      label="Timezone"
                      onChange={(e) => setProfileData({ ...profileData, timezone: e.target.value })}
                      disabled={!editing}
                    >
                      <MenuItem value="Asia/Baghdad">Asia/Baghdad</MenuItem>
                      <MenuItem value="UTC">UTC</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          {/* Profile Avatar */}
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Avatar
                sx={{ width: 120, height: 120, mx: 'auto', mb: 2 }}
              >
                {profileData.name.charAt(0)}
              </Avatar>
              <Typography variant="h6" gutterBottom>
                {profileData.name}
              </Typography>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                {profileData.role}
              </Typography>
              <Chip label={profileData.department} size="small" sx={{ mb: 2 }} />
              <Typography variant="body2" color="textSecondary">
                Member since {new Date().getFullYear()}
              </Typography>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <List>
                <ListItem button onClick={() => setOpenPasswordDialog(true)}>
                  <ListItemIcon>
                    <SecurityIcon />
                  </ListItemIcon>
                  <ListItemText primary="Change Password" />
                </ListItem>
                <ListItem button>
                  <ListItemIcon>
                    <NotificationsIcon />
                  </ListItemIcon>
                  <ListItemText primary="Notification Settings" />
                </ListItem>
              </List>
            </CardContent>
          </Card>

          {/* Notification Preferences */}
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Notification Preferences
              </Typography>
              <List>
                <ListItem>
                  <ListItemText primary="Email Notifications" />
                  <Switch
                    checked={profileData.notifications.email}
                    onChange={(e) => setProfileData({
                      ...profileData,
                      notifications: {
                        ...profileData.notifications,
                        email: e.target.checked
                      }
                    })}
                    disabled={!editing}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText primary="SMS Notifications" />
                  <Switch
                    checked={profileData.notifications.sms}
                    onChange={(e) => setProfileData({
                      ...profileData,
                      notifications: {
                        ...profileData.notifications,
                        sms: e.target.checked
                      }
                    })}
                    disabled={!editing}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Push Notifications" />
                  <Switch
                    checked={profileData.notifications.push}
                    onChange={(e) => setProfileData({
                      ...profileData,
                      notifications: {
                        ...profileData.notifications,
                        push: e.target.checked
                      }
                    })}
                    disabled={!editing}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Power Alerts" />
                  <Switch
                    checked={profileData.notifications.powerAlerts}
                    onChange={(e) => setProfileData({
                      ...profileData,
                      notifications: {
                        ...profileData.notifications,
                        powerAlerts: e.target.checked
                      }
                    })}
                    disabled={!editing}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Batch Updates" />
                  <Switch
                    checked={profileData.notifications.batchUpdates}
                    onChange={(e) => setProfileData({
                      ...profileData,
                      notifications: {
                        ...profileData.notifications,
                        batchUpdates: e.target.checked
                      }
                    })}
                    disabled={!editing}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText primary="System Alerts" />
                  <Switch
                    checked={profileData.notifications.systemAlerts}
                    onChange={(e) => setProfileData({
                      ...profileData,
                      notifications: {
                        ...profileData.notifications,
                        systemAlerts: e.target.checked
                      }
                    })}
                    disabled={!editing}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Change Password Dialog */}
      <Dialog open={openPasswordDialog} onClose={() => setOpenPasswordDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Change Password</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Current Password"
                type="password"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="New Password"
                type="password"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Confirm New Password"
                type="password"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenPasswordDialog(false)}>Cancel</Button>
          <Button onClick={handlePasswordChange} variant="contained">
            Change Password
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Profile; 