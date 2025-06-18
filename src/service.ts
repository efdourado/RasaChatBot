import { db } from './database';
import { Doctor, Patient, Specialty } from '@prisma/client';

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

    case 'getAppointmentsByDoctor':
      const doctorId = parseInt(args[1], 10);
      const date = args[2]; // Formato YYYY-MM-DD
      const appointments = await db.getAppointmentsByDoctorForDate(doctorId, new Date(date));
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