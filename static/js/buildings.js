// Buildings page logic
console.log('[Buildings.js] Script loaded');

// Check authentication
const authCheck = Auth.requireAdmin();
console.log('[Buildings.js] Auth check result:', authCheck);

if (!authCheck) {
    console.error('[Buildings.js] Auth failed - script may not continue');
}

let allBuildings = [];
let allRooms = [];
let filteredBuildings = [];
let filteredRooms = [];
let selectedBuildingId = null;
let editingBuildingId = null;
let editingRoomId = null;

const buildingModal = new Modal('building-modal-overlay');
const roomModal = new Modal('room-modal-overlay');

// Load buildings
async function loadBuildings() {
    try {
        allBuildings = await API.get(Endpoints.buildings);
        filteredBuildings = [...allBuildings];
    } catch (error) {
        showNotification('Failed to load buildings: ' + error.message, 'error');
    }
}

// Load rooms
async function loadRooms() {
    try {
        allRooms = await API.get(Endpoints.rooms);
        filteredRooms = [...allRooms];
        renderRoomsTable();
    } catch (error) {
        showNotification('Failed to load rooms: ' + error.message, 'error');
    }
}

// Render buildings table
function renderBuildingsTable() {
    const columns = [
        { key: 'building_name', label: 'Building Name' },
        { 
            key: 'room_count', 
            label: 'Rooms',
            format: (value, building) => {
                const count = allRooms.filter(r => r.building_id === building.building_id).length;
                return `<span class="badge badge-primary">${count}</span>`;
            }
        }
    ];

    const actions = [
        {
            label: 'View Rooms',
            className: 'btn-primary',
            handler: (building) => viewBuildingRooms(building)
        },
        {
            label: 'Edit',
            className: 'btn-secondary',
            handler: (building) => editBuilding(building)
        },
        {
            label: 'Delete',
            className: 'btn-danger',
            handler: (building) => deleteBuilding(building.building_id)
        }
    ];

    const table = createTable(filteredBuildings, columns, actions);
    document.getElementById('buildings-table').innerHTML = '';
    document.getElementById('buildings-table').appendChild(table);
}

// Render rooms table
function renderRoomsTable() {
    // Show all rooms, not just for selected building
    const roomsToShow = selectedBuildingId ? filteredRooms.filter(r => r.building_id === selectedBuildingId) : filteredRooms;
    
    const columns = [
        { key: 'room_number', label: 'Room Number' },
        { 
            key: 'building', 
            label: 'Building',
            format: (value, room) => {
                const building = allBuildings.find(b => b.building_id === room.building_id);
                return building ? building.building_name : 'N/A';
            }
        },
        { key: 'room_type', label: 'Type' },
        { key: 'capacity', label: 'Capacity' }
    ];

    const actions = [
        {
            label: 'Edit',
            className: 'btn-secondary',
            handler: (room) => editRoom(room)
        },
        {
            label: 'Delete',
            className: 'btn-danger',
            handler: (room) => deleteRoom(room.room_id)
        }
    ];

    const table = createTable(roomsToShow, columns, actions);
    document.getElementById('rooms-table').innerHTML = '';
    document.getElementById('rooms-table').appendChild(table);
}

// View building's rooms
function viewBuildingRooms(building) {
    selectedBuildingId = building.building_id;
    filterRooms();
    
    // Scroll to rooms section
    document.getElementById('rooms-section').scrollIntoView({ behavior: 'smooth' });
}

// Filter buildings
function filterBuildings() {
    const searchTerm = document.getElementById('building-search').value;
    filteredBuildings = filterData(allBuildings, searchTerm, ['building_name']);
    renderBuildingsTable();
}

// Filter rooms
function filterRooms() {
    const searchTerm = document.getElementById('room-search').value;
    filteredRooms = filterData(allRooms, searchTerm, ['room_number', 'room_type']);
    renderRoomsTable();
}

// Open building modal
function openBuildingModal() {
    editingBuildingId = null;
    buildingModal.setTitle('Add Building');
    clearForm('building-form');
    buildingModal.open();
}

// Edit building
function editBuilding(building) {
    editingBuildingId = building.building_id;
    buildingModal.setTitle('Edit Building');
    setFormData('building-form', building);
    buildingModal.open();
}

