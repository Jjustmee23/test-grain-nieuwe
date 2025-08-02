import { Router } from 'express';
import { AuthController } from '../controllers/authController';
import { authenticateToken, requireAuth, requireAdmin } from '../middleware/auth';

const router = Router();

// Public routes
router.post('/login', AuthController.login);
router.post('/logout', AuthController.logout);
router.get('/verify', authenticateToken, AuthController.verifyToken);

// Protected routes
router.get('/profile', authenticateToken, requireAuth, AuthController.getProfile);
router.put('/profile', authenticateToken, requireAuth, AuthController.updateProfile);
router.post('/change-password', authenticateToken, requireAuth, AuthController.changePassword);

// Admin only routes
router.post('/register', authenticateToken, requireAdmin, AuthController.register);

export default router; 