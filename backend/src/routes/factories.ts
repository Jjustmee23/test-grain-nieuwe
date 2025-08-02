import { Router } from 'express';
import { prisma } from '../config/database';
import { logger } from '../config/logger';
import { authenticateToken } from '../middleware/auth';

const router = Router();

// Test endpoint to check if backend is working
router.get('/test', (req, res) => {
  return res.json({
    success: true,
    message: 'Factories endpoint is working',
    timestamp: new Date().toISOString()
  });
});

// Get all factories
router.get('/', async (req, res) => {
  try {
    logger.info('Fetching factories from database...');
    
    const factories = await prisma.factory.findMany({
      include: {
        city: {
          select: {
            id: true,
            name: true
          }
        },
        _count: {
          select: {
            devices: true,
            batches: true
          }
        }
      },
      orderBy: {
        name: 'asc'
      }
    });

    logger.info(`Retrieved ${factories.length} factories from database`);
    
    return res.json({
      success: true,
      data: factories,
      count: factories.length
    });
  } catch (error) {
    logger.error('Error in GET /factories:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to fetch factories',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Create new factory
router.post('/', authenticateToken, async (req, res) => {
  try {
    const { name, cityId, group, address, latitude, longitude } = req.body;

    // Validation
    if (!name || typeof name !== 'string' || name.trim().length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Factory name is required'
      });
    }

    if (!cityId || isNaN(parseInt(cityId))) {
      return res.status(400).json({
        success: false,
        error: 'Valid city ID is required'
      });
    }

    if (!group || !['government', 'private', 'commercial'].includes(group)) {
      return res.status(400).json({
        success: false,
        error: 'Valid group is required (government, private, or commercial)'
      });
    }

    // Check if city exists
    const city = await prisma.city.findUnique({
      where: { id: parseInt(cityId) }
    });

    if (!city) {
      return res.status(400).json({
        success: false,
        error: 'City not found'
      });
    }

    // Check if factory name already exists
    const existingFactory = await prisma.factory.findFirst({
      where: { name: name.trim() }
    });

    if (existingFactory) {
      return res.status(409).json({
        success: false,
        error: 'Factory with this name already exists'
      });
    }

    // Create factory
    const factory = await prisma.factory.create({
      data: {
        name: name.trim(),
        cityId: parseInt(cityId),
        group,
        address: address?.trim(),
        latitude: latitude ? parseFloat(latitude) : null,
        longitude: longitude ? parseFloat(longitude) : null,
        status: true,
        error: false
      },
      include: {
        city: {
          select: {
            id: true,
            name: true
          }
        },
        _count: {
          select: {
            devices: true,
            batches: true
          }
        }
      }
    });

    logger.info(`Created new factory: ${factory.name} in ${factory.city?.name}`);

    return res.status(201).json({
      success: true,
      message: 'Factory created successfully',
      data: factory
    });
  } catch (error) {
    logger.error('Error in POST /factories:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to create factory',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Get factory by ID
router.get('/:id', async (req, res) => {
  try {
    const id = parseInt(req.params.id);
    if (isNaN(id)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid factory ID'
      });
    }

    const factory = await prisma.factory.findUnique({
      where: { id },
      include: {
        city: {
          select: {
            id: true,
            name: true
          }
        },
        _count: {
          select: {
            devices: true,
            batches: true
          }
        }
      }
    });

    if (!factory) {
      return res.status(404).json({
        success: false,
        error: 'Factory not found'
      });
    }

    return res.json({
      success: true,
      data: factory
    });
  } catch (error) {
    logger.error(`Error in GET /factories/${req.params.id}:`, error);
    return res.status(500).json({
      success: false,
      error: 'Failed to fetch factory'
    });
  }
});

// Get factories by city
router.get('/city/:cityId', async (req, res) => {
  try {
    const cityId = parseInt(req.params.cityId);
    if (isNaN(cityId)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid city ID'
      });
    }

    const factories = await prisma.factory.findMany({
      where: { cityId },
      include: {
        city: {
          select: {
            id: true,
            name: true
          }
        },
        _count: {
          select: {
            devices: true,
            batches: true
          }
        }
      },
      orderBy: {
        name: 'asc'
      }
    });

    return res.json({
      success: true,
      data: factories,
      count: factories.length
    });
  } catch (error) {
    logger.error(`Error in GET /factories/city/${req.params.cityId}:`, error);
    return res.status(500).json({
      success: false,
      error: 'Failed to fetch factories by city'
    });
  }
});

// Get factory statistics
router.get('/stats/overview', async (req, res) => {
  try {
    const totalFactories = await prisma.factory.count();
    const activeFactories = await prisma.factory.count({
      where: { status: true }
    });
    const errorFactories = await prisma.factory.count({
      where: { error: true }
    });

    const stats = {
      total: totalFactories,
      active: activeFactories,
      error: errorFactories,
      inactive: totalFactories - activeFactories
    };

    return res.json({
      success: true,
      data: stats
    });
  } catch (error) {
    logger.error('Error in GET /factories/stats/overview:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to fetch factory statistics'
    });
  }
});

// Get factory statistics with devices
router.get('/stats', authenticateToken, async (req, res) => {
  try {
    const user = (req as any).user;
    
    // Get all factories
    let factories = await prisma.factory.findMany({
      include: {
        city: {
          select: {
            id: true,
            name: true
          }
        },
        devices: {
          select: {
            id: true,
            name: true,
            status: true,
            serialNumber: true,
            selectedCounter: true,
            createdAt: true
          }
        }
      },
      orderBy: {
        name: 'asc'
      }
    });

    // Filter factories based on user permissions
    if (!user.isSuperuser) {
      // For non-super users, filter based on permissions
      // This is a simplified version - you might want to implement more complex permission logic
      factories = factories.filter(factory => {
        // Add your permission logic here
        // For now, we'll show all factories
        return true;
      });
    }

    // Calculate statistics for each factory
    const factoriesWithStats = factories.map(factory => {
      const onlineDevices = factory.devices.filter(d => d.status).length;
      const totalDevices = factory.devices.length;
      
      // Calculate production metrics based on devices
      const baseProduction = totalDevices * 1000;
      const onlineMultiplier = totalDevices > 0 ? onlineDevices / totalDevices : 0;
      
      const daily = Math.round(baseProduction * onlineMultiplier * (0.8 + Math.random() * 0.4));
      const weekly = Math.round(daily * 7 * (0.9 + Math.random() * 0.2));
      const monthly = Math.round(daily * 30 * (0.85 + Math.random() * 0.3));
      const yearly = Math.round(daily * 365 * (0.8 + Math.random() * 0.4));

      return {
        ...factory,
        stats: {
          daily,
          weekly,
          monthly,
          yearly,
          deviceCount: totalDevices,
          onlineDevices,
          powerStatus: onlineDevices > 0 ? 'on' : 'off',
          doorStatus: Math.random() > 0.8 ? 'open' : 'closed',
          startTime: onlineDevices > 0 ? '08:00' : undefined,
          stopTime: onlineDevices > 0 ? '18:00' : undefined
        }
      };
    });

    return res.json({
      success: true,
      data: factoriesWithStats,
      count: factoriesWithStats.length
    });
  } catch (error) {
    console.error('Error fetching factory statistics:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to fetch factory statistics',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

export default router; 