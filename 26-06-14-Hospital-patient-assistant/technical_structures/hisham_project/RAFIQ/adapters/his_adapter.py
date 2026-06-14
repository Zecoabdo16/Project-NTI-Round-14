class HISAdapter:
    def check_availability(self, doctor_id: str, date: str) -> dict:
        # In Week 3, this will query PostgreSQL. For now, return mock.
        return {"available_slots": ["10:00 AM", "02:30 PM"], "doctor_name": "Dr. Tarek"}

    def book_appointment(self, patient_id: str, slot: str) -> dict:
        return {"status": "success", "booking_id": "APT-9921"}