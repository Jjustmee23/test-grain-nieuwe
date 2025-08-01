// Shared types between frontend and backend
export interface User {
  id: number;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  isStaff: boolean;
  isActive: boolean;
  isSuperuser: boolean;
  dateJoined: string;
  lastLogin?: string;
  userProfile?: UserProfile;
}

export interface UserProfile {
  id: number;
  team?: string;
  supportTicketsEnabled: boolean;
  allowedCities: City[];
  allowedFactories: Factory[];
}

export interface City {
  id: number;
  name: string;
  status: boolean;
  createdAt: string;
}

export interface Factory {
  id: number;
  name: string;
  status: boolean;
  error: boolean;
  group: 'government' | 'private' | 'commercial';
  address?: string;
  latitude?: number;
  longitude?: number;
  createdAt: string;
  city?: City;
  cityId?: number;
  devices?: Device[];
  batches?: Batch[];
  responsibleUsers?: User[];
}

export interface Device {
  id: string;
  name: string;
  serialNumber?: string;
  selectedCounter: string;
  status: boolean;
  createdAt: string;
  factory?: Factory;
  factoryId?: number;
  productionData?: ProductionData[];
  powerStatus?: DevicePowerStatus;
  doorStatus?: DoorStatus;
}

export interface ProductionData {
  id: number;
  dailyProduction: number;
  weeklyProduction: number;
  monthlyProduction: number;
  yearlyProduction: number;
  createdAt: string;
  updatedAt: string;
  deviceId: string;
  device?: Device;
}

export interface Batch {
  id: number;
  batchNumber: string;
  wheatAmount: number;
  wasteFactor: number;
  expectedFlourOutput: number;
  actualFlourOutput: number;
  startDate: string;
  endDate?: string;
  startValue: number;
  currentValue: number;
  status: 'pending' | 'approved' | 'in_process' | 'paused' | 'stopped' | 'completed' | 'rejected';
  isCompleted: boolean;
  approvedAt?: string;
  createdAt: string;
  updatedAt: string;
  factoryId?: number;
  approvedById?: number;
  factory?: Factory;
  approvedBy?: User;
  alerts?: Alert[];
  flourBagCounts?: FlourBagCount[];
}

export interface BatchTemplate {
  id: number;
  name: string;
  description?: string;
  wheatAmount: number;
  wasteFactor: number;
  expectedDurationDays: number;
  isActive: boolean;
  isDefault: boolean;
  createdAt: string;
  updatedAt: string;
  createdById?: number;
  createdBy?: User;
  applicableFactories?: Factory[];
}

export interface Alert {
  id: number;
  alertType: 'PRODUCTION_LOW' | 'DEVIATION' | 'SYSTEM';
  severity: 'LOW' | 'MEDIUM' | 'HIGH';
  message: string;
  isActive: boolean;
  isAcknowledged: boolean;
  createdAt: string;
  updatedAt: string;
  batchId: number;
  acknowledgedById?: number;
  batch?: Batch;
  acknowledgedBy?: User;
}

export interface PowerEvent {
  id: number;
  eventType: 'power_loss' | 'power_restored' | 'production_without_power' | 'power_fluctuation' | 'battery_low' | 'power_surge';
  severity: 'low' | 'medium' | 'high' | 'critical';
  ain1Value?: number;
  previousAin1Value?: number;
  message: string;
  isResolved: boolean;
  resolvedAt?: string;
  resolutionNotes?: string;
  notificationSent: boolean;
  emailSent: boolean;
  superAdminNotified: boolean;
  createdAt: string;
  updatedAt: string;
  deviceId: string;
  resolvedById?: number;
  device?: Device;
  resolvedBy?: User;
}

export interface DevicePowerStatus {
  id: number;
  hasPower: boolean;
  ain1Value?: number;
  lastPowerCheck: string;
  powerThreshold: number;
  powerLossDetectedAt?: string;
  powerRestoredAt?: string;
  productionDuringPowerLoss: boolean;
  lastProductionCheck?: string;
  notifyOnPowerLoss: boolean;
  notifyOnPowerRestore: boolean;
  notifyOnProductionWithoutPower: boolean;
  createdAt: string;
  updatedAt: string;
  deviceId: string;
  device?: Device;
}

export interface DoorStatus {
  id: number;
  isOpen: boolean;
  lastDinData?: string;
  lastCheck: string;
  doorInputIndex: number;
  createdAt: string;
  updatedAt: string;
  deviceId: string;
  device?: Device;
}

export interface Notification {
  id: number;
  title: string;
  message: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'pending' | 'sent' | 'failed' | 'cancelled';
  sentInApp: boolean;
  sentEmail: boolean;
  emailSentAt?: string;
  emailError?: string;
  read: boolean;
  readAt?: string;
  link?: string;
  createdAt: string;
  updatedAt: string;
  userId: number;
  categoryId: number;
  relatedBatchId?: number;
  relatedFactoryId?: number;
  relatedDeviceId?: string;
  user?: User;
  category?: NotificationCategory;
  relatedBatch?: Batch;
  relatedFactory?: Factory;
  relatedDevice?: Device;
}

export interface NotificationCategory {
  id: number;
  name: string;
  description: string;
  notificationType: string;
  isActive: boolean;
  requiresAdmin: boolean;
  requiresSuperAdmin: boolean;
}

