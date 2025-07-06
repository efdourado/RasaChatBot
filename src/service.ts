import express from 'express';
import { db } from './database';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();
const app = express();
// A porta será fornecida pelo Render, ou 3000 como padrão
const port = process.env.PORT || 3000;

app.use(express.json());

// Função auxiliar para serializar BigInt, evitando erros no JSON
(BigInt.prototype as any).toJSON = function () {
    return this.toString();
};

// --- Funções Auxiliares ---
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

// --- Rotas da API ---

// Rota para Health Check do Render
app.get('/', (req, res) => {
  res.status(200).send('API do Chatbot DB está saudável!');
});

// GET /specialties - Retorna todas as especialidades
app.get('/specialties', async (req, res, next) => {
    try {
        const specialties = await db.getAllSpecialties();
        res.json(specialties);
    } catch (error) {
        next(error);
    }
});

// GET /doctors/specialty/:specialtyId - Retorna médicos por ID da especialidade
app.get('/doctors/specialty/:specialtyId', async (req, res, next) => {
    try {
        const specialtyId = parseInt(req.params.specialtyId, 10);
        if (isNaN(specialtyId)) {
            return res.status(400).json({ error: 'ID da especialidade inválido.' });
        }
        const doctors = await db.getDoctorsBySpecialty(specialtyId);
        res.json(doctors);
    } catch (error) {
        next(error);
    }
});

// GET /doctors/:doctorId/available-slots?date=YYYY-MM-DD - Retorna horários livres
app.get('/doctors/:doctorId/available-slots', async (req, res, next) => {
    try {
        const doctorId = parseInt(req.params.doctorId, 10);
        const dateStr = req.query.date as string;

        if (isNaN(doctorId)) {
            return res.status(400).json({ error: 'ID do médico inválido.' });
        }
        if (!dateStr || !/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
            return res.status(400).json({ error: 'Parâmetro de data é obrigatório no formato YYYY-MM-DD.' });
        }

        const targetDate = new Date(`${dateStr}T12:00:00.000Z`);
        const dayOfWeek = targetDate.getUTCDay();

        const availability = await db.getAvailabilityByDoctor(doctorId, dayOfWeek);
        if (!availability) {
            return res.json([]); // Médico não trabalha neste dia
        }

        const allPossibleSlots = generateTimeSlots(availability.startTime, availability.endTime, 60);
        const appointments = await db.getAppointmentsByDoctorForDate(doctorId, targetDate);
        const bookedSlots = appointments.map(a => a.dateTime.toISOString().substring(11, 16));
        const availableSlots = allPossibleSlots.filter(slot => !bookedSlots.includes(slot));
        
        res.json(availableSlots);
    } catch (error) {
        next(error);
    }
});

// POST /patients - Encontra ou cria um paciente
app.post('/patients', async (req, res, next) => {
    try {
        const { email, name } = req.body;
        if (!email || !name) {
            return res.status(400).json({ error: 'Email e nome são obrigatórios.' });
        }
        let patient = await db.getPatientByEmail(email);
        if (!patient) {
            patient = await db.createPatient({ email, name });
        }
        res.status(patient ? 200 : 201).json(patient);
    } catch (error) {
        next(error);
    }
});

// POST /appointments - Cria um novo agendamento
app.post('/appointments', async (req, res, next) => {
    try {
        const data = req.body;
        const appointment = await db.createAppointment({
            patientId: data.patientId,
            doctorId: data.doctorId,
            dateTime: new Date(data.dateTime)
        });
        res.status(201).json(appointment);
    } catch (error) {
        next(error);
    }
});

// Middleware para tratamento de erros
app.use((err: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
    console.error(err.stack);
    res.status(500).json({ error: 'Ocorreu um erro interno no servidor.' });
});

// Inicia o servidor
app.listen(port, () => {
    console.log(`Servidor da API rodando na porta ${port}`);
});