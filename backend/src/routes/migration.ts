import { Router } from 'express';
import { dataMigrationService } from '../services/data-migration';

const router = Router();

// Start data migration service
router.post('/start', async (req, res) => {
  try {
    await dataMigrationService.start();
    res.json({ 
      message: 'Data migration service started successfully',
      status: 'started'
    });
  } catch (error) {
    console.error('Failed to start migration service:', error);
    res.status(500).json({ 
      message: 'Failed to start migration service',
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Stop data migration service
router.post('/stop', async (req, res) => {
  try {
    await dataMigrationService.stop();
    res.json({ 
      message: 'Data migration service stopped successfully',
      status: 'stopped'
    });
  } catch (error) {
    console.error('Failed to stop migration service:', error);
    res.status(500).json({ 
      message: 'Failed to stop migration service',
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Trigger manual migration
router.post('/migrate-now', async (req, res) => {
  try {
    await dataMigrationService.migrateNow();
    res.json({ 
      message: 'Manual migration completed successfully',
      status: 'completed'
    });
  } catch (error) {
    console.error('Manual migration failed:', error);
    res.status(500).json({ 
      message: 'Manual migration failed',
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Get migration status
router.get('/status', async (req, res) => {
  try {
    const status = await dataMigrationService.getStatus();
    res.json(status);
  } catch (error) {
    console.error('Failed to get migration status:', error);
    res.status(500).json({ 
      message: 'Failed to get migration status',
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Get migration statistics
router.get('/stats', async (req, res) => {
  try {
    const { PrismaClient } = require('@prisma/client');
    const prisma = new PrismaClient();
    
    const totalRecords = await prisma.rawData.count();
    const todayRecords = await prisma.rawData.count({
      where: {
        createdAt: {
          gte: new Date(new Date().setHours(0, 0, 0, 0))
        }
      }
    });
    
    const latestRecord = await prisma.rawData.findFirst({
      orderBy: { createdAt: 'desc' },
      select: { createdAt: true, deviceId: true }
    });
    
    const deviceStats = await prisma.rawData.groupBy({
      by: ['deviceId'],
      _count: { deviceId: true },
      orderBy: { _count: { deviceId: 'desc' } },
      take: 10
    });
    
    res.json({
      totalRecords,
      todayRecords,
      latestRecord,
      deviceStats,
      migrationInterval: '5 minutes'
    });
  } catch (error) {
    console.error('Failed to get migration stats:', error);
    res.status(500).json({ 
      message: 'Failed to get migration stats',
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

export default router; 