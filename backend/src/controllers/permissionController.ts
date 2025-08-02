import { Request, Response } from 'express';
import { PrismaClient, PermissionType } from '@prisma/client';
import { PermissionService } from '../services/permissionService';

const prisma = new PrismaClient();

export class PermissionController {
  /**
   * Get all permissions for the current user
   */
  static async getUserPermissions(req: Request, res: Response) {
    try {
      const userId = (req as any).user?.id;
      if (!userId) {
        return res.status(401).json({ error: 'Authentication required' });
      }

      const permissions = await PermissionService.getUserPermissions(userId);
      res.json(permissions);
    } catch (error) {
      console.error('Error getting user permissions:', error);
      res.status(500).json({ error: 'Failed to get user permissions' });
    }
  }

  /**
   * Assign permission to user for a city
   */
  static async assignCityPermission(req: Request, res: Response) {
    try {
      const { userId, cityId, permission } = req.body;

      if (!userId || !cityId || !permission) {
        return res.status(400).json({ 
          error: 'userId, cityId, and permission are required' 
        });
      }

      await PermissionService.assignCityPermission(userId, cityId, permission);
      res.json({ message: 'City permission assigned successfully' });
    } catch (error) {
      console.error('Error assigning city permission:', error);
      res.status(500).json({ error: 'Failed to assign city permission' });
    }
  }

  /**
   * Assign permission to user for a factory
   */
  static async assignFactoryPermission(req: Request, res: Response) {
    try {
      const { userId, factoryId, permission } = req.body;

      if (!userId || !factoryId || !permission) {
        return res.status(400).json({ 
          error: 'userId, factoryId, and permission are required' 
        });
      }

      await PermissionService.assignFactoryPermission(userId, factoryId, permission);
      res.json({ message: 'Factory permission assigned successfully' });
    } catch (error) {
      console.error('Error assigning factory permission:', error);
      res.status(500).json({ error: 'Failed to assign factory permission' });
    }
  }

  /**
   * Assign permission to user for a device
   */
  static async assignDevicePermission(req: Request, res: Response) {
    try {
      const { userId, deviceId, permission } = req.body;

      if (!userId || !deviceId || !permission) {
        return res.status(400).json({ 
          error: 'userId, deviceId, and permission are required' 
        });
      }

      await PermissionService.assignDevicePermission(userId, deviceId, permission);
      res.json({ message: 'Device permission assigned successfully' });
    } catch (error) {
      console.error('Error assigning device permission:', error);
      res.status(500).json({ error: 'Failed to assign device permission' });
    }
  }

  /**
   * Remove permission from user for a city
   */
  static async removeCityPermission(req: Request, res: Response) {
    try {
      const { userId, cityId } = req.params;

      if (!userId || !cityId) {
        return res.status(400).json({ 
          error: 'userId and cityId are required' 
        });
      }

      await PermissionService.removeCityPermission(parseInt(userId), parseInt(cityId));
      res.json({ message: 'City permission removed successfully' });
    } catch (error) {
      console.error('Error removing city permission:', error);
      res.status(500).json({ error: 'Failed to remove city permission' });
    }
  }

  /**
   * Remove permission from user for a factory
   */
  static async removeFactoryPermission(req: Request, res: Response) {
    try {
      const { userId, factoryId } = req.params;

      if (!userId || !factoryId) {
        return res.status(400).json({ 
          error: 'userId and factoryId are required' 
        });
      }

      await PermissionService.removeFactoryPermission(parseInt(userId), parseInt(factoryId));
      res.json({ message: 'Factory permission removed successfully' });
    } catch (error) {
      console.error('Error removing factory permission:', error);
      res.status(500).json({ error: 'Failed to remove factory permission' });
    }
  }

  /**
   * Remove permission from user for a device
   */
  static async removeDevicePermission(req: Request, res: Response) {
    try {
      const { userId, deviceId } = req.params;

      if (!userId || !deviceId) {
        return res.status(400).json({ 
          error: 'userId and deviceId are required' 
        });
      }

      await PermissionService.removeDevicePermission(parseInt(userId), deviceId);
      res.json({ message: 'Device permission removed successfully' });
    } catch (error) {
      console.error('Error removing device permission:', error);
      res.status(500).json({ error: 'Failed to remove device permission' });
    }
  }

  /**
   * Get all users with their permissions
   */
  static async getAllUsersWithPermissions(req: Request, res: Response) {
    try {
      const users = await prisma.user.findMany({
        include: {
          userCityPermissions: {
            include: { city: true },
          },
          userFactoryPermissions: {
            include: { factory: true },
          },
          userDevicePermissions: {
            include: { device: true },
          },
        },
      });

      const usersWithPermissions = users.map(user => ({
        id: user.id,
        username: user.username,
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        isStaff: user.isStaff,
        isActive: user.isActive,
        isSuperuser: user.isSuperuser,
        cityPermissions: user.userCityPermissions.map(p => ({
          cityId: p.cityId,
          cityName: p.city.name,
          permission: p.permission,
        })),
        factoryPermissions: user.userFactoryPermissions.map(p => ({
          factoryId: p.factoryId,
          factoryName: p.factory.name,
          permission: p.permission,
        })),
        devicePermissions: user.userDevicePermissions.map(p => ({
          deviceId: p.deviceId,
          deviceName: p.device.name || p.device.id,
          permission: p.permission,
        })),
      }));

      res.json(usersWithPermissions);
    } catch (error) {
      console.error('Error getting users with permissions:', error);
      res.status(500).json({ error: 'Failed to get users with permissions' });
    }
  }

  /**
   * Get permission types
   */
  static async getPermissionTypes(req: Request, res: Response) {
    try {
      const permissionTypes = Object.values(PermissionType);
      res.json(permissionTypes);
    } catch (error) {
      console.error('Error getting permission types:', error);
      res.status(500).json({ error: 'Failed to get permission types' });
    }
  }
} 