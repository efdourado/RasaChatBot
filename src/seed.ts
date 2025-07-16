import { db } from './database';

async function main() {
  console.log('🌱 Starting database seeding...');

  // Clear existing data
  console.log('🧹 Clearing existing data...');
  const prisma = db.getClient();
  
  await prisma.appointment.deleteMany();
  
  await prisma.doctorAvailability.deleteMany();

  await prisma.doctor.deleteMany();
  await prisma.patient.deleteMany();
  await prisma.specialty.deleteMany();
  
  console.log('✅ Database cleared');

  // Create specialties
  const cardiology = await db.createSpecialty({
    name: 'Cardiologia',
    description: 'Especialidade médica que trata do coração e sistema cardiovascular'
  });

  const dermatology = await db.createSpecialty({
    name: 'Dermatologia',
    description: 'Especialidade médica que trata da pele e seus anexos'
  });

  const orthopedics = await db.createSpecialty({
    name: 'Ortopedia',
    description: 'Especialidade médica que trata dos ossos, músculos e articulações'
  });

  const pediatrics = await db.createSpecialty({
    name: 'Pediatria',
    description: 'Especialidade médica que trata da saúde de crianças e adolescentes'
  });

  const generalClinic = await db.createSpecialty({
    name: 'Clínica Geral',
    description: 'Especialidade médica que trata de cuidados primários de saúde'
  });

  console.log('✅ Specialties created');

  // Create doctors
  const drSilva = await db.createDoctor({
    name: 'Dr. João Silva',
    email: 'joao.silva@supersaudavel.com',
    // phone: '(11) 99999-1111',
    specialtyId: cardiology.id
  });

  const drSantos = await db.createDoctor({
    name: 'Dra. Maria Santos',
    email: 'maria.santos@supersaudavel.com',
    // phone: '(11) 99999-2222',
    specialtyId: dermatology.id
  });

  const drOliveira = await db.createDoctor({
    name: 'Dr. Carlos Oliveira',
    email: 'carlos.oliveira@supersaudavel.com',
    // phone: '(11) 99999-3333',
    specialtyId: orthopedics.id
  });

  const drFernandes = await db.createDoctor({
    name: 'Dra. Ana Fernandes',
    email: 'ana.fernandes@supersaudavel.com',
    phone: '(11) 99999-4444',
    specialtyId: pediatrics.id
  });

  const drSousa = await db.createDoctor({
    name: 'Dr. João Sousa',
    email: 'joao.sousa@supersaudavel.com',
    phone: '(11) 99999-5555',
    specialtyId: generalClinic.id
  });

  console.log('✅ Doctors created');

  console.log('⏰ Creating doctor availabilities...');
  await prisma.doctorAvailability.createMany({
    data: [
      // Dr. João Silva (Cardiologista) - Seg/Qua/Sex das 09:00 às 17:00
      { doctorId: drSilva.id, dayOfWeek: 1, startTime: '09:00', endTime: '17:00' }, // Segunda
      { doctorId: drSilva.id, dayOfWeek: 3, startTime: '09:00', endTime: '17:00' }, // Quarta
      { doctorId: drSilva.id, dayOfWeek: 5, startTime: '09:00', endTime: '17:00' }, // Sexta

      // Dra. Maria Santos (Dermatologista) - Ter/Qui das 10:00 às 18:00
      { doctorId: drSantos.id, dayOfWeek: 2, startTime: '10:00', endTime: '18:00' }, // Terça
      { doctorId: drSantos.id, dayOfWeek: 4, startTime: '10:00', endTime: '18:00' }, // Quinta
    ]
  });
  console.log('✅ Availabilities created');

  // Create sample patients
  const patient1 = await db.createPatient({
    name: 'José da Silva',
    email: 'jose.silva@email.com',
    // phone: '(11) 88888-1111',
    // birthDate: new Date('1985-03-15')
  });

  const patient2 = await db.createPatient({
    name: 'Maria Oliveira',
    email: 'maria.oliveira@email.com',
    // phone: '(11) 88888-2222',
    // birthDate: new Date('1990-07-22')
  });

  const patient3 = await db.createPatient({
    name: 'Carlos Santos',
    email: 'carlos.santos@email.com',
    // phone: '(11) 88888-3333',
    // birthDate: new Date('1978-11-05')
  });

  console.log('✅ Patients created');

  // Create sample appointments
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  tomorrow.setHours(9, 0, 0, 0);

  const nextWeek = new Date();
  nextWeek.setDate(nextWeek.getDate() + 7);
  nextWeek.setHours(14, 30, 0, 0);

  const appointment1 = await db.createAppointment({
    patientId: patient1.id,
    doctorId: drSilva.id,
    dateTime: tomorrow,
    notes: 'Consulta de rotina - cardiologia'
  });

  const appointment2 = await db.createAppointment({
    patientId: patient2.id,
    doctorId: drSantos.id,
    dateTime: nextWeek,
    notes: 'Avaliação dermatológica'
  });

  console.log('✅ Appointments created');

  console.log('\n🎉 Database seeding completed successfully!');
  
  // Display summary
  const specialties = await db.getAllSpecialties();
  const doctors = await db.getAllDoctors();
  const patients = await db.getAllPatients();
  
  console.log(`\n📊 Summary:`);
  console.log(`   - ${specialties.length} specialties`);
  console.log(`   - ${doctors.length} doctors`);
  console.log(`   - ${patients.length} patients`);
  console.log(`   - 2 appointments scheduled`);
}

main()
  .catch((e) => {
    console.error('❌ Error during seeding:', e);
    process.exit(1);
  })
  .finally(async () => {
    await db.disconnect();
  }); 