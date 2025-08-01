import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function initializeDatabases() {
  console.log('🚀 Initializing Mill Management System Databases...');

  try {
    // Create admin user
    const adminPassword = await bcrypt.hash('admin123', 12);
    
    const adminUser = await prisma.user.upsert({
      where: { username: 'admin' },
      update: {},
      create: {
        email: 'admin@nexonsolutions.be',
        username: 'admin',
        password: adminPassword,
        firstName: 'Admin',
        lastName: 'User',
        isActive: true,
        isStaff: true,
        isSuperuser: true,
        userProfile: {
          create: {
            phoneNumber: '+32 123 456 789',
            department: 'IT',
            position: 'System Administrator',
            profilePicture: null,
            timezone: 'Europe/Brussels',
            language: 'en',
            theme: 'light',
            notificationPreferences: {
              email: true,
              sms: false,
              push: true
            }
          }
        }
      }
    });

    console.log('✅ Admin user created:', adminUser.email);

    // Create Danny user
    const dannyPassword = await bcrypt.hash('danny123', 12);
    
    const dannyUser = await prisma.user.upsert({
      where: { username: 'danny' },
      update: {},
      create: {
        email: 'danny.v@nexonsolutions.be',
        username: 'danny',
        password: dannyPassword,
        firstName: 'Danny',
        lastName: 'Verheyden',
        isActive: true,
        isStaff: true,
        isSuperuser: false,
        userProfile: {
          create: {
            phoneNumber: '+32 987 654 321',
            department: 'Operations',
            position: 'Operations Manager',
            profilePicture: null,
            timezone: 'Europe/Brussels',
            language: 'nl',
            theme: 'dark',
            notificationPreferences: {
              email: true,
              sms: true,
              push: true
            }
          }
        }
      }
    });

    console.log('✅ Danny user created:', dannyUser.email);

    console.log('🎉 Database initialization completed successfully!');
    console.log('');
    console.log('📋 Login Credentials:');
    console.log('Admin: admin@nexonsolutions.be / admin123');
    console.log('Danny: danny.v@nexonsolutions.be / danny123');

  } catch (error) {
    console.error('❌ Database initialization failed:', error);
    throw error;
  } finally {
    await prisma.$disconnect();
  }
}

// Run the initialization
initializeDatabases()
  .then(() => {
    console.log('✅ Database initialization script completed');
    process.exit(0);
  })
  .catch((error) => {
    console.error('❌ Database initialization script failed:', error);
    process.exit(1);
  }); 