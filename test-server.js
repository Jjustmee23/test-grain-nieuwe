const express = require('express');
const cors = require('cors');
const app = express();

// Middleware
app.use(cors({
  origin: "http://localhost:3000",
  credentials: true
}));
app.use(express.json());

// Test routes that match the frontend expectations
app.get('/api/factories/stats/public', (req, res) => {
  console.log('GET /api/factories/stats/public');
  res.json({
    success: true,
    data: [
      {
        id: 1,
        name: 'Test Factory 1',
        cityId: 1,
        city: { id: 1, name: 'Test City' },
        group: 'government',
        status: true,
        error: false,
        address: 'Test Address 1',
        stats: {
          daily: 1000,
          weekly: 7000,
          monthly: 30000,
          yearly: 365000,
          deviceCount: 2,
          onlineDevices: 1,
          powerStatus: 'on',
          doorStatus: 'closed',
          startTime: '08:00',
          stopTime: '18:00'
        },
        devices: [
          { id: 'device1', name: 'Device 1', status: true },
          { id: 'device2', name: 'Device 2', status: false }
        ]
      },
      {
        id: 2,
        name: 'Test Factory 2',
        cityId: 2,
        city: { id: 2, name: 'Test City 2' },
        group: 'private',
        status: true,
        error: false,
        address: 'Test Address 2',
        stats: {
          daily: 1500,
          weekly: 10500,
          monthly: 45000,
          yearly: 547500,
          deviceCount: 3,
          onlineDevices: 2,
          powerStatus: 'on',
          doorStatus: 'closed',
          startTime: '07:00',
          stopTime: '19:00'
        },
        devices: [
          { id: 'device3', name: 'Device 3', status: true },
          { id: 'device4', name: 'Device 4', status: true },
          { id: 'device5', name: 'Device 5', status: false }
        ]
      }
    ],
    count: 2
  });
});

app.get('/api/cities/public', (req, res) => {
  console.log('GET /api/cities/public');
  res.json({
    success: true,
    data: [
      {
        id: 1,
        name: 'Test City 1',
        status: true,
        createdAt: new Date().toISOString(),
        _count: { factories: 1 }
      },
      {
        id: 2,
        name: 'Test City 2',
        status: true,
        createdAt: new Date().toISOString(),
        _count: { factories: 1 }
      }
    ],
    total: 2
  });
});

app.get('/api/factories/test', (req, res) => {
  console.log('GET /api/factories/test');
  res.json({
    success: true,
    message: 'Test endpoint is working!',
    timestamp: new Date().toISOString()
  });
});

app.get('/health', (req, res) => {
  console.log('GET /health');
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: 'development',
    database: 'simulated'
  });
});

// Handle all other routes
app.use('*', (req, res) => {
  console.log(`404: ${req.method} ${req.originalUrl}`);
  res.status(404).json({
    error: 'Not found',
    message: `Route ${req.originalUrl} not found`
  });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`🚀 Test server running on port ${PORT}`);
  console.log(`📱 Health check: http://localhost:${PORT}/health`);
  console.log(`🏭 Factories API: http://localhost:${PORT}/api/factories/stats/public`);
  console.log(`🏙️  Cities API: http://localhost:${PORT}/api/cities/public`);
});