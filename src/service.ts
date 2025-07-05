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

    default:
      console.error('Comando inválido');
      process.exit(1);
} }

main().catch(async (e) => {
  console.error(e);
  await db.disconnect();
  process.exit(1);
});