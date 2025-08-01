import { Router } from 'express';
import { prisma, counterPrisma } from '../config/database';
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

    // Enrich with real-time data from counter database
    const enrichedDevices = await Promise.all(
      devices.map(async (device) => {
        try {
          const powerStatus = await counterPrisma.devicePowerStatus.findFirst({
            where: { deviceId: device.id },
            orderBy: { lastPowerCheck: 'desc' }
          });

          const doorStatus = await counterPrisma.doorStatus.findFirst({
            where: { deviceId: device.id },
            orderBy: { lastCheck: 'desc' }
          });

          const productionData = await counterPrisma.productionData.findFirst({
            where: { deviceId: device.id },
            orderBy: { createdAt: 'desc' }
          });

          return {
            ...device,
            powerStatus: powerStatus?.hasPower || false,
            doorStatus: doorStatus?.isOpen || false,
            temperature: powerStatus?.ain1Value || null,
            lastSeen: powerStatus?.lastPowerCheck || null,
            productionCount: productionData?.dailyProduction || 0
          };
        } catch (error) {
          logger.error(`Error enriching device ${device.id}:`, error);
          return {
            ...device,
            powerStatus: false,
            doorStatus: false,
            temperature: null,
            lastSeen: null,
            productionCount: 0
          };
        }
      })
    );
    
    logger.info(`Retrieved ${devices.length} devices from database`);
    
    return res.json({
      success: true,
      data: enrichedDevices,
      count: enrichedDevices.length
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

    // Enrich with real-time data
    try {
      const powerStatus = await counterPrisma.devicePowerStatus.findFirst({
        where: { deviceId: device.id },
        orderBy: { lastPowerCheck: 'desc' }
      });

      const doorStatus = await counterPrisma.doorStatus.findFirst({
        where: { deviceId: device.id },
        orderBy: { lastCheck: 'desc' }
      });

      const productionData = await counterPrisma.productionData.findFirst({
        where: { deviceId: device.id },
        orderBy: { createdAt: 'desc' }
      });

      const enrichedDevice = {
        ...device,
        powerStatus: powerStatus?.hasPower || false,
        doorStatus: doorStatus?.isOpen || false,
        temperature: powerStatus?.ain1Value || null,
        lastSeen: powerStatus?.lastPowerCheck || null,
        productionCount: productionData?.dailyProduction || 0
      };

      return res.json({
        success: true,
        data: enrichedDevice
      });
    } catch (error) {
      logger.error(`Error enriching device ${deviceId}:`, error);
      return res.json({
        success: true,
        data: {
          ...device,
          powerStatus: false,
          doorStatus: false,
          temperature: null,
          lastSeen: null,
          productionCount: 0
        }
      });
    }
  } catch (error) {
    logger.error(`Error in GET /devices/${req.params.id}:`, error);
    return res.status(500).json({
      success: false,
      error: 'Failed to fetch device'
    });
  }
});

// Get devices by factory
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

    // Enrich with real-time data
    const enrichedDevices = await Promise.all(
      devices.map(async (device) => {
        try {
          const powerStatus = await counterPrisma.devicePowerStatus.findFirst({
            where: { deviceId: device.id },
            orderBy: { lastPowerCheck: 'desc' }
          });

          const doorStatus = await counterPrisma.doorStatus.findFirst({
            where: { deviceId: device.id },
            orderBy: { lastCheck: 'desc' }
          });

          const productionData = await counterPrisma.productionData.findFirst({
            where: { deviceId: device.id },
            orderBy: { createdAt: 'desc' }
          });

          return {
            ...device,
            powerStatus: powerStatus?.hasPower || false,
            doorStatus: doorStatus?.isOpen || false,
            temperature: powerStatus?.ain1Value || null,
            lastSeen: powerStatus?.lastPowerCheck || null,
            productionCount: productionData?.dailyProduction || 0
          };
        } catch (error) {
          logger.error(`Error enriching device ${device.id}:`, error);
          return {
            ...device,
            powerStatus: false,
            doorStatus: false,
            temperature: null,
            lastSeen: null,
            productionCount: 0
          };
        }
      })
    );

    return res.json({
      success: true,
      data: enrichedDevices,
      count: enrichedDevices.length
    });
  } catch (error) {
    logger.error(`Error in GET /devices/factory/${req.params.factoryId}:`, error);
    return res.status(500).json({
      success: false,
      error: 'Failed to fetch devices by factory'
    });
  }
});

// Get device statistics
router.get('/stats/overview', async (req, res) => {
  try {
    const totalDevices = await prisma.device.count();
    const onlineDevices = await prisma.device.count({
      where: { status: true }
    });

    // Get powered devices from counter database
    const poweredDevices = await counterPrisma.devicePowerStatus.count({
      where: { hasPower: true }
    });

    const stats = {
      total: totalDevices,
      online: onlineDevices,
      powered: poweredDevices,
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
      error: 'Failed to fetch device statistics'
    });
  }
});

export default router; 