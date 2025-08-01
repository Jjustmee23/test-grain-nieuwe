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

export default router; 