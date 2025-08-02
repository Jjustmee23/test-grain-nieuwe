import { Request, Response } from 'express';
import { PrismaClient } from '@prisma/client';
import * as bcrypt from 'bcryptjs';
import * as jwt from 'jsonwebtoken';

const prisma = new PrismaClient();

export class AuthController {
  /**
   * User login
   */
  static async login(req: Request, res: Response): Promise<void> {
    try {
      const { email, password } = req.body;

      // Basic validation
      if (!email || !password) {
        res.status(400).json({
          error: 'Email and password are required',
        });
        return;
      }

      // Find user by email (including password for verification)
      const user = await prisma.user.findUnique({
        where: { email },
      });

      if (!user) {
        res.status(401).json({ error: 'Invalid email or password' });
        return;
      }

      // Check if user is active
      if (!user.isActive) {
        res.status(401).json({ error: 'Account is deactivated' });
        return;
      }

      // Verify password
      const isValidPassword = await bcrypt.compare(password, user.password);
      if (!isValidPassword) {
        res.status(401).json({ error: 'Invalid email or password' });
        return;
      }

      // Update last login
      await prisma.user.update({
        where: { id: user.id },
        data: { lastLogin: new Date() },
      });

      // Get user profile separately
      const userProfile = await prisma.userProfile.findUnique({
        where: { userId: user.id },
      });

      // Generate JWT token
      const token = jwt.sign(
        {
          userId: user.id,
          email: user.email,
          username: user.username,
          isSuperuser: user.isSuperuser,
          isStaff: user.isStaff,
        },
        process.env.JWT_SECRET || 'your-secret-key',
        { expiresIn: '24h' }
      );

      // Return user data (without password) and token
      const userData = {
        id: user.id,
        username: user.username,
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        isStaff: user.isStaff,
        isActive: user.isActive,
        isSuperuser: user.isSuperuser,
        dateJoined: user.dateJoined,
        lastLogin: user.lastLogin,
        userProfile: userProfile,
      };

      res.json({
        message: 'Login successful',
        token,
        user: userData,
      });
    } catch (error) {
      console.error('Login error:', error);
      res.status(500).json({ error: 'Login failed' });
    }
  }

  /**
   * User registration (admin only)
   */
  static async register(req: Request, res: Response): Promise<void> {
    try {
      // Check if user is admin
      const currentUser = (req as any).user;
      if (!currentUser || (!currentUser.isSuperuser && !currentUser.isStaff)) {
        res.status(403).json({ error: 'Admin access required' });
        return;
      }

      const { username, email, password, firstName, lastName } = req.body;

      // Basic validation
      if (!username || !email || !password || !firstName || !lastName) {
        res.status(400).json({
          error: 'All fields are required',
        });
        return;
      }

      if (password.length < 8) {
        res.status(400).json({
          error: 'Password must be at least 8 characters',
        });
        return;
      }

      // Check if email already exists
      const existingUser = await prisma.user.findFirst({
        where: {
          OR: [
            { email },
            { username },
          ],
        },
      });

      if (existingUser) {
        res.status(400).json({
          error: 'User with this email or username already exists',
        });
        return;
      }

      // Hash password
      const hashedPassword = await bcrypt.hash(password, 10);

      // Create user
      const newUser = await prisma.user.create({
        data: {
          username,
          email,
          password: hashedPassword,
          firstName,
          lastName,
          isStaff: false,
          isActive: true,
          isSuperuser: false,
        },
        include: {
          userProfile: true,
        },
      });

      // Create user profile
      await prisma.userProfile.create({
        data: {
          userId: newUser.id,
          team: 'Production',
          supportTicketsEnabled: false,
        },
      });

      // Return user data (without password)
      const userData = {
        id: newUser.id,
        username: newUser.username,
        email: newUser.email,
        firstName: newUser.firstName,
        lastName: newUser.lastName,
        isStaff: newUser.isStaff,
        isActive: newUser.isActive,
        isSuperuser: newUser.isSuperuser,
        dateJoined: newUser.dateJoined,
        lastLogin: newUser.lastLogin,
        userProfile: newUser.userProfile,
      };

      res.status(201).json({
        message: 'User created successfully',
        user: userData,
      });
    } catch (error) {
      console.error('Registration error:', error);
      res.status(500).json({ error: 'Registration failed' });
    }
  }

  /**
   * Get current user profile
   */
  static async getProfile(req: Request, res: Response): Promise<void> {
    try {
      const userId = (req as any).user?.id;
      if (!userId) {
        res.status(401).json({ error: 'Authentication required' });
        return;
      }

      const user = await prisma.user.findUnique({
        where: { id: userId },
        include: {
          userProfile: true,
        },
      });

      if (!user) {
        res.status(404).json({ error: 'User not found' });
        return;
      }

      // Return user data (without password)
      const userData = {
        id: user.id,
        username: user.username,
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        isStaff: user.isStaff,
        isActive: user.isActive,
        isSuperuser: user.isSuperuser,
        dateJoined: user.dateJoined,
        lastLogin: user.lastLogin,
        userProfile: user.userProfile,
      };

      res.json(userData);
    } catch (error) {
      console.error('Get profile error:', error);
      res.status(500).json({ error: 'Failed to get profile' });
    }
  }

