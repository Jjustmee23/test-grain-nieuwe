import { Request, Response, NextFunction } from 'express';
import * as jwt from 'jsonwebtoken';

export interface AuthenticatedRequest extends Request {
  user?: {
    id: number;
    email: string;
    username: string;
    isSuperuser: boolean;
    isStaff: boolean;
  };
}

/**
 * JWT Authentication Middleware
 */
export const authenticateToken = (req: AuthenticatedRequest, res: Response, next: NextFunction): void => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

  if (!token) {
    res.status(401).json({ error: 'Access token required' });
    return;
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key') as any;
    req.user = {
      id: decoded.userId,
      email: decoded.email,
      username: decoded.username,
      isSuperuser: decoded.isSuperuser,
      isStaff: decoded.isStaff,
    };
    next();
  } catch (error) {
    console.error('Token verification failed:', error);
    res.status(403).json({ error: 'Invalid or expired token' });
    return;
  }
};

/**
 * Optional Authentication Middleware (doesn't fail if no token)
 */
export const optionalAuth = (req: AuthenticatedRequest, res: Response, next: NextFunction): void => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    next(); // Continue without authentication
    return;
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key') as any;
    req.user = {
      id: decoded.userId,
      email: decoded.email,
      username: decoded.username,
      isSuperuser: decoded.isSuperuser,
      isStaff: decoded.isStaff,
    };
    next();
  } catch (error) {
    console.error('Token verification failed:', error);
    // Continue without authentication instead of failing
    next();
  }
};

/**
 * Require authentication middleware
 */
export const requireAuth = (req: AuthenticatedRequest, res: Response, next: NextFunction): void => {
  if (!req.user) {
    res.status(401).json({ error: 'Authentication required' });
    return;
  }
  next();
};

/**
 * Require super admin middleware
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
 * Require admin middleware
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