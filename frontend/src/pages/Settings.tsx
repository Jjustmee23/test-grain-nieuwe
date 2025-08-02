import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  TextField,
  Switch,
  FormControlLabel,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Chip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Slider,
  Tabs,
  Tab
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  Storage as StorageIcon,
  NetworkCheck as NetworkIcon,
  Backup as BackupIcon,
  Restore as RestoreIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const Settings: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [openBackupDialog, setOpenBackupDialog] = useState(false);
  const [openRestoreDialog, setOpenRestoreDialog] = useState(false);
  const [settings, setSettings] = useState({
    general: {
      language: 'English',
      timezone: 'Asia/Baghdad',
      dateFormat: 'DD/MM/YYYY',
      timeFormat: '24h',
      autoRefresh: true,
      refreshInterval: 30,
      theme: 'light'
    },
    security: {
      sessionTimeout: 30,
      requirePasswordChange: false,
      passwordExpiryDays: 90,
      maxLoginAttempts: 5,
      lockoutDuration: 15,
      twoFactorAuth: false,
      ipWhitelist: '',
      auditLogging: true
    },
    notifications: {
      emailEnabled: true,
      smsEnabled: false,
      pushEnabled: true,
      powerAlerts: true,
      batchUpdates: true,
      systemAlerts: true,
      maintenanceAlerts: true,
      alertSound: true,
      alertVolume: 50
    },
    system: {
      dataRetentionDays: 365,
      autoBackup: true,
      backupFrequency: 'daily',
      backupTime: '02:00',
      maxBackupSize: 10,
      compressionEnabled: true,
      encryptionEnabled: true
    }
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleSave = () => {
    // Mock save functionality
    console.log('Saving settings:', settings);
    alert('Settings saved successfully!');
  };

  const handleBackup = () => {
    setOpenBackupDialog(false);
    // Mock backup functionality
    console.log('Creating backup...');
    alert('Backup created successfully!');
  };

  const handleRestore = () => {
    setOpenRestoreDialog(false);
    // Mock restore functionality
    console.log('Restoring from backup...');
    alert('System restored successfully!');
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          System Settings
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => window.location.reload()}
            sx={{ mr: 1 }}
          >
            Reset
          </Button>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSave}
          >
            Save Settings
          </Button>
        </Box>
      </Box>

      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="settings tabs">
            <Tab label="General" />
            <Tab label="Security" />
            <Tab label="Notifications" />
            <Tab label="System" />
          </Tabs>
        </Box>

        {/* General Settings */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Language</InputLabel>
                <Select
                  value={settings.general.language}
                  label="Language"
                  onChange={(e) => setSettings({
                    ...settings,
                    general: { ...settings.general, language: e.target.value }
                  })}
                >
                  <MenuItem value="English">English</MenuItem>
                  <MenuItem value="Arabic">Arabic</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Timezone</InputLabel>
                <Select
                  value={settings.general.timezone}
                  label="Timezone"
                  onChange={(e) => setSettings({
                    ...settings,
                    general: { ...settings.general, timezone: e.target.value }
                  })}
                >
                  <MenuItem value="Asia/Baghdad">Asia/Baghdad</MenuItem>
                  <MenuItem value="UTC">UTC</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Date Format</InputLabel>
                <Select
                  value={settings.general.dateFormat}
                  label="Date Format"
                  onChange={(e) => setSettings({
                    ...settings,
                    general: { ...settings.general, dateFormat: e.target.value }
                  })}
                >
                  <MenuItem value="DD/MM/YYYY">DD/MM/YYYY</MenuItem>
                  <MenuItem value="MM/DD/YYYY">MM/DD/YYYY</MenuItem>
                  <MenuItem value="YYYY-MM-DD">YYYY-MM-DD</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Time Format</InputLabel>
                <Select
                  value={settings.general.timeFormat}
                  label="Time Format"
                  onChange={(e) => setSettings({
                    ...settings,
                    general: { ...settings.general, timeFormat: e.target.value }
                  })}
                >
                  <MenuItem value="12h">12-hour</MenuItem>
                  <MenuItem value="24h">24-hour</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.general.autoRefresh}
                    onChange={(e) => setSettings({
                      ...settings,
                      general: { ...settings.general, autoRefresh: e.target.checked }
                    })}
                  />
                }
                label="Enable Auto Refresh"
              />
            </Grid>
            {settings.general.autoRefresh && (
              <Grid item xs={12} md={6}>
                <Typography gutterBottom>Refresh Interval (seconds)</Typography>
                <Slider
                  value={settings.general.refreshInterval}
                  onChange={(e, value) => setSettings({
                    ...settings,
                    general: { ...settings.general, refreshInterval: value as number }
                  })}
                  min={10}
                  max={300}
                  step={10}
                  marks
                  valueLabelDisplay="auto"
                />
              </Grid>
            )}
          </Grid>
        </TabPanel>

        {/* Security Settings */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography gutterBottom>Session Timeout (minutes)</Typography>
              <Slider
                value={settings.security.sessionTimeout}
                onChange={(e, value) => setSettings({
                  ...settings,
                  security: { ...settings.security, sessionTimeout: value as number }
                })}
                min={5}
                max={120}
                step={5}
                marks
                valueLabelDisplay="auto"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography gutterBottom>Password Expiry (days)</Typography>
              <Slider
                value={settings.security.passwordExpiryDays}
                onChange={(e, value) => setSettings({
                  ...settings,
                  security: { ...settings.security, passwordExpiryDays: value as number }
                })}
                min={30}
                max={365}
                step={30}
                marks
                valueLabelDisplay="auto"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Max Login Attempts"
                type="number"
                value={settings.security.maxLoginAttempts}
                onChange={(e) => setSettings({
                  ...settings,
                  security: { ...settings.security, maxLoginAttempts: parseInt(e.target.value) }
                })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Lockout Duration (minutes)"
                type="number"
                value={settings.security.lockoutDuration}
                onChange={(e) => setSettings({
                  ...settings,
                  security: { ...settings.security, lockoutDuration: parseInt(e.target.value) }
                })}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.security.requirePasswordChange}
                    onChange={(e) => setSettings({
                      ...settings,
                      security: { ...settings.security, requirePasswordChange: e.target.checked }
                    })}
                  />
                }
                label="Require Password Change on First Login"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.security.twoFactorAuth}
                    onChange={(e) => setSettings({
                      ...settings,
                      security: { ...settings.security, twoFactorAuth: e.target.checked }
                    })}
                  />
                }
                label="Enable Two-Factor Authentication"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.security.auditLogging}
                    onChange={(e) => setSettings({
                      ...settings,
                      security: { ...settings.security, auditLogging: e.target.checked }
                    })}
                  />
                }
                label="Enable Audit Logging"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="IP Whitelist (comma-separated)"
                value={settings.security.ipWhitelist}
                onChange={(e) => setSettings({
                  ...settings,
                  security: { ...settings.security, ipWhitelist: e.target.value }
                })}
                helperText="Leave empty to allow all IPs"
              />
            </Grid>
          </Grid>
        </TabPanel>

        {/* Notification Settings */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notifications.emailEnabled}
                    onChange={(e) => setSettings({
                      ...settings,
                      notifications: { ...settings.notifications, emailEnabled: e.target.checked }
                    })}
                  />
                }
                label="Email Notifications"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notifications.smsEnabled}
                    onChange={(e) => setSettings({
                      ...settings,
                      notifications: { ...settings.notifications, smsEnabled: e.target.checked }
                    })}
                  />
                }
                label="SMS Notifications"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notifications.pushEnabled}
                    onChange={(e) => setSettings({
                      ...settings,
                      notifications: { ...settings.notifications, pushEnabled: e.target.checked }
                    })}
                  />
                }
                label="Push Notifications"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notifications.alertSound}
                    onChange={(e) => setSettings({
                      ...settings,
                      notifications: { ...settings.notifications, alertSound: e.target.checked }
                    })}
                  />
                }
                label="Alert Sounds"
              />
            </Grid>
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Alert Types
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notifications.powerAlerts}
                    onChange={(e) => setSettings({
                      ...settings,
                      notifications: { ...settings.notifications, powerAlerts: e.target.checked }
                    })}
                  />
                }
                label="Power Alerts"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notifications.batchUpdates}
                    onChange={(e) => setSettings({
                      ...settings,
                      notifications: { ...settings.notifications, batchUpdates: e.target.checked }
                    })}
                  />
                }
                label="Batch Updates"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notifications.systemAlerts}
                    onChange={(e) => setSettings({
                      ...settings,
                      notifications: { ...settings.notifications, systemAlerts: e.target.checked }
                    })}
                  />
                }
                label="System Alerts"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notifications.maintenanceAlerts}
                    onChange={(e) => setSettings({
                      ...settings,
                      notifications: { ...settings.notifications, maintenanceAlerts: e.target.checked }
                    })}
                  />
                }
                label="Maintenance Alerts"
              />
            </Grid>
            {settings.notifications.alertSound && (
              <Grid item xs={12} md={6}>
                <Typography gutterBottom>Alert Volume</Typography>
                <Slider
                  value={settings.notifications.alertVolume}
                  onChange={(e, value) => setSettings({
                    ...settings,
                    notifications: { ...settings.notifications, alertVolume: value as number }
                  })}
                  min={0}
                  max={100}
                  step={10}
                  marks
                  valueLabelDisplay="auto"
                />
              </Grid>
            )}
          </Grid>
        </TabPanel>

        {/* System Settings */}
        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography gutterBottom>Data Retention (days)</Typography>
              <Slider
                value={settings.system.dataRetentionDays}
                onChange={(e, value) => setSettings({
                  ...settings,
                  system: { ...settings.system, dataRetentionDays: value as number }
                })}
                min={30}
                max={1095}
                step={30}
                marks
                valueLabelDisplay="auto"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography gutterBottom>Max Backup Size (GB)</Typography>
              <Slider
                value={settings.system.maxBackupSize}
                onChange={(e, value) => setSettings({
                  ...settings,
                  system: { ...settings.system, maxBackupSize: value as number }
                })}
                min={1}
                max={50}
                step={1}
                marks
                valueLabelDisplay="auto"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Backup Frequency</InputLabel>
                <Select
                  value={settings.system.backupFrequency}
                  label="Backup Frequency"
                  onChange={(e) => setSettings({
                    ...settings,
                    system: { ...settings.system, backupFrequency: e.target.value }
                  })}
                >
                  <MenuItem value="daily">Daily</MenuItem>
                  <MenuItem value="weekly">Weekly</MenuItem>
                  <MenuItem value="monthly">Monthly</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Backup Time"
                type="time"
                value={settings.system.backupTime}
                onChange={(e) => setSettings({
                  ...settings,
                  system: { ...settings.system, backupTime: e.target.value }
                })}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.system.autoBackup}
                    onChange={(e) => setSettings({
                      ...settings,
                      system: { ...settings.system, autoBackup: e.target.checked }
                    })}
                  />
                }
                label="Enable Automatic Backups"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.system.compressionEnabled}
                    onChange={(e) => setSettings({
                      ...settings,
                      system: { ...settings.system, compressionEnabled: e.target.checked }
                    })}
                  />
                }
                label="Enable Backup Compression"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.system.encryptionEnabled}
                    onChange={(e) => setSettings({
                      ...settings,
                      system: { ...settings.system, encryptionEnabled: e.target.checked }
                    })}
                  />
                }
                label="Enable Backup Encryption"
              />
            </Grid>
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                System Actions
              </Typography>
              <Box display="flex" gap={2}>
                <Button
                  variant="outlined"
                  startIcon={<BackupIcon />}
                  onClick={() => setOpenBackupDialog(true)}
                >
                  Create Backup
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<RestoreIcon />}
                  onClick={() => setOpenRestoreDialog(true)}
                >
                  Restore System
                </Button>
              </Box>
            </Grid>
          </Grid>
        </TabPanel>
      </Card>

      {/* Backup Dialog */}
      <Dialog open={openBackupDialog} onClose={() => setOpenBackupDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create System Backup</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            This will create a complete backup of all system data and settings.
          </Alert>
          <Typography variant="body2" color="textSecondary">
            Backup will include:
          </Typography>
          <List dense>
            <ListItem>
              <ListItemIcon>
                <CheckCircleIcon color="success" />
              </ListItemIcon>
              <ListItemText primary="All factory and device data" />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckCircleIcon color="success" />
              </ListItemIcon>
              <ListItemText primary="Production and batch records" />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckCircleIcon color="success" />
              </ListItemIcon>
              <ListItemText primary="User accounts and permissions" />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckCircleIcon color="success" />
              </ListItemIcon>
              <ListItemText primary="System settings and configurations" />
            </ListItem>
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenBackupDialog(false)}>Cancel</Button>
          <Button onClick={handleBackup} variant="contained">
            Create Backup
          </Button>
        </DialogActions>
      </Dialog>

      {/* Restore Dialog */}
      <Dialog open={openRestoreDialog} onClose={() => setOpenRestoreDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Restore System</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            Warning: This action will overwrite all current data with the backup data.
          </Alert>
          <Typography variant="body2" color="textSecondary" gutterBottom>
            Please select a backup file to restore from:
          </Typography>
          <TextField
            fullWidth
            type="file"
            inputProps={{ accept: '.backup' }}
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenRestoreDialog(false)}>Cancel</Button>
          <Button onClick={handleRestore} variant="contained" color="warning">
            Restore System
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Settings; 