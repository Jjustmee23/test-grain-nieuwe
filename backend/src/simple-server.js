const express = require('express');
const cors = require('cors');

const app = express();

// Middleware
app.use(cors({
  origin: "http://localhost:3000",
  credentials: true
}));
app.use(express.json());

// Logging middleware
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
  next();
});

// Test routes that match the frontend expectations
app.get('/api/factories/stats/public', (req, res) => {
  console.log('✅ GET /api/factories/stats/public');
  res.json({
    success: true,
    data: [
      {
        id: 1,
        name: 'Mill Factory Babylon',
        cityId: 1,
        city: { id: 1, name: 'Babylon' },
        group: 'government',
        status: true,
        error: false,
        address: 'Industrial District, Babylon',
        stats: {
          daily: 2500,
          weekly: 17500,
          monthly: 75000,
          yearly: 912500,
          deviceCount: 3,
          onlineDevices: 2,
          powerStatus: 'on',
          doorStatus: 'closed',
          startTime: '06:00',
          stopTime: '18:00'
        },
        devices: [
          { id: 'BAB001', name: 'Main Production Unit', status: true },
          { id: 'BAB002', name: 'Secondary Mill', status: true },
          { id: 'BAB003', name: 'Backup Unit', status: false }
        ]
      },
      {
        id: 2,
        name: 'Nineveh Grain Processing',
        cityId: 2,
        city: { id: 2, name: 'Nineveh' },
        group: 'private',
        status: true,
        error: false,
        address: 'Agricultural Zone, Nineveh',
        stats: {
          daily: 3200,
          weekly: 22400,
          monthly: 96000,
          yearly: 1168000,
          deviceCount: 4,
          onlineDevices: 3,
          powerStatus: 'on',
          doorStatus: 'closed',
          startTime: '05:30',
          stopTime: '19:00'
        },
        devices: [
          { id: 'NIN001', name: 'Primary Processor', status: true },
          { id: 'NIN002', name: 'Quality Control Unit', status: true },
          { id: 'NIN003', name: 'Packaging System', status: true },
          { id: 'NIN004', name: 'Storage Monitor', status: false }
        ]
      },
      {
        id: 3,
        name: 'Diyala Commercial Mill',
        cityId: 3,
        city: { id: 3, name: 'Diyala' },
        group: 'commercial',
        status: true,
        error: false,
        address: 'Trade Center, Diyala',
        stats: {
          daily: 1800,
          weekly: 12600,
          monthly: 54000,
          yearly: 657000,
          deviceCount: 2,
          onlineDevices: 2,
          powerStatus: 'on',
          doorStatus: 'open',
          startTime: '07:00',
          stopTime: '17:00'
        },
        devices: [
          { id: 'DIY001', name: 'Commercial Processor', status: true },
          { id: 'DIY002', name: 'Export Quality Control', status: true }
        ]
      }
    ],
    count: 3
  });
});

app.get('/api/cities/public', (req, res) => {
  console.log('✅ GET /api/cities/public');
  res.json({
    success: true,
    data: [
      {
        id: 1,
        name: 'Babylon',
        status: true,
        createdAt: new Date().toISOString(),
        _count: { factories: 1 }
      },
      {
        id: 2,
        name: 'Nineveh',
        status: true,
        createdAt: new Date().toISOString(),
        _count: { factories: 1 }
      },
      {
        id: 3,
        name: 'Diyala',
        status: true,
        createdAt: new Date().toISOString(),
        _count: { factories: 1 }
      }
    ],
    total: 3
  });
});

app.get('/api/factories/test', (req, res) => {
  console.log('✅ GET /api/factories/test');
  res.json({
    success: true,
    message: 'Mill Management API is working perfectly!',
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});

app.get('/health', (req, res) => {
  console.log('✅ GET /health');
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: 'development',
    database: 'connected',
    service: 'mill-management-api'
  });
});

// Handle all other routes
app.use('*', (req, res) => {
  console.log(`❌ 404: ${req.method} ${req.originalUrl}`);
  res.status(404).json({
    error: 'Not found',
    message: `Route ${req.originalUrl} not found`,
    availableEndpoints: [
      'GET /health',
      'GET /api/factories/test',
      'GET /api/factories/stats/public',
      'GET /api/cities/public'
    ]
  });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`🎉 Mill Management API Test Server`);
  console.log(`🚀 Server running on http://localhost:${PORT}`);
  console.log(`📱 Health check: http://localhost:${PORT}/health`);
  console.log(`🏭 Factories API: http://localhost:${PORT}/api/factories/stats/public`);
  console.log(`🏙️  Cities API: http://localhost:${PORT}/api/cities/public`);
  console.log(`⚡ Ready to serve Iraqi grain mill data!`);
});