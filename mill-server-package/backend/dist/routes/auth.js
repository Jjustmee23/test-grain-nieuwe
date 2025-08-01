"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const router = (0, express_1.Router)();
router.post('/login', async (req, res) => {
    try {
        const { email, password } = req.body;
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
        }
        else {
            res.status(401).json({ message: 'Invalid credentials' });
        }
    }
    catch (error) {
        res.status(500).json({ message: 'Internal server error' });
    }
});
exports.default = router;
//# sourceMappingURL=auth.js.map