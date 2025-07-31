import { PrismaClient } from '@prisma/client';
declare const prisma: PrismaClient<import(".prisma/client").Prisma.PrismaClientOptions, never, import("@prisma/client/runtime/library").DefaultArgs>;
export declare class DatabaseService {
    private prisma;
    constructor();
    createPatient(data: {
        email: string;
        name: string;
    }): Promise<{
        appointments: ({
            doctor: {
                specialty: {
                    id: number;
                    name: string;
                    createdAt: Date;
                    description: string | null;
                };
            } & {
                id: number;
                name: string;
                email: string;
                phone: string | null;
                createdAt: Date;
                updatedAt: Date;
                specialtyId: number;
            };
        } & {
            id: number;
            createdAt: Date;
            updatedAt: Date;
            doctorId: number;
            patientId: number;
            dateTime: Date;
            status: string;
            notes: string | null;
        })[];
    } & {
        id: number;
        name: string;
        email: string;
        phone: string | null;
        birthDate: Date | null;
        createdAt: Date;
        updatedAt: Date;
    }>;
    getPatientByEmail(email: string): Promise<({
        appointments: ({
            doctor: {
                specialty: {
                    id: number;
                    name: string;
                    createdAt: Date;
                    description: string | null;
                };
            } & {
                id: number;
                name: string;
                email: string;
                phone: string | null;
                createdAt: Date;
                updatedAt: Date;
                specialtyId: number;
            };
        } & {
            id: number;
            createdAt: Date;
            updatedAt: Date;
            doctorId: number;
            patientId: number;
            dateTime: Date;
            status: string;
            notes: string | null;
        })[];
    } & {
        id: number;
        name: string;
        email: string;
        phone: string | null;
        birthDate: Date | null;
        createdAt: Date;
        updatedAt: Date;
    }) | null>;
    getAllPatients(): Promise<({
        appointments: ({
            doctor: {
                specialty: {
                    id: number;
                    name: string;
                    createdAt: Date;
                    description: string | null;
                };
            } & {
                id: number;
                name: string;
                email: string;
                phone: string | null;
                createdAt: Date;
                updatedAt: Date;
                specialtyId: number;
            };
        } & {
            id: number;
            createdAt: Date;
            updatedAt: Date;
            doctorId: number;
            patientId: number;
            dateTime: Date;
            status: string;
            notes: string | null;
        })[];
    } & {
        id: number;
        name: string;
        email: string;
        phone: string | null;
        birthDate: Date | null;
        createdAt: Date;
        updatedAt: Date;
    })[]>;
    createDoctor(data: {
        name: string;
        email: string;
        phone?: string;
        specialtyId: number;
    }): Promise<{
        specialty: {
            id: number;
            name: string;
            createdAt: Date;
            description: string | null;
        };
    } & {
        id: number;
        name: string;
        email: string;
        phone: string | null;
        createdAt: Date;
        updatedAt: Date;
        specialtyId: number;
    }>;
    getDoctorsBySpecialty(specialtyId: number): Promise<({
        specialty: {
            id: number;
            name: string;
            createdAt: Date;
            description: string | null;
        };
    } & {
        id: number;
        name: string;
        email: string;
        phone: string | null;
        createdAt: Date;
        updatedAt: Date;
        specialtyId: number;
    })[]>;
    getAllDoctors(): Promise<({
        appointments: {
            id: number;
            createdAt: Date;
            updatedAt: Date;
            doctorId: number;
            patientId: number;
            dateTime: Date;
            status: string;
            notes: string | null;
        }[];
        specialty: {
            id: number;
            name: string;
            createdAt: Date;
            description: string | null;
        };
    } & {
        id: number;
        name: string;
        email: string;
        phone: string | null;
        createdAt: Date;
        updatedAt: Date;
        specialtyId: number;
    })[]>;
    getAvailabilityByDoctor(doctorId: number, dayOfWeek: number): Promise<{
        id: number;
        dayOfWeek: number;
        startTime: string;
        endTime: string;
        doctorId: number;
    } | null>;
    createSpecialty(data: {
        name: string;
        description?: string;
    }): Promise<{
        id: number;
        name: string;
        createdAt: Date;
        description: string | null;
    }>;
    getAllSpecialties(): Promise<({
        doctors: {
            id: number;
            name: string;
            email: string;
            phone: string | null;
            createdAt: Date;
            updatedAt: Date;
            specialtyId: number;
        }[];
    } & {
        id: number;
        name: string;
        createdAt: Date;
        description: string | null;
    })[]>;
    createAppointment(data: {
        patientId: number;
        doctorId: number;
        dateTime: Date;
        notes?: string;
    }): Promise<{
        patient: {
            id: number;
            name: string;
            email: string;
            phone: string | null;
            birthDate: Date | null;
            createdAt: Date;
            updatedAt: Date;
        };
        doctor: {
            specialty: {
                id: number;
                name: string;
                createdAt: Date;
                description: string | null;
            };
        } & {
            id: number;
            name: string;
            email: string;
            phone: string | null;
            createdAt: Date;
            updatedAt: Date;
            specialtyId: number;
        };
    } & {
        id: number;
        createdAt: Date;
        updatedAt: Date;
        doctorId: number;
        patientId: number;
        dateTime: Date;
        status: string;
        notes: string | null;
    }>;
    getAppointmentsByPatient(patientId: number): Promise<({
        doctor: {
            specialty: {
                id: number;
                name: string;
                createdAt: Date;
                description: string | null;
            };
        } & {
            id: number;
            name: string;
            email: string;
            phone: string | null;
            createdAt: Date;
            updatedAt: Date;
            specialtyId: number;
        };
    } & {
        id: number;
        createdAt: Date;
        updatedAt: Date;
        doctorId: number;
        patientId: number;
        dateTime: Date;
        status: string;
        notes: string | null;
    })[]>;
    getAppointmentsByDoctor(doctorId: number): Promise<({
        patient: {
            id: number;
            name: string;
            email: string;
            phone: string | null;
            birthDate: Date | null;
            createdAt: Date;
            updatedAt: Date;
        };
    } & {
        id: number;
        createdAt: Date;
        updatedAt: Date;
        doctorId: number;
        patientId: number;
        dateTime: Date;
        status: string;
        notes: string | null;
    })[]>;
    updateAppointmentStatus(id: number, status: 'SCHEDULED' | 'CONFIRMED' | 'CANCELLED' | 'COMPLETED'): Promise<{
        patient: {
            id: number;
            name: string;
            email: string;
            phone: string | null;
            birthDate: Date | null;
            createdAt: Date;
            updatedAt: Date;
        };
        doctor: {
            specialty: {
                id: number;
                name: string;
                createdAt: Date;
                description: string | null;
            };
        } & {
            id: number;
            name: string;
            email: string;
            phone: string | null;
            createdAt: Date;
            updatedAt: Date;
            specialtyId: number;
        };
    } & {
        id: number;
        createdAt: Date;
        updatedAt: Date;
        doctorId: number;
        patientId: number;
        dateTime: Date;
        status: string;
        notes: string | null;
    }>;
    getAppointmentsByDoctorForDate(doctorId: number, date: Date): Promise<{
        id: number;
        createdAt: Date;
        updatedAt: Date;
        doctorId: number;
        patientId: number;
        dateTime: Date;
        status: string;
        notes: string | null;
    }[]>;
    disconnect(): Promise<void>;
    getClient(): PrismaClient<import(".prisma/client").Prisma.PrismaClientOptions, never, import("@prisma/client/runtime/library").DefaultArgs>;
}
export declare const db: DatabaseService;
export { prisma };
//# sourceMappingURL=database.d.ts.map