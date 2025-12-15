// API client wrapper
class API {
    static BASE_URL = '/api';

    static async request(endpoint, options = {}) {
        const token = Auth.getToken();
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        // Remove Content-Type for FormData
        if (options.body instanceof FormData) {
            delete headers['Content-Type'];
        }

        const config = {
            ...options,
            headers
        };

        const fullUrl = `${this.BASE_URL}${endpoint}`;
        console.log(`[API.request] ${options.method || 'GET'} ${fullUrl}`);

        const response = await fetch(fullUrl, config);

        // Handle 401 Unauthorized
        if (response.status === 401) {
            console.error('[API.request] 401 Unauthorized - logging out');
            Auth.logout();
            throw new Error('Session expired. Please login again.');
        }

        // Handle errors
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Request failed' }));
            console.error('[API.request] Error:', {
                status: response.status,
                endpoint: fullUrl,
                error: error
            });
            
            // Handle validation errors from FastAPI
            if (error.detail && Array.isArray(error.detail)) {
                const messages = error.detail.map(err => {
                    const field = err.loc ? err.loc[err.loc.length - 1] : 'field';
                    return `${field}: ${err.msg}`;
                }).join(', ');
                throw new Error(messages);
            }
            
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        // Handle 204 No Content (successful delete)
        if (response.status === 204) {
            console.log('[API.request] Success (204 No Content):', fullUrl);
            return null;
        }

        // Handle responses with JSON content
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }

        // Handle other successful responses with no content
        console.log('[API.request] Success (no content):', fullUrl);
        return null;
    }

    static async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    static async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    static async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    static async delete(endpoint) {
        console.log('[API.delete] Called with endpoint:', endpoint);
        const result = await this.request(endpoint, { method: 'DELETE' });
        console.log('[API.delete] Success for endpoint:', endpoint);
        return result;
    }

    static async uploadFile(endpoint, file, additionalData = {}) {
        const formData = new FormData();
        formData.append('file', file);
        
        for (const [key, value] of Object.entries(additionalData)) {
            formData.append(key, value);
        }

        return this.request(endpoint, {
            method: 'POST',
            body: formData
        });
    }

    static async downloadFile(endpoint, filename) {
        const token = Auth.getToken();
        const headers = {};
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${this.BASE_URL}${endpoint}`, { headers });
        
        if (!response.ok) {
            throw new Error('Download failed');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }
}

// API endpoints organized by resource
const Endpoints = {
    // Auth
    login: '/auth/login',
    me: '/auth/me',

    // Buildings
    buildings: '/buildings',
    building: (id) => `/buildings/${id}`,

    // Halls
    halls: '/halls',
    hall: (id) => `/halls/${id}`,

    // Rooms
    rooms: '/rooms',
    room: (id) => `/rooms/${id}`,
    buildingRooms: (buildingId) => `/buildings/${buildingId}/rooms`,

    // Levels
    levels: '/levels',
    level: (id) => `/levels/${id}`,
    
    // Sections
    sections: '/sections',
    section: (id) => `/sections/${id}`,
    levelSections: (levelId) => `/levels/${levelId}/sections`,

    // Groups
    groups: '/groups',
    group: (id) => `/groups/${id}`,
    groupSections: (groupId) => `/groups/${groupId}/sections`,

    // Courses
    courses: '/courses',
    course: (id) => `/courses/${id}`,

    // Instructors
    instructors: '/instructors',
    instructor: (id) => `/instructors/${id}`,
    instructorCourses: (instructorId) => `/instructors/${instructorId}/courses`,
    assignInstructorCourse: (instructorId, courseId) => `/instructors/${instructorId}/courses/${courseId}`,

    // TAs
    tas: '/tas',
    ta: (id) => `/tas/${id}`,
    taCourses: (taId) => `/tas/${taId}/courses`,
    assignTACourse: (taId, courseId) => `/tas/${taId}/courses/${courseId}`,

    // Schedule
    generateSchedule: '/schedule/generate',
    getSchedule: '/schedule/',
    exportSchedule: '/schedule/export',
    importSchedule: '/schedule/import'
};