  /**
   * Update user profile
   */
  static async updateProfile(req: Request, res: Response): Promise<void> {
    try {
      const userId = (req as any).user?.id;
      if (!userId) {
        res.status(401).json({ error: 'Authentication required' });
        return;
      }

      const { firstName, lastName, team, supportTicketsEnabled } = req.body;

      // Update user
      const updatedUser = await prisma.user.update({
        where: { id: userId },
        data: {
          firstName: firstName || undefined,
          lastName: lastName || undefined,
        },
        include: {
          userProfile: true,
        },
      });

      // Update user profile
      if (team !== undefined || supportTicketsEnabled !== undefined) {
        await prisma.userProfile.update({
          where: { userId },
          data: {
            team: team || undefined,
            supportTicketsEnabled: supportTicketsEnabled || undefined,
          },
        });
      }

      // Return updated user data (without password)
      const userData = {
        id: updatedUser.id,
        username: updatedUser.username,
        email: updatedUser.email,
        firstName: updatedUser.firstName,
        lastName: updatedUser.lastName,
        isStaff: updatedUser.isStaff,
        isActive: updatedUser.isActive,
        isSuperuser: updatedUser.isSuperuser,
        dateJoined: updatedUser.dateJoined,
        lastLogin: updatedUser.lastLogin,
        userProfile: updatedUser.userProfile,
      };

      res.json({
        message: 'Profile updated successfully',
        user: userData,
      });
    } catch (error) {
      console.error('Update profile error:', error);
      res.status(500).json({ error: 'Failed to update profile' });
    }
  }

  /**
   * Change password
   */
  static async changePassword(req: Request, res: Response): Promise<void> {
    try {
      const userId = (req as any).user?.id;
      if (!userId) {
        res.status(401).json({ error: 'Authentication required' });
        return;
      }

      const { currentPassword, newPassword } = req.body;

      // Basic validation
      if (!currentPassword || !newPassword) {
        res.status(400).json({
          error: 'Current password and new password are required',
        });
        return;
      }

      if (newPassword.length < 8) {
        res.status(400).json({
          error: 'New password must be at least 8 characters',
        });
        return;
      }

      // Get current user
      const user = await prisma.user.findUnique({
        where: { id: userId },
      });

      if (!user) {
        res.status(404).json({ error: 'User not found' });
        return;
      }

      // Verify current password
      const isValidPassword = await bcrypt.compare(currentPassword, user.password);
      if (!isValidPassword) {
        res.status(400).json({ error: 'Current password is incorrect' });
        return;
      }

      // Hash new password
      const hashedNewPassword = await bcrypt.hash(newPassword, 10);

      // Update password
      await prisma.user.update({
        where: { id: userId },
        data: { password: hashedNewPassword },
      });

      res.json({ message: 'Password changed successfully' });
    } catch (error) {
      console.error('Change password error:', error);
      res.status(500).json({ error: 'Failed to change password' });
    }
  }

  /**
   * Logout (client-side token removal)
   */
  static async logout(req: Request, res: Response): Promise<void> {
    try {
      // In a stateless JWT system, logout is handled client-side
      // by removing the token from storage
      res.json({ message: 'Logout successful' });
    } catch (error) {
      console.error('Logout error:', error);
      res.status(500).json({ error: 'Logout failed' });
    }
  }

  /**
   * Verify token and return user data
   */
  static async verifyToken(req: Request, res: Response): Promise<void> {
    try {
      const userId = (req as any).user?.id;
      if (!userId) {
        res.status(401).json({ error: 'Invalid token' });
        return;
      }

      const user = await prisma.user.findUnique({
        where: { id: userId },
        include: {
          userProfile: true,
        },
      });

      if (!user) {
        res.status(401).json({ error: 'User not found' });
        return;
      }

      if (!user.isActive) {
        res.status(401).json({ error: 'Account is deactivated' });
        return;
      }

      // Return user data (without password)
      const userData = {
        id: user.id,
        username: user.username,
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        isStaff: user.isStaff,
        isActive: user.isActive,
        isSuperuser: user.isSuperuser,
        dateJoined: user.dateJoined,
        lastLogin: user.lastLogin,
        userProfile: user.userProfile,
      };

      res.json({
        valid: true,
        user: userData,
      });
    } catch (error) {
      console.error('Token verification error:', error);
      res.status(401).json({ error: 'Invalid token' });
    }
  }
} 