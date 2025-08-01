import { Router } from 'express';
import { prisma } from '../config/database';
import { logger } from '../config/logger';

const router = Router();

// Test endpoint to check if backend is working
router.get('/test', (req, res) => {
  return res.json({
    success: true,
    message: 'Devices endpoint is working',
    timestamp: new Date().toISOString()
  });
});

// Get all devices
router.get('/', async (req, res) => {
  try {
    logger.info('Fetching devices from database...');
    
    const devices = await prisma.device.findMany({
      include: {
        factory: {
          select: {
            id: true,
            name: true
          }
        }
      },
      orderBy: {
        name: 'asc'
      }
    });
    
    logger.info(`Retrieved ${devices.length} devices from database`);
    
    return res.json({
      success: true,
      data: devices,
      count: devices.length
    });
  } catch (error) {
    logger.error('Error in GET /devices:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to fetch devices',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Get device by ID
router.get('/:id', async (req, res) => {
  try {
    const deviceId = req.params.id;
    
    const device = await prisma.device.findUnique({
      where: { id: deviceId },
      include: {
        factory: {
          select: {
            id: true,
            name: true
          }
        }
      }
    });
    
    if (!device) {
      return res.status(404).json({
        success: false,
        error: 'Device not found'
      });
    }

    return res.json({
      success: true,
      data: device
    });
  } catch (error) {
    logger.error(`Error in GET /devices/${req.params.id}:`, error);
    return res.status(500).json({
      success: false,
      error: 'Failed to fetch device',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Get devices by factory ID
router.get('/factory/:factoryId', async (req, res) => {
  try {
    const factoryId = parseInt(req.params.factoryId);
    if (isNaN(factoryId)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid factory ID'
      });
    }
    
    const devices = await prisma.device.findMany({
      where: { factoryId },
      include: {
        factory: {
          select: {
            id: true,
            name: true
          }
        }
      },
      orderBy: {
        name: 'asc'
      }
    });
    
    return res.json({
      success: true,
      data: devices,
      count: devices.length
    });
  } catch (error) {
    logger.error(`Error in GET /devices/factory/${req.params.factoryId}:`, error);
    return res.status(500).json({
      success: false,
      error: 'Failed to fetch devices by factory',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Get devices stats overview
router.get('/stats/overview', async (req, res) => {
  try {
    const totalDevices = await prisma.device.count();
    const onlineDevices = await prisma.device.count({
      where: { status: true }
    });

    const stats = {
      total: totalDevices,
      online: onlineDevices,
      offline: totalDevices - onlineDevices
    };
    
    return res.json({
      success: true,
      data: stats
    });
  } catch (error) {
    logger.error('Error in GET /devices/stats/overview:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to fetch device stats',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

export default router; 