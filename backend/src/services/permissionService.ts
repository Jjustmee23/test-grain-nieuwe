import { PrismaClient, UserRole, PermissionType } from '@prisma/client';

const prisma = new PrismaClient();

export interface UserPermissions {
  cities: { id: number; name: string; permission: PermissionType }[];
  factories: { id: number; name: string; permission: PermissionType }[];
  devices: { id: string; name: string; permission: PermissionType }[];
}

export class PermissionService {
  /**
   * Check if user has permission for a specific resource
   */
  static async hasPermission(
    userId: number,
    resourceType: 'city' | 'factory' | 'device',
    resourceId: number | string,
    requiredPermission: PermissionType
  ): Promise<boolean> {
    const user = await prisma.user.findUnique({
      where: { id: userId },
      include: {
        userCityPermissions: true,
        userFactoryPermissions: true,
        userDevicePermissions: true,
      },
    });

    if (!user) return false;

    // Super admin has all permissions
    if (user.isSuperuser) return true;

    // Check specific permissions based on resource type
    switch (resourceType) {
      case 'city':
        const cityPermission = user.userCityPermissions.find(
          p => p.cityId === resourceId
        );
        return cityPermission ? this.hasRequiredPermission(cityPermission.permission, requiredPermission) : false;

      case 'factory':
        const factoryPermission = user.userFactoryPermissions.find(
          p => p.factoryId === resourceId
        );
        return factoryPermission ? this.hasRequiredPermission(factoryPermission.permission, requiredPermission) : false;

      case 'device':
        const devicePermission = user.userDevicePermissions.find(
          p => p.deviceId === resourceId
        );
        return devicePermission ? this.hasRequiredPermission(devicePermission.permission, requiredPermission) : false;

      default:
        return false;
    }
  }

  /**
   * Get all permissions for a user
   */
  static async getUserPermissions(userId: number): Promise<UserPermissions> {
    const user = await prisma.user.findUnique({
      where: { id: userId },
      include: {
        userCityPermissions: {
          include: { city: true },
        },
        userFactoryPermissions: {
          include: { factory: true },
        },
        userDevicePermissions: {
          include: { device: true },
        },
      },
    });

    if (!user) {
      throw new Error('User not found');
    }

    // Super admin gets all resources
    if (user.isSuperuser) {
      const [cities, factories, devices] = await Promise.all([
        prisma.city.findMany(),
        prisma.factory.findMany(),
        prisma.device.findMany(),
      ]);

      return {
        cities: cities.map(city => ({ id: city.id, name: city.name, permission: PermissionType.MANAGE })),
        factories: factories.map(factory => ({ id: factory.id, name: factory.name, permission: PermissionType.MANAGE })),
        devices: devices.map(device => ({ id: device.id, name: device.name || device.id, permission: PermissionType.MANAGE })),
      };
    }

    return {
      cities: user.userCityPermissions.map(p => ({
        id: p.city.id,
        name: p.city.name,
        permission: p.permission,
      })),
      factories: user.userFactoryPermissions.map(p => ({
        id: p.factory.id,
        name: p.factory.name,
        permission: p.permission,
      })),
      devices: user.userDevicePermissions.map(p => ({
        id: p.device.id,
        name: p.device.name || p.device.id,
        permission: p.permission,
      })),
    };
  }

  /**
   * Get accessible cities for a user
   */
  static async getAccessibleCities(userId: number): Promise<number[]> {
    const user = await prisma.user.findUnique({
      where: { id: userId },
      include: { userCityPermissions: true },
    });

    if (!user) return [];

    if (user.isSuperuser) {
      const cities = await prisma.city.findMany();
      return cities.map(city => city.id);
    }

    return user.userCityPermissions.map(p => p.cityId);
  }

  /**
   * Get accessible factories for a user
   */
  static async getAccessibleFactories(userId: number): Promise<number[]> {
    const user = await prisma.user.findUnique({
      where: { id: userId },
      include: { userFactoryPermissions: true },
    });

    if (!user) return [];

    if (user.isSuperuser) {
      const factories = await prisma.factory.findMany();
      return factories.map(factory => factory.id);
    }

    return user.userFactoryPermissions.map(p => p.factoryId);
  }

  /**
   * Get accessible devices for a user
   */
  static async getAccessibleDevices(userId: number): Promise<string[]> {
    const user = await prisma.user.findUnique({
      where: { id: userId },
      include: { userDevicePermissions: true },
    });

    if (!user) return [];

    if (user.isSuperuser) {
      const devices = await prisma.device.findMany();
      return devices.map(device => device.id);
    }

    return user.userDevicePermissions.map(p => p.deviceId);
  }

  /**
   * Assign permission to user for a city
   */
  static async assignCityPermission(
    userId: number,
    cityId: number,
    permission: PermissionType
  ): Promise<void> {
    await prisma.userCityPermission.upsert({
      where: {
        userId_cityId: { userId, cityId },
      },
      update: { permission },
      create: {
        userId,
        cityId,
        permission,
      },
    });
  }

  /**
   * Assign permission to user for a factory
   */
  static async assignFactoryPermission(
    userId: number,
    factoryId: number,
    permission: PermissionType
  ): Promise<void> {
    await prisma.userFactoryPermission.upsert({
      where: {
        userId_factoryId: { userId, factoryId },
      },
      update: { permission },
      create: {
        userId,
        factoryId,
        permission,
      },
    });
  }

  /**
   * Assign permission to user for a device
   */
  static async assignDevicePermission(
    userId: number,
    deviceId: string,
    permission: PermissionType
  ): Promise<void> {
    await prisma.userDevicePermission.upsert({
      where: {
        userId_deviceId: { userId, deviceId },
      },
      update: { permission },
      create: {
        userId,
        deviceId,
        permission,
      },
    });
  }

  /**
   * Remove permission from user for a city
   */
  static async removeCityPermission(userId: number, cityId: number): Promise<void> {
    await prisma.userCityPermission.delete({
      where: {
        userId_cityId: { userId, cityId },
      },
    });
  }

  /**
   * Remove permission from user for a factory
   */
  static async removeFactoryPermission(userId: number, factoryId: number): Promise<void> {
    await prisma.userFactoryPermission.delete({
      where: {
        userId_factoryId: { userId, factoryId },
      },
    });
  }

  /**
   * Remove permission from user for a device
   */
  static async removeDevicePermission(userId: number, deviceId: string): Promise<void> {
    await prisma.userDevicePermission.delete({
      where: {
        userId_deviceId: { userId, deviceId },
      },
    });
  }

  /**
   * Check if user has required permission level
   */
  private static hasRequiredPermission(
    userPermission: PermissionType,
    requiredPermission: PermissionType
  ): boolean {
    const permissionHierarchy = {
      [PermissionType.READ]: 1,
      [PermissionType.WRITE]: 2,
      [PermissionType.DELETE]: 3,
      [PermissionType.MANAGE]: 4,
    };

    return permissionHierarchy[userPermission] >= permissionHierarchy[requiredPermission];
  }
} 