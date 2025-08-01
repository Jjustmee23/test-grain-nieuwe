import { Router } from 'express';

const router = Router();

router.get('/', (req, res) => {
  res.json({ message: 'Batches endpoint' });
});

export default router; 