// Save building
async function saveBuilding() {
    if (!validateForm('building-form')) {
        return;
    }

    const data = getFormData('building-form');
    delete data.building_id; // Remove id from data

    try {
        showLoading(true);
        
        if (editingBuildingId) {
            await API.put(Endpoints.building(editingBuildingId), data);
            showNotification('Building updated successfully', 'success');
        } else {
            await API.post(Endpoints.buildings, data);
            showNotification('Building created successfully', 'success');
        }

        buildingModal.close();
        await loadBuildings();
        await loadRooms(); // Refresh rooms to update building names
        renderBuildingsTable();
        renderRoomsTable();
    } catch (error) {
        showNotification('Failed to save building: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Delete building
async function deleteBuilding(id) {
    console.log('=== DELETE BUILDING CLICKED ===');
    console.log('[deleteBuilding] ID received:', id);
    console.log('[deleteBuilding] ID type:', typeof id);
    
    const roomCount = allRooms.filter(r => r.building_id === id).length;
    console.log('[deleteBuilding] Room count:', roomCount);
    
    if (roomCount > 0) {
        console.log('[deleteBuilding] Cannot delete - has rooms');
        showNotification(`Cannot delete building. It has ${roomCount} room(s). Delete rooms first.`, 'error');
        return;
    }

    if (!window.confirm('Are you sure you want to delete this building?')) {
        console.log('[deleteBuilding] User cancelled');
        return;
    }

    try {
        showLoading(true);
        const endpoint = Endpoints.building(id);
        console.log('[deleteBuilding] Calling API with endpoint:', endpoint);
        await API.delete(endpoint);
        console.log('[deleteBuilding] API call successful');
        showNotification('Building deleted successfully', 'success');
        await loadBuildings();
        console.log('[deleteBuilding] Buildings reloaded');
        renderBuildingsTable();
        console.log('[deleteBuilding] Table rendered');
    } catch (error) {
        console.error('[deleteBuilding] Error caught:', error);
        console.error('[deleteBuilding] Error message:', error.message);
        console.error('[deleteBuilding] Error stack:', error.stack);
        showNotification('Failed to delete building: ' + error.message, 'error');
    } finally {
        showLoading(false);
        console.log('=== DELETE BUILDING COMPLETE ===');
    }
}

// Open room modal
function openRoomModal() {
    editingRoomId = null;
    roomModal.setTitle('Add Room');
    clearForm('room-form');
    
    // Populate building dropdown
    populateBuildingDropdown();
    
    // Pre-select the current building if one is selected
    if (selectedBuildingId) {
        document.getElementById('room-building').value = selectedBuildingId;
    }
    
    roomModal.open();
}

// Edit room
function editRoom(room) {
    editingRoomId = room.room_id;
    roomModal.setTitle('Edit Room');
    
    // Populate building dropdown first
    populateBuildingDropdown();
    
    setFormData('room-form', room);
    roomModal.open();
}

// Save room
async function saveRoom() {
    if (!validateForm('room-form')) {
        return;
    }

    const data = getFormData('room-form');
    delete data.room_id; // Remove id from data

    try {
        showLoading(true);
        
        if (editingRoomId) {
            await API.put(Endpoints.room(editingRoomId), data);
            showNotification('Room updated successfully', 'success');
        } else {
            await API.post(Endpoints.rooms, data);
            showNotification('Room created successfully', 'success');
        }

        roomModal.close();
        await loadRooms();
        renderRoomsTable();
        renderBuildingsTable(); // Update room counts
    } catch (error) {
        showNotification('Failed to save room: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Delete room
async function deleteRoom(id) {
    console.log('=== DELETE ROOM CLICKED ===');
    console.log('[deleteRoom] ID received:', id);
    console.log('[deleteRoom] ID type:', typeof id);
    
    if (!window.confirm('Are you sure you want to delete this room?')) {
        console.log('[deleteRoom] User cancelled');
        return;
    }

    try {
        showLoading(true);
        const endpoint = Endpoints.room(id);
        console.log('[deleteRoom] Calling API with endpoint:', endpoint);
        await API.delete(endpoint);
        console.log('[deleteRoom] API call successful');
        showNotification('Room deleted successfully', 'success');
        await loadRooms();
        renderRoomsTable();
        renderBuildingsTable(); // Update room counts
        console.log('[deleteRoom] Tables updated');
    } catch (error) {
        console.error('[deleteRoom] Error caught:', error);
        console.error('[deleteRoom] Error message:', error.message);
        showNotification('Failed to delete room: ' + error.message, 'error');
    } finally {
        showLoading(false);
        console.log('=== DELETE ROOM COMPLETE ===');
    }
}

// Populate building dropdown in room form
function populateBuildingDropdown() {
    const select = document.getElementById('room-building');
    select.innerHTML = '<option value="">Select building</option>';
    
    allBuildings.forEach(building => {
        const option = document.createElement('option');
        option.value = building.building_id;
        option.textContent = building.building_name;
        select.appendChild(option);
    });
}

// Hall Management
let allHalls = [];
let filteredHalls = [];
let editingHallId = null;
const hallModal = new Modal('hall-modal-overlay');

// Load halls
async function loadHalls() {
    try {
        allHalls = await API.get(Endpoints.halls);
        filteredHalls = [...allHalls];
        renderHallsTable();
    } catch (error) {
        showNotification('Failed to load halls: ' + error.message, 'error');
    }
}

// Render halls table
function renderHallsTable() {
    const columns = [
        { key: 'hall_name', label: 'Hall Name' },
        { key: 'capacity', label: 'Capacity' }
    ];

    const actions = [
        {
            label: 'Edit',
            className: 'btn-secondary',
            handler: (hall) => editHall(hall)
        },
        {
            label: 'Delete',
            className: 'btn-danger',
            handler: (hall) => deleteHall(hall.hall_id)
        }
    ];

    const table = createTable(filteredHalls, columns, actions);
    document.getElementById('halls-table').innerHTML = '';
    document.getElementById('halls-table').appendChild(table);
}

// Filter halls
function filterHalls() {
    const searchTerm = document.getElementById('hall-search').value;
    filteredHalls = filterData(allHalls, searchTerm, ['hall_name']);
    renderHallsTable();
}

// Open hall modal
function openHallModal() {
    editingHallId = null;
    hallModal.setTitle('Add Hall');
    clearForm('hall-form');
    hallModal.open();
}

// Edit hall
function editHall(hall) {
    editingHallId = hall.hall_id;
    hallModal.setTitle('Edit Hall');
    setFormData('hall-form', hall);
    hallModal.open();
}

// Save hall
async function saveHall() {
    if (!validateForm('hall-form')) {
        return;
    }

    const data = getFormData('hall-form');
    delete data.hall_id;

    try {
        showLoading(true);
        
        if (editingHallId) {
            await API.put(Endpoints.hall(editingHallId), data);
            showNotification('Hall updated successfully', 'success');
        } else {
            await API.post(Endpoints.halls, data);
            showNotification('Hall created successfully', 'success');
        }

        hallModal.close();
        await loadHalls();
    } catch (error) {
        showNotification('Failed to save hall: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Delete hall
async function deleteHall(id) {
    console.log('=== DELETE HALL CLICKED ===');
    console.log('[deleteHall] ID received:', id);
    console.log('[deleteHall] ID type:', typeof id);
    
    if (!window.confirm('Are you sure you want to delete this hall?')) {
        console.log('[deleteHall] User cancelled');
        return;
    }

    try {
        showLoading(true);
        const endpoint = Endpoints.hall(id);
        console.log('[deleteHall] Calling API with endpoint:', endpoint);
        await API.delete(endpoint);
        console.log('[deleteHall] API call successful');
        showNotification('Hall deleted successfully', 'success');
        await loadHalls();
        console.log('[deleteHall] Halls reloaded');
    } catch (error) {
        console.error('[deleteHall] Error caught:', error);
        console.error('[deleteHall] Error message:', error.message);
        showNotification('Failed to delete hall: ' + error.message, 'error');
    } finally {
        showLoading(false);
        console.log('=== DELETE HALL COMPLETE ===');
    }
}

// Initialize page
async function init() {
    console.log('[Buildings.js] init() called');
    try {
        showLoading(true);
        console.log('[Buildings.js] Loading data...');
        await loadBuildings();
        console.log('[Buildings.js] Buildings loaded:', allBuildings.length);
        await loadRooms();
        console.log('[Buildings.js] Rooms loaded:', allRooms.length);
        await loadHalls();
        console.log('[Buildings.js] Halls loaded:', allHalls.length);
        // Render tables after all data is loaded
        renderBuildingsTable();
        renderHallsTable();
        console.log('[Buildings.js] Tables rendered');
    } catch (error) {
        console.error('[Buildings.js] Initialization error:', error);
        showNotification('Failed to initialize page: ' + error.message, 'error');
    } finally {
        showLoading(false);
        console.log('[Buildings.js] Initialization complete');
    }
}

console.log('[Buildings.js] Calling init()');
init();
