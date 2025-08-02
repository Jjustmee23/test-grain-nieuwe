import { PrismaClient } from '@prisma/client';
import * as bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Starting database seed...');

  // Create Danny as Super Admin User
  const dannyPassword = await bcrypt.hash('Jjustmee12773@', 10);
  const danny = await prisma.user.upsert({
    where: { email: 'danny.v@nexonsolutions.be' },
    update: {},
    create: {
      username: 'danny',
      email: 'danny.v@nexonsolutions.be',
      firstName: 'Danny',
      lastName: 'V',
      password: dannyPassword,
      isStaff: true,
      isActive: true,
      isSuperuser: true,
    },
  });

  // Create Super Admin User
  const superAdminPassword = await bcrypt.hash('superadmin123', 10);
  const superAdmin = await prisma.user.upsert({
    where: { email: 'superadmin@mill.com' },
    update: {},
    create: {
      username: 'superadmin',
      email: 'superadmin@mill.com',
      firstName: 'Super',
      lastName: 'Admin',
      password: superAdminPassword,
      isStaff: true,
      isActive: true,
      isSuperuser: true,
    },
  });

  // Create Admin User
  const adminPassword = await bcrypt.hash('admin123', 10);
  const admin = await prisma.user.upsert({
    where: { email: 'admin@mill.com' },
    update: {},
    create: {
      username: 'admin',
      email: 'admin@mill.com',
      firstName: 'Admin',
      lastName: 'User',
      password: adminPassword,
      isStaff: true,
      isActive: true,
      isSuperuser: false,
    },
  });

  // Create Regular User
  const userPassword = await bcrypt.hash('user123', 10);
  const user = await prisma.user.upsert({
    where: { email: 'user@mill.com' },
    update: {},
    create: {
      username: 'user',
      email: 'user@mill.com',
      firstName: 'Regular',
      lastName: 'User',
      password: userPassword,
      isStaff: false,
      isActive: true,
      isSuperuser: false,
    },
  });

  // Create Cities
  const cities = await Promise.all([
    prisma.city.upsert({
      where: { name: 'Antwerpen' },
      update: {},
      create: { name: 'Antwerpen', status: true },
    }),
    prisma.city.upsert({
      where: { name: 'Gent' },
      update: {},
      create: { name: 'Gent', status: true },
    }),
    prisma.city.upsert({
      where: { name: 'Brugge' },
      update: {},
      create: { name: 'Brugge', status: true },
    }),
    prisma.city.upsert({
      where: { name: 'Leuven' },
      update: {},
      create: { name: 'Leuven', status: true },
    }),
  ]);

  // Create Factories
  const factories = await Promise.all([
    prisma.factory.create({
      data: {
        name: 'Antwerpen Mill 1',
        status: true,
        error: false,
        group: 'government',
        address: 'Antwerpen Centrum',
        latitude: 51.2194,
        longitude: 4.4025,
        cityId: cities[0].id,
      },
    }),
    prisma.factory.create({
      data: {
        name: 'Antwerpen Mill 2',
        status: true,
        error: false,
        group: 'private',
        address: 'Antwerpen Haven',
        latitude: 51.2194,
        longitude: 4.4025,
        cityId: cities[0].id,
      },
    }),
    prisma.factory.create({
      data: {
        name: 'Gent Mill 1',
        status: true,
        error: false,
        group: 'commercial',
        address: 'Gent Centrum',
        latitude: 51.0500,
        longitude: 3.7300,
        cityId: cities[1].id,
      },
    }),
    prisma.factory.create({
      data: {
        name: 'Brugge Mill 1',
        status: true,
        error: false,
        group: 'government',
        address: 'Brugge Centrum',
        latitude: 51.2093,
        longitude: 3.2247,
        cityId: cities[2].id,
      },
    }),
  ]);

  // Create Devices (from MQTT data)
  const devices = await Promise.all([
    prisma.device.upsert({
      where: { id: '6445F17439690014' },
      update: {},
      create: {
        id: '6445F17439690014',
        name: 'Antwerpen Mill 1 - Device 1',
        serialNumber: '6445F17439690014',
        selectedCounter: 'counter_1',
        status: true,
        isConfigured: true,
        factoryId: factories[0].id,
      },
    }),
    prisma.device.upsert({
      where: { id: '6445F17094410018' },
      update: {},
      create: {
        id: '6445F17094410018',
        name: 'Antwerpen Mill 2 - Device 1',
        serialNumber: '6445F17094410018',
        selectedCounter: 'counter_1',
        status: true,
        isConfigured: true,
        factoryId: factories[1].id,
      },
    }),
    prisma.device.upsert({
      where: { id: '6445E28636540016' },
      update: {},
      create: {
        id: '6445E28636540016',
        name: 'Gent Mill 1 - Device 1',
        serialNumber: '6445E28636540016',
        selectedCounter: 'counter_1',
        status: true,
        isConfigured: true,
        factoryId: factories[2].id,
      },
    }),
    // Add some unconfigured devices (new devices from MQTT)
    prisma.device.upsert({
      where: { id: '6445F17439690015' },
      update: {},
      create: {
        id: '6445F17439690015',
        serialNumber: '6445F17439690015',
        selectedCounter: 'counter_1',
        status: true,
        isConfigured: false, // This is a new device that needs configuration
      },
    }),
    prisma.device.upsert({
      where: { id: '6445F17094410019' },
      update: {},
      create: {
        id: '6445F17094410019',
        serialNumber: '6445F17094410019',
        selectedCounter: 'counter_1',
        status: false,
        isConfigured: false, // This is a new device that needs configuration
      },
    }),
    prisma.device.upsert({
      where: { id: '6445E28636540017' },
      update: {},
      create: {
        id: '6445E28636540017',
        serialNumber: '6445E28636540017',
        selectedCounter: 'counter_1',
        status: true,
        isConfigured: false, // This is a new device that needs configuration
      },
    }),
    prisma.device.upsert({
      where: { id: '6445F17439690016' },
      update: {},
      create: {
        id: '6445F17439690016',
        serialNumber: '6445F17439690016',
        selectedCounter: 'counter_1',
        status: false,
        isConfigured: false, // This is a new device that needs configuration
      },
    }),
  ]);

  // Create User Profiles
  await Promise.all([
    prisma.userProfile.upsert({
      where: { userId: superAdmin.id },
      update: {},
      create: {
        userId: superAdmin.id,
        team: 'Management',
        supportTicketsEnabled: true,
      },
    }),
    prisma.userProfile.upsert({
      where: { userId: admin.id },
      update: {},
      create: {
        userId: admin.id,
        team: 'Operations',
        supportTicketsEnabled: true,
      },
    }),
    prisma.userProfile.upsert({
      where: { userId: user.id },
      update: {},
      create: {
        userId: user.id,
        team: 'Production',
        supportTicketsEnabled: false,
      },
    }),
  ]);

  console.log('✅ Database seeded successfully!');
  console.log('👤 Users created:');
  console.log(`   Super Admin: ${superAdmin.email}`);
  console.log(`   Admin: ${admin.email}`);
  console.log(`   User: ${user.email}`);
  console.log(`🏙️ Cities created: ${cities.length}`);
  console.log(`🏭 Factories created: ${factories.length}`);
  console.log(`📱 Devices created: ${devices.length}`);
}

main()
  .catch((e) => {
    console.error('❌ Error seeding database:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  }); 