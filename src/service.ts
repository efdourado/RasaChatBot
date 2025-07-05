import { db } from './database';
import { Doctor, Patient, Specialty } from '@prisma/client';

import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

const printJSON = (data: any) => {
  console.log(JSON.stringify(data, (key, value) => 
    typeof value === 'bigint' ? value.toString() : value
  ));
  process.exit(0);
};

const args = process.argv.slice(2);
const command = args[0];


function generateTimeSlots(start: string, end: string, intervalMinutes: number): string[] {
    const slots = [];
    const [startHour, startMinute] = start.split(':').map(Number);
    const [endHour, endMinute] = end.split(':').map(Number);
    
    let currentTime = new Date();
    currentTime.setHours(startHour, startMinute, 0, 0);

    const endTime = new Date();
    endTime.setHours(endHour, endMinute, 0, 0);

    while (currentTime < endTime) {
        slots.push(currentTime.toTimeString().substring(0, 5));
        currentTime.setMinutes(currentTime.getMinutes() + intervalMinutes);
    }
    return slots;
}


async function main() {
  switch (command) {
    case 'getSpecialties':
      const specialties = await db.getAllSpecialties();
      printJSON(specialties);
      break;

    case 'getDoctorsBySpecialty':
      const specialtyId = parseInt(args[1], 10);
      const doctors = await db.getDoctorsBySpecialty(specialtyId);
      printJSON(doctors);
      break;

    case 'getAppointmentsByDoctorAndDate':
        if (args.length < 2) {
          throw new Error("Doctor ID and Date are required.");
        }
        const doctorId = parseInt(args[0], 10);
        const dateStr = args[1]; // Espera o formato "YYYY-MM-DD"
        
        // Cria o intervalo de data para o dia inteiro
        const startDate = new Date(`${dateStr}T00:00:00.000Z`);
        const endDate = new Date(`${dateStr}T23:59:59.999Z`);

        const appointments = await prisma.appointment.findMany({
            where: {
                doctorId: doctorId,
                dateTime: {
                    gte: startDate, // "greater than or equal to" o início do dia
                    lte: endDate,   // "less than or equal to" o fim do dia
                }
            }
        });
        printJSON(appointments);
        break;
    
    case 'findOrCreatePatient':
      const email = args[1];
      const name = args[2];
      let patient = await db.getPatientByEmail(email);
      if (!patient) {
        patient = await db.createPatient({ email, name });
      }
      printJSON(patient);
      break;

    case 'createAppointment':
      const data = JSON.parse(args[1]);
      const appointment = await db.createAppointment({
        patientId: data.patientId,
        doctorId: data.doctorId,
        dateTime: new Date(data.dateTime),
        notes: `Agendado via Chatbot para ${data.patientName}`
      });
      printJSON(appointment);
      break;

    case 'getAvailableSlotsByDoctorAndDate': {
        if (args.length < 3) {
          throw new Error("Doctor ID and Date are required.");
        }
        const doctorId = parseInt(args[1], 10);
        const dateStr = args[2]; // Formato "YYYY-MM-DD"
        
        const targetDate = new Date(`${dateStr}T12:00:00.000Z`);
        const dayOfWeek = targetDate.getUTCDay();

        // 1. Buscar a disponibilidade do médico para o dia da semana
        const availability = await db.getAvailabilityByDoctor(doctorId, dayOfWeek);

        if (!availability) {
            printJSON([]); // Médico não trabalha neste dia
            return;
        }

        // 2. Gerar todos os horários de trabalho possíveis (a cada 60 min)
        const allPossibleSlots = generateTimeSlots(availability.startTime, availability.endTime, 60);

        // 3. Buscar agendamentos existentes para o médico na data específica
        const appointments = await db.getAppointmentsByDoctorForDate(doctorId, targetDate);
        const bookedSlots = appointments.map(a => a.dateTime.toISOString().substring(11, 16));
        
        // 4. Filtrar e retornar apenas os horários disponíveis
        const availableSlots = allPossibleSlots.filter(slot => !bookedSlots.includes(slot));
        
        printJSON(availableSlots);
        break;
    }

    default:
      console.error('Comando inválido');
      process.exit(1);
} }

main().catch(async (e) => {
  console.error(e);
  await db.disconnect();
  process.exit(1);
});