# Database Setup with Prisma

This project now includes a working database using Prisma ORM with SQLite. The database is designed to support the clinic appointment chatbot functionality.

## 🗄️ Database Schema

The database includes the following models:

### Patient
- Patient information (name, email, phone, birth date)
- Relationship with appointments

### Doctor  
- Doctor information (name, email, phone)
- Linked to a medical specialty
- Relationship with appointments

### Specialty
- Medical specialties (Cardiologia, Dermatologia, etc.)
- Relationship with doctors

### Appointment
- Appointment scheduling between patients and doctors
- Status tracking (SCHEDULED, CONFIRMED, CANCELLED, COMPLETED)
- Date/time and notes

## 🚀 Getting Started

### Prerequisites
- Node.js installed
- npm or yarn

### Installation
The database is already set up! If you need to reinstall:

```bash
npm install
npm run prisma:generate
```

### Database Operations

#### Seed the database with sample data:
```bash
npm run seed
```

#### View database in Prisma Studio:
```bash
npm run prisma:studio
```

#### Reset database (removes all data):
```bash
npm run prisma:reset
```

#### Run example queries:
```bash
ts-node src/example.ts
```

## 📁 File Structure

```
├── prisma/
│   ├── schema.prisma          # Database schema definition
│   └── migrations/            # Database migration files
├── src/
│   ├── database.ts           # Database service with CRUD operations
│   ├── seed.ts               # Database seeding script
│   └── example.ts            # Usage examples
├── generated/
│   └── prisma/               # Generated Prisma client
└── dev.db                    # SQLite database file
```

## 🔧 Usage Examples

### Import the database service:
```typescript
import { db } from './src/database';
```

### Basic Operations:

#### Create a new patient:
```typescript
const patient = await db.createPatient({
  name: 'João Silva',
  email: 'joao@email.com',
  phone: '(11) 99999-9999'
});
```

#### Find patient by email:
```typescript
const patient = await db.getPatientByEmail('joao@email.com');
```

#### Get all doctors by specialty:
```typescript
const cardiologists = await db.getDoctorsBySpecialty(1); // specialty ID
```

#### Create an appointment:
```typescript
const appointment = await db.createAppointment({
  patientId: 1,
  doctorId: 1,
  dateTime: new Date('2024-12-15T10:00:00'),
  notes: 'Regular checkup'
});
```

#### Update appointment status:
```typescript
const updatedAppointment = await db.updateAppointmentStatus(1, 'CONFIRMED');
```

## 🎯 Integration with Rasa Chatbot

You can integrate this database with your Rasa chatbot by:

1. **Custom Actions**: Use the database service in your Rasa custom actions
2. **Patient Management**: Store and retrieve patient information
3. **Appointment Booking**: Handle appointment creation and management
4. **Doctor Lookup**: Find available doctors by specialty
5. **Schedule Management**: Check availability and manage appointments

### Example Rasa Integration:

```python
# In your actions.py file
import subprocess
import json

class ActionBookAppointment(Action):
    def name(self) -> Text:
        return "action_book_appointment"
    
    def run(self, dispatcher, tracker, domain):
        # Call your TypeScript database service
        result = subprocess.run([
            'ts-node', 
            'src/appointment-service.ts',
            '--patient-email', tracker.get_slot('email'),
            '--doctor-id', tracker.get_slot('doctor_id'),
            '--datetime', tracker.get_slot('appointment_date')
        ], capture_output=True, text=True)
        
        # Process result and respond
        if result.returncode == 0:
            dispatcher.utter_message("Appointment booked successfully!")
        else:
            dispatcher.utter_message("Sorry, there was an error booking your appointment.")
```

## 🛠️ Available Scripts

- `npm run build` - Compile TypeScript to JavaScript
- `npm run seed` - Populate database with sample data
- `npm run prisma:studio` - Open Prisma Studio (database GUI)
- `npm run prisma:generate` - Generate Prisma client
- `npm run prisma:migrate` - Run database migrations
- `npm run prisma:reset` - Reset database and run migrations

## 📊 Sample Data

The database is seeded with:
- 4 medical specialties (Cardiologia, Dermatologia, Ortopedia, Pediatria)
- 4 doctors (one for each specialty)
- 3 sample patients
- 2 scheduled appointments

## 🔒 Environment Variables

The database connection is configured in `.env`:
```
DATABASE_URL="file:./dev.db"
```

For production, you can switch to PostgreSQL or MySQL by updating the datasource in `prisma/schema.prisma` and the `DATABASE_URL`.

## 📝 Database Schema Visualization

```
Patient (1) ←→ (N) Appointment (N) ←→ (1) Doctor (N) ←→ (1) Specialty
```

## 🚨 Important Notes

- The SQLite database file (`dev.db`) should not be committed to version control in production
- For production use, consider using PostgreSQL or MySQL
- Always run `prisma generate` after modifying the schema
- Use migrations for schema changes: `prisma migrate dev --name description`

## 🆘 Troubleshooting

### Common Issues:

1. **"Client not generated"**: Run `npm run prisma:generate`
2. **"Database not found"**: Run `npm run prisma:migrate`
3. **"TypeScript errors"**: Run `npm run build` to check compilation
4. **"Seed script fails"**: Ensure database is migrated first

### Reset Everything:
```bash
npm run prisma:reset
npm run seed
```

This will recreate the database from scratch with sample data. 