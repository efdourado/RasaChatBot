import { PrismaClient } from '../generated/prisma';

// Initialize Prisma Client
const prisma = new PrismaClient();

// Database service class
export class DatabaseService {
  private prisma: PrismaClient;

  constructor() {
    this.prisma = prisma;
  }

  // Patient operations
  async createPatient(data: {
    name: string;
    email: string;
    phone?: string;
    birthDate?: Date;
  }) {
    return await this.prisma.patient.create({
      data
    });
  }

  async getPatientByEmail(email: string) {
    return await this.prisma.patient.findUnique({
      where: { email },
      include: {
        appointments: {
          include: {
            doctor: {
              include: {
                specialty: true
              }
            }
          }
        }
      }
    });
  }

  async getAllPatients() {
    return await this.prisma.patient.findMany({
      include: {
        appointments: {
          include: {
            doctor: {
              include: {
                specialty: true
              }
            }
          }
        }
      }
    });
  }

  // Doctor operations
  async createDoctor(data: {
    name: string;
    email: string;
    phone?: string;
    specialtyId: number;
  }) {
    return await this.prisma.doctor.create({
      data,
      include: {
        specialty: true
      }
    });
  }

  async getDoctorsBySpecialty(specialtyId: number) {
    return await this.prisma.doctor.findMany({
      where: { specialtyId },
      include: {
        specialty: true
      }
    });
  }

  async getAllDoctors() {
    return await this.prisma.doctor.findMany({
      include: {
        specialty: true,
        appointments: true
      }
    });
  }

  // Specialty operations
  async createSpecialty(data: {
    name: string;
    description?: string;
  }) {
    return await this.prisma.specialty.create({
      data
    });
  }

  async getAllSpecialties() {
    return await this.prisma.specialty.findMany({
      include: {
        doctors: true
      }
    });
  }

  // Appointment operations
  async createAppointment(data: {
    patientId: number;
    doctorId: number;
    dateTime: Date;
    notes?: string;
  }) {
    return await this.prisma.appointment.create({
      data,
      include: {
        patient: true,
        doctor: {
          include: {
            specialty: true
          }
        }
      }
    });
  }

  async getAppointmentsByPatient(patientId: number) {
    return await this.prisma.appointment.findMany({
      where: { patientId },
      include: {
        doctor: {
          include: {
            specialty: true
          }
        }
      },
      orderBy: {
        dateTime: 'asc'
      }
    });
  }

  async getAppointmentsByDoctor(doctorId: number) {
    return await this.prisma.appointment.findMany({
      where: { doctorId },
      include: {
        patient: true
      },
      orderBy: {
        dateTime: 'asc'
      }
    });
  }

  async updateAppointmentStatus(id: number, status: 'SCHEDULED' | 'CONFIRMED' | 'CANCELLED' | 'COMPLETED') {
    return await this.prisma.appointment.update({
      where: { id },
      data: { status },
      include: {
        patient: true,
        doctor: {
          include: {
            specialty: true
          }
        }
      }
    });
  }

  // Utility method to disconnect from database
  async disconnect() {
    await this.prisma.$disconnect();
  }

  // Get Prisma client instance for advanced operations
  getClient() {
    return this.prisma;
  }
}

// Export a singleton instance
export const db = new DatabaseService();

// Export Prisma client for direct access if needed
export { prisma }; 