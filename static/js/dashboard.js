// Dashboard page logic
Auth.requireAdmin();

// Load all statistics
async function loadStatistics() {
    try {
        showLoading(true);
        
        const [buildings, rooms, courses, instructors, tas, levels] = await Promise.all([
            API.get(Endpoints.buildings),
            API.get(Endpoints.rooms),
            API.get(Endpoints.courses),
            API.get(Endpoints.instructors),
            API.get(Endpoints.tas),
            API.get(Endpoints.levels)
        ]);

        document.getElementById('stat-buildings').textContent = buildings.length;
        document.getElementById('stat-rooms').textContent = rooms.length;
        document.getElementById('stat-courses').textContent = courses.length;
        document.getElementById('stat-instructors').textContent = instructors.length;
        document.getElementById('stat-tas').textContent = tas.length;
        document.getElementById('stat-levels').textContent = levels.length;
    } catch (error) {
        showNotification('Failed to load statistics: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadStatistics();
});
