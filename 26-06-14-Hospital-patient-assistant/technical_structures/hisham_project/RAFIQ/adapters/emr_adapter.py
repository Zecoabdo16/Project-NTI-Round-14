class EMRAdapter:
    def get_patient_history(self, patient_id: str) -> dict:
        # Later, queries Postgres. Now, hardcode the "CKD Patient" story.
        return {
            "name": "أحمد محمد",
            "chronic_conditions": ["CKD", "Hypertension"],
            "allergies": ["Penicillin"],
            "medications": ["Warfarin"]
        }