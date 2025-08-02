import { Request, Response, NextFunction } from 'express';
import { PermissionType } from '@prisma/client';
import { PermissionService } from '../services/permissionService';

export interface AuthenticatedRequest extends Request {
  user?: {
    id: number;
    username: string;
    email: string;
    isSuperuser: boolean;
    isStaff: boolean;
  };
  accessibleIds?: (number | string)[];
}

/**
 * Middleware to check if user has permission for a specific resource
 */
export const requirePermission = (
  resourceType: 'city' | 'factory' | 'device',
  requiredPermission: PermissionType = PermissionType.READ
) => {
  return async (req: AuthenticatedRequest, res: Response, next: NextFunction): Promise<void> => {
    try {
      if (!req.user) {
        res.status(401).json({ error: 'Authentication required' });
        return;
      }

      // Super admin bypasses all permission checks
      if (req.user.isSuperuser) {
        next();
        return;
      }

      let resourceId: number | string;

      // Extract resource ID from request parameters
      switch (resourceType) {
        case 'city':
          resourceId = parseInt(req.params.cityId || req.body.cityId);
          break;
        case 'factory':
          resourceId = parseInt(req.params.factoryId || req.body.factoryId);
          break;
        case 'device':
          resourceId = req.params.deviceId || req.body.deviceId;
          break;
        default:
          res.status(400).json({ error: 'Invalid resource type' });
          return;
      }

      if (!resourceId) {
        res.status(400).json({ error: `${resourceType} ID is required` });
        return;
      }

      const hasPermission = await PermissionService.hasPermission(
        req.user.id,
        resourceType,
        resourceId,
        requiredPermission
      );

      if (!hasPermission) {
        res.status(403).json({ 
          error: `Insufficient permissions for ${resourceType}`,
          requiredPermission,
          resourceId 
        });
        return;
      }

      next();
    } catch (error) {
      console.error('Permission check error:', error);
      res.status(500).json({ error: 'Permission check failed' });
    }
  };
};

/**
 * Middleware to filter data based on user permissions
 */
export const filterByPermissions = (resourceType: 'city' | 'factory' | 'device') => {
  return async (req: AuthenticatedRequest, res: Response, next: NextFunction): Promise<void> => {
    try {
      if (!req.user) {
        res.status(401).json({ error: 'Authentication required' });
        return;
      }

      // Super admin sees all data
      if (req.user.isSuperuser) {
        next();
        return;
      }

      let accessibleIds: (number | string)[];

      switch (resourceType) {
        case 'city':
          accessibleIds = await PermissionService.getAccessibleCities(req.user.id);
          break;
        case 'factory':
          accessibleIds = await PermissionService.getAccessibleFactories(req.user.id);
          break;
        case 'device':
          accessibleIds = await PermissionService.getAccessibleDevices(req.user.id);
          break;
        default:
          res.status(400).json({ error: 'Invalid resource type' });
          return;
      }

      // Add accessible IDs to request for controllers to use
      req.accessibleIds = accessibleIds;
      next();
    } catch (error) {
      console.error('Permission filter error:', error);
      res.status(500).json({ error: 'Permission filtering failed' });
    }
  };
};

/**
 * Middleware to require super admin access
 */
export const requireSuperAdmin = (req: AuthenticatedRequest, res: Response, next: NextFunction): void => {
  if (!req.user) {
    res.status(401).json({ error: 'Authentication required' });
    return;
  }

  if (!req.user.isSuperuser) {
    res.status(403).json({ error: 'Super admin access required' });
    return;
  }

  next();
};

/**
 * Middleware to require admin access
 */
export const requireAdmin = (req: AuthenticatedRequest, res: Response, next: NextFunction): void => {
  if (!req.user) {
    res.status(401).json({ error: 'Authentication required' });
    return;
  }

  if (!req.user.isSuperuser && !req.user.isStaff) {
    res.status(403).json({ error: 'Admin access required' });
    return;
  }

  next();
}; 