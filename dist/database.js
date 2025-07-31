"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.prisma = exports.db = exports.DatabaseService = void 0;
const client_1 = require("@prisma/client");
// Initialize Prisma Client
const prisma = new client_1.PrismaClient();
exports.prisma = prisma;
// Database service class
class DatabaseService {
    constructor() {
        this.prisma = prisma;
    }
    // Patient operations
    async createPatient(data) {
        return await this.prisma.patient.create({
            data,
            include: {
                appointments: {
                    include: {
                        doctor: {
                            include: {
                                specialty: true,
                            },
                        },
                    },
                },
            },
        });
    }
    async getPatientByEmail(email) {
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
    async createDoctor(data) {
        return await this.prisma.doctor.create({
            data,
            include: {
                specialty: true
            }
        });
    }
    async getDoctorsBySpecialty(specialtyId) {
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
    async getAvailabilityByDoctor(doctorId, dayOfWeek) {
        return await this.prisma.doctorAvailability.findUnique({
            where: {
                doctorId_dayOfWeek: {
                    doctorId: doctorId,
                    dayOfWeek: dayOfWeek,
                },
            },
        });
    }
    // Specialty operations
    async createSpecialty(data) {
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
    async createAppointment(data) {
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
    async getAppointmentsByPatient(patientId) {
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
    async getAppointmentsByDoctor(doctorId) {
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
    async updateAppointmentStatus(id, status) {
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
    async getAppointmentsByDoctorForDate(doctorId, date) {
        const startOfDay = new Date(date.setHours(0, 0, 0, 0));
        const endOfDay = new Date(date.setHours(23, 59, 59, 999));
        return await this.prisma.appointment.findMany({
            where: {
                doctorId,
                dateTime: {
                    gte: startOfDay,
                    lte: endOfDay,
                },
            },
            orderBy: {
                dateTime: 'asc',
            },
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
exports.DatabaseService = DatabaseService;
// Export a singleton instance
exports.db = new DatabaseService();
//# sourceMappingURL=database.js.map