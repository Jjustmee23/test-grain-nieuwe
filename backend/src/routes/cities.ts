import { Router } from 'express';
import { PrismaClient } from '@prisma/client';
import { authenticateToken } from '../middleware/auth';

const router = Router();
const prisma = new PrismaClient();

// GET /api/cities/public - Get all cities (public, no auth required)
router.get('/public', async (req, res) => {
  try {
    const cities = await prisma.city.findMany({
      include: {
        _count: {
          select: {
            factories: true
          }
        }
      },
      orderBy: {
        name: 'asc'
      }
    });

    res.json({
      success: true,
      data: cities,
      total: cities.length
    });
  } catch (error) {
    console.error('Error fetching cities:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch cities',
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// GET /api/cities - Get all cities
router.get('/', authenticateToken, async (req, res) => {
  try {
    const cities = await prisma.city.findMany({
      include: {
        factories: {
          include: {
            devices: true,
            _count: {
              select: {
                devices: true,
                batches: true
              }
            }
          }
        },
        _count: {
          select: {
            factories: true
          }
        }
      },
      orderBy: {
        name: 'asc'
      }
    });

    res.json({
      success: true,
      data: cities,
      total: cities.length
    });
  } catch (error) {
    console.error('Error fetching cities:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch cities',
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// GET /api/cities/:id - Get city by ID
router.get('/:id', authenticateToken, async (req, res) => {
  try {
    const { id } = req.params;
    const cityId = parseInt(id);

    if (isNaN(cityId)) {
      return res.status(400).json({
        success: false,
        message: 'Invalid city ID'
      });
    }

    const city = await prisma.city.findUnique({
      where: { id: cityId },
      include: {
        factories: {
          include: {
            devices: {
              include: {
                _count: {
                  select: {
                    productionData: true,
                    powerEvents: true
                  }
                }
              }
            },
            _count: {
              select: {
                devices: true,
                batches: true
              }
            }
          }
        },
        _count: {
          select: {
            factories: true
          }
        }
      }
    });

    if (!city) {
      return res.status(404).json({
        success: false,
        message: 'City not found'
      });
    }

    return res.json({
      success: true,
      data: city
    });
  } catch (error) {
    console.error('Error fetching city:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to fetch city',
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// POST /api/cities - Create new city
router.post('/', authenticateToken, async (req, res) => {
  try {
    const { name, status = true } = req.body;

    if (!name || typeof name !== 'string' || name.trim().length === 0) {
      return res.status(400).json({
        success: false,
        message: 'City name is required'
      });
    }

    // Check if city already exists
    const existingCity = await prisma.city.findUnique({
      where: { name: name.trim() }
    });

    if (existingCity) {
      return res.status(409).json({
        success: false,
        message: 'City with this name already exists'
      });
    }

    const city = await prisma.city.create({
      data: {
        name: name.trim(),
        status
      },
      include: {
        factories: true,
        _count: {
          select: {
            factories: true
          }
        }
      }
    });

    return res.status(201).json({
      success: true,
      message: 'City created successfully',
      data: city
    });
  } catch (error) {
    console.error('Error creating city:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to create city',
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// PUT /api/cities/:id - Update city
router.put('/:id', authenticateToken, async (req, res) => {
  try {
    const { id } = req.params;
    const { name, status } = req.body;
    const cityId = parseInt(id);

    if (isNaN(cityId)) {
      return res.status(400).json({
        success: false,
        message: 'Invalid city ID'
      });
    }

    // Check if city exists
    const existingCity = await prisma.city.findUnique({
      where: { id: cityId }
    });

    if (!existingCity) {
      return res.status(404).json({
        success: false,
        message: 'City not found'
      });
    }

    // Check if new name conflicts with existing city
    if (name && name !== existingCity.name) {
      const nameConflict = await prisma.city.findUnique({
        where: { name: name.trim() }
      });

      if (nameConflict) {
        return res.status(409).json({
          success: false,
          message: 'City with this name already exists'
        });
      }
    }

    const updateData: any = {};
    if (name !== undefined) updateData.name = name.trim();
    if (status !== undefined) updateData.status = status;

    const city = await prisma.city.update({
      where: { id: cityId },
      data: updateData,
      include: {
        factories: true,
        _count: {
          select: {
            factories: true
          }
        }
      }
    });

    return res.json({
      success: true,
      message: 'City updated successfully',
      data: city
    });
  } catch (error) {
    console.error('Error updating city:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to update city',
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// DELETE /api/cities/:id - Delete city
router.delete('/:id', authenticateToken, async (req, res) => {
  try {
    const { id } = req.params;
    const cityId = parseInt(id);

    if (isNaN(cityId)) {
      return res.status(400).json({
        success: false,
        message: 'Invalid city ID'
      });
    }

    // Check if city exists
    const city = await prisma.city.findUnique({
      where: { id: cityId },
      include: {
        _count: {
          select: {
            factories: true
          }
        }
      }
    });

    if (!city) {
      return res.status(404).json({
        success: false,
        message: 'City not found'
      });
    }

    // Check if city has factories
    if (city._count.factories > 0) {
      return res.status(400).json({
        success: false,
        message: 'Cannot delete city with existing factories. Please remove or reassign factories first.'
      });
    }

    await prisma.city.delete({
      where: { id: cityId }
    });

    return res.json({
      success: true,
      message: 'City deleted successfully'
    });
  } catch (error) {
    console.error('Error deleting city:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to delete city',
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// GET /api/cities/:id/factories - Get factories for a city
router.get('/:id/factories', authenticateToken, async (req, res) => {
  try {
    const { id } = req.params;
    const cityId = parseInt(id);

    if (isNaN(cityId)) {
      return res.status(400).json({
        success: false,
        message: 'Invalid city ID'
      });
    }

    const factories = await prisma.factory.findMany({
      where: { cityId },
      include: {
        devices: {
          include: {
            _count: {
              select: {
                productionData: true,
                powerEvents: true
              }
            }
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
      total: factories.length
    });
  } catch (error) {
    console.error('Error fetching city factories:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to fetch city factories',
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// GET /api/cities/:id/statistics - Get city statistics
router.get('/:id/statistics', authenticateToken, async (req, res) => {
  try {
    const { id } = req.params;
    const cityId = parseInt(id);

    if (isNaN(cityId)) {
      return res.status(400).json({
        success: false,
        message: 'Invalid city ID'
      });
    }

    const city = await prisma.city.findUnique({
      where: { id: cityId },
      include: {
        factories: {
          include: {
            devices: {
              include: {
                _count: {
                  select: {
                    productionData: true,
                    powerEvents: true
                  }
                }
              }
            },
            _count: {
              select: {
                devices: true,
                batches: true
              }
            }
          }
        }
      }
    });

    if (!city) {
      return res.status(404).json({
        success: false,
        message: 'City not found'
      });
    }

    // Calculate statistics
    const totalFactories = city.factories.length;
    const activeFactories = city.factories.filter(f => f.status).length;
    const totalDevices = city.factories.reduce((sum, f) => sum + f._count.devices, 0);
    const totalBatches = city.factories.reduce((sum, f) => sum + f._count.batches, 0);
    const totalProductionData = city.factories.reduce((sum, f) => 
      sum + f.devices.reduce((dSum, d) => dSum + d._count.productionData, 0), 0
    );
    const totalPowerEvents = city.factories.reduce((sum, f) => 
      sum + f.devices.reduce((dSum, d) => dSum + d._count.powerEvents, 0), 0
    );

    const statistics = {
      cityId: city.id,
      cityName: city.name,
      totalFactories,
      activeFactories,
      inactiveFactories: totalFactories - activeFactories,
      totalDevices,
      totalBatches,
      totalProductionData,
      totalPowerEvents,
      factories: city.factories.map(factory => ({
        id: factory.id,
        name: factory.name,
        status: factory.status,
        deviceCount: factory._count.devices,
        batchCount: factory._count.batches,
        devices: factory.devices.map(device => ({
          id: device.id,
          name: device.name,
          status: device.status,
          productionDataCount: device._count.productionData,
          powerEventsCount: device._count.powerEvents
        }))
      }))
    };

    return res.json({
      success: true,
      data: statistics
    });
  } catch (error) {
    console.error('Error fetching city statistics:', error);
    return res.status(500).json({
      success: false,
      message: 'Failed to fetch city statistics',
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

export default router; 