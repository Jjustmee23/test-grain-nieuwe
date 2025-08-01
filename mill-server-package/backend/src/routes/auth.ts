import { Router } from 'express';

const router = Router();

// Basic login endpoint
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    
    // Mock authentication - replace with real logic
    if (email === 'admin@example.com' && password === 'password') {
      res.json({
        user: {
          id: 1,
          email: email,
          name: 'Admin User',
          role: 'admin'
        },
        token: 'mock-jwt-token'
      });
    } else {
      res.status(401).json({ message: 'Invalid credentials' });
    }
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

export default router; 