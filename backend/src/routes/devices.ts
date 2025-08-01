import { Router } from 'express';
import { prisma } from '../config/database';
import { logger } from '../config/logger';
import { authenticateToken } from '../middleware/auth';

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

// Get new devices (unconfigured)
router.get('/new', async (req, res) => {
  try {
    logger.info('Fetching new devices from database...');
    
    const newDevices = await prisma.device.findMany({
      where: {
        isConfigured: false
      },
      orderBy: {
        createdAt: 'desc'
      }
    });
    
    logger.info(`Retrieved ${newDevices.length} new devices from database`);
    
    return res.json({
      success: true,
      data: newDevices,
      count: newDevices.length
    });
  } catch (error) {
    logger.error('Error in GET /devices/new:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to fetch new devices',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Get configured devices only
router.get('/configured', async (req, res) => {
  try {
    logger.info('Fetching configured devices from database...');
    
    const configuredDevices = await prisma.device.findMany({
      where: {
        isConfigured: true
      },
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
    
    logger.info(`Retrieved ${configuredDevices.length} configured devices from database`);
    
    return res.json({
      success: true,
      data: configuredDevices,
      count: configuredDevices.length
    });
  } catch (error) {
    logger.error('Error in GET /devices/configured:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to fetch configured devices',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Create new device
router.post('/', authenticateToken, async (req, res) => {
  try {
    const { id, name, factoryId, serialNumber, selectedCounter } = req.body;

    // Validation
    if (!id || typeof id !== 'string' || id.trim().length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Device ID is required'
      });
    }

    if (!name || typeof name !== 'string' || name.trim().length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Device name is required'
      });
    }

    if (!factoryId || isNaN(parseInt(factoryId))) {
      return res.status(400).json({
        success: false,
        error: 'Valid factory ID is required'
      });
    }

    if (!selectedCounter || !['counter_1', 'counter_2', 'counter_3', 'counter_4'].includes(selectedCounter)) {
      return res.status(400).json({
        success: false,
        error: 'Valid counter selection is required (counter_1, counter_2, counter_3, or counter_4)'
      });
    }

    // Check if factory exists
    const factory = await prisma.factory.findUnique({
      where: { id: parseInt(factoryId) }
    });

    if (!factory) {
      return res.status(400).json({
        success: false,
        error: 'Factory not found'
      });
    }

    // Check if device ID already exists
    const existingDevice = await prisma.device.findUnique({
      where: { id: id.trim() }
    });

    if (existingDevice) {
      return res.status(409).json({
        success: false,
        error: 'Device with this ID already exists'
      });
    }

    // Create device
    const device = await prisma.device.create({
      data: {
        id: id.trim(),
        name: name.trim(),
        factoryId: parseInt(factoryId),
        serialNumber: serialNumber?.trim(),
        selectedCounter,
        status: false, // Default to offline
        isConfigured: true // Mark as configured
      },
      include: {
        factory: {
          select: {
            id: true,
            name: true
          }
        }
      }
    });

    logger.info(`Created new device: ${device.name} in factory ${device.factory?.name}`);

    return res.status(201).json({
      success: true,
      message: 'Device created successfully',
      data: device
    });
  } catch (error) {
    logger.error('Error in POST /devices:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to create device',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Configure existing device (add name and factory)
router.put('/:id/configure', authenticateToken, async (req, res) => {
  try {
    const deviceId = req.params.id;
    const { name, factoryId, serialNumber, selectedCounter } = req.body;

    // Validation
    if (!name || typeof name !== 'string' || name.trim().length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Device name is required'
      });
    }

    if (!factoryId || isNaN(parseInt(factoryId))) {
      return res.status(400).json({
        success: false,
        error: 'Valid factory ID is required'
      });
    }

    if (!selectedCounter || !['counter_1', 'counter_2', 'counter_3', 'counter_4'].includes(selectedCounter)) {
      return res.status(400).json({
        success: false,
        error: 'Valid counter selection is required (counter_1, counter_2, counter_3, or counter_4)'
      });
    }

    // Check if device exists
    const existingDevice = await prisma.device.findUnique({
      where: { id: deviceId }
    });

    if (!existingDevice) {
      return res.status(404).json({
        success: false,
        error: 'Device not found'
      });
    }

    // Check if factory exists
    const factory = await prisma.factory.findUnique({
      where: { id: parseInt(factoryId) }
    });

    if (!factory) {
      return res.status(400).json({
        success: false,
        error: 'Factory not found'
      });
    }

    // Update device
    const device = await prisma.device.update({
      where: { id: deviceId },
      data: {
        name: name.trim(),
        factoryId: parseInt(factoryId),
        serialNumber: serialNumber?.trim() || existingDevice.serialNumber,
        selectedCounter,
        isConfigured: true
      },
      include: {
        factory: {
          select: {
            id: true,
            name: true
          }
        }
      }
    });

    logger.info(`Configured device: ${device.id} -> ${device.name} in factory ${device.factory?.name}`);

    return res.json({
      success: true,
      message: 'Device configured successfully',
      data: device
    });
  } catch (error) {
    logger.error(`Error in PUT /devices/${req.params.id}/configure:`, error);
    return res.status(500).json({
      success: false,
      error: 'Failed to configure device',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Register new device from MQTT (no authentication required for MQTT)
router.post('/register', async (req, res) => {
  try {
    const { serialNumber, status = false } = req.body;

    // Validation
    if (!serialNumber || typeof serialNumber !== 'string' || serialNumber.trim().length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Serial number is required'
      });
    }

    // Check if device already exists
    const existingDevice = await prisma.device.findUnique({
      where: { id: serialNumber.trim() }
    });

    if (existingDevice) {
      // Update status if device exists
      await prisma.device.update({
        where: { id: serialNumber.trim() },
        data: { status }
      });

      return res.json({
        success: true,
        message: 'Device status updated',
        data: existingDevice
      });
    }

    // Create new device
    const device = await prisma.device.create({
      data: {
        id: serialNumber.trim(),
        serialNumber: serialNumber.trim(),
        status,
        isConfigured: false // Mark as unconfigured
      }
    });

    logger.info(`Registered new device from MQTT: ${device.id}`);

    return res.status(201).json({
      success: true,
      message: 'Device registered successfully',
      data: device
    });
  } catch (error) {
    logger.error('Error in POST /devices/register:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to register device',
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

// Delete device
router.delete('/:id', authenticateToken, async (req, res) => {
  try {
    const deviceId = req.params.id;
    
    // Check if device exists
    const device = await prisma.device.findUnique({
      where: { id: deviceId }
    });

    if (!device) {
      return res.status(404).json({
        success: false,
        error: 'Device not found'
      });
    }

    // Delete device
    await prisma.device.delete({
      where: { id: deviceId }
    });

    logger.info(`Deleted device: ${deviceId}`);

    return res.json({
      success: true,
      message: 'Device deleted successfully'
    });
  } catch (error) {
    logger.error(`Error in DELETE /devices/${req.params.id}:`, error);
    return res.status(500).json({
      success: false,
      error: 'Failed to delete device',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

export default router; 