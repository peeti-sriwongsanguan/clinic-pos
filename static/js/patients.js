class PatientManager {
    constructor() {
        this.searchTimeout = null;
    }

    async searchPatients(query) {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(async () => {
            try {
                const response = await fetch(`/api/patients/search?q=${query}`);
                const patients = await response.json();
                this.displaySearchResults(patients);
            } catch (error) {
                console.error('Error searching patients:', error);
            }
        }, 300);
    }

    displaySearchResults(patients) {
        // Display logic here
    }
}