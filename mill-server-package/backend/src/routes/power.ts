import { Router } from 'express';

const router = Router();

router.get('/', (req, res) => {
  res.json({ message: 'Power endpoint' });
});

export default router; 