export interface ContactTicket {
  id: number;
  name: string;
  email: string;
  phone?: string;
  ticketType: 'TECHNICAL' | 'ACCOUNT' | 'FEATURE' | 'BUG' | 'OTHER';
  subject: string;
  message: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
  status: 'NEW' | 'IN_PROGRESS' | 'PENDING' | 'RESOLVED' | 'CLOSED';
  createdAt: string;
  updatedAt: string;
  factoryId?: number;
  createdById?: number;
  assignedToId?: number;
  factory?: Factory;
  createdBy?: User;
  assignedTo?: User;
  responses?: TicketResponse[];
}

export interface TicketResponse {
  id: number;
  message: string;
  isInternal: boolean;
  isRead: boolean;
  createdAt: string;
  updatedAt: string;
  ticketId: number;
  createdById?: number;
  ticket?: ContactTicket;
  createdBy?: User;
}

export interface RawData {
  id: number;
  timestamp?: string;
  mobileSignal?: number;
  doutEnabled?: string;
  dout?: string;
  diMode?: string;
  din?: string;
  counter1?: number;
  counter2?: number;
  counter3?: number;
  counter4?: number;
  ainMode?: string;
  ain1Value?: number;
  ain2Value?: number;
  ain3Value?: number;
  ain4Value?: number;
  ain5Value?: number;
  ain6Value?: number;
  ain7Value?: number;
  ain8Value?: number;
  startFlag?: number;
  dataType?: number;
  length?: number;
  version?: number;
  endFlag?: number;
  deviceId: string;
  device?: Device;
}

export interface FlourBagCount {
  id: number;
  bagCount: number;
  bagsWeight: number;
  timestamp: string;
  batchId: number;
  deviceId: string;
  createdById?: number;
  batch?: Batch;
  device?: Device;
  createdBy?: User;
}

// API Response Types
export interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  error?: string;
  status: number;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

export interface LoginRequest {
  username: string;
  password: string;
  remember?: boolean;
}

export interface LoginResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface RefreshTokenRequest {
  refreshToken: string;
}

export interface ChangePasswordRequest {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

// Analytics Types
export interface ProductionAnalytics {
  totalProduction: number;
  dailyAverage: number;
  weeklyAverage: number;
  monthlyAverage: number;
  yearlyTotal: number;
  efficiency: number;
  trends: ProductionTrend[];
}

export interface ProductionTrend {
  date: string;
  production: number;
  efficiency?: number;
  deviceCount?: number;
}

export interface FactoryAnalytics {
  factoryId: number;
  factoryName: string;
  totalProduction: number;
  activeDevices: number;
  totalDevices: number;
  activeBatches: number;
  completedBatches: number;
  efficiency: number;
  powerStatus: {
    onlineDevices: number;
    offlineDevices: number;
    powerEvents: number;
  };
}

export interface DashboardStats {
  totalFactories: number;
  activeFactories: number;
  totalDevices: number;
  onlineDevices: number;
  activeBatches: number;
  completedBatches: number;
  totalProduction: number;
  powerEvents: number;
  unreadNotifications: number;
  openTickets: number;
}

// WebSocket Event Types
export interface WebSocketEvent<T = any> {
  type: string;
  data: T;
  timestamp: string;
  userId?: number;
  factoryId?: number;
  deviceId?: string;
}

export interface DeviceDataEvent {
  deviceId: string;
  data: RawData;
  timestamp: string;
}

export interface PowerEventWebSocket {
  deviceId: string;
  eventType: 'power_restored' | 'power_loss';
  ain1Value: number;
  timestamp: string;
}

export interface DoorStatusChangeEvent {
  deviceId: string;
  isOpen: boolean;
  timestamp: string;
}

export interface BatchUpdateEvent {
  batchId: number;
  status: string;
  progress?: number;
  timestamp: string;
}

// Filter and Search Types
export interface FactoryFilter {
  cityId?: number;
  group?: 'government' | 'private' | 'commercial';
  status?: boolean;
  search?: string;
}

export interface DeviceFilter {
  factoryId?: number;
  status?: boolean;
  hasData?: boolean;
  search?: string;
}

export interface BatchFilter {
  factoryId?: number;
  status?: Batch['status'];
  dateRange?: {
    start: string;
    end: string;
  };
  search?: string;
}

export interface NotificationFilter {
  read?: boolean;
  priority?: Notification['priority'];
  categoryId?: number;
  dateRange?: {
    start: string;
    end: string;
  };
}

// Form Types
export interface CreateFactoryForm {
  name: string;
  cityId: number;
  group: 'government' | 'private' | 'commercial';
  address?: string;
  latitude?: number;
  longitude?: number;
  responsibleUserIds?: number[];
}

export interface CreateDeviceForm {
  id: string;
  name: string;
  serialNumber?: string;
  selectedCounter: string;
  factoryId: number;
}

export interface CreateBatchForm {
  batchNumber: string;
  factoryId: number;
  wheatAmount: number;
  wasteFactor: number;
  templateId?: number;
}

export interface UpdateBatchForm {
  wheatAmount?: number;
  wasteFactor?: number;
  actualFlourOutput?: number;
  status?: Batch['status'];
}

// Theme and UI Types
export interface ThemeConfig {
  mode: 'light' | 'dark';
  primaryColor: string;
  secondaryColor: string;
  direction: 'ltr' | 'rtl';
}

export interface MenuItem {
  id: string;
  label: string;
  icon?: string;
  path?: string;
  children?: MenuItem[];
  permissions?: string[];
  badge?: number;
}

// Error Types
export interface ValidationError {
  field: string;
  message: string;
  value?: any;
}

export interface ApiError {
  message: string;
  status: number;
  details?: any;
  errors?: ValidationError[];
  timestamp: string;
  path?: string;
  method?: string;
} 