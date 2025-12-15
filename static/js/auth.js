// Authentication utilities
class Auth {
    static TOKEN_KEY = 'jwt_token';
    static USER_KEY = 'user_info';

    static saveToken(token) {
        localStorage.setItem(this.TOKEN_KEY, token);
    }

    static getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    }

    static removeToken() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
    }

    static saveUserInfo(userInfo) {
        localStorage.setItem(this.USER_KEY, JSON.stringify(userInfo));
    }

    static getUserInfo() {
        const userInfo = localStorage.getItem(this.USER_KEY);
        return userInfo ? JSON.parse(userInfo) : null;
    }

    static isAuthenticated() {
        return !!this.getToken();
    }

    static isAdmin() {
        const userInfo = this.getUserInfo();
        return userInfo && userInfo.is_admin;
    }

    static async login(username, password) {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch('/api/auth/login', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }

        const data = await response.json();
        this.saveToken(data.access_token);
        this.saveUserInfo(data.user);
        return data;
    }

    static logout() {
        this.removeToken();
        window.location.href = '/';
    }

    static requireAuth() {
        if (!this.isAuthenticated()) {
            window.location.href = '/';
            return false;
        }
        return true;
    }

    static requireAdmin() {
        if (!this.requireAuth()) return false;
        if (!this.isAdmin()) {
            showNotification('Access denied. Admin privileges required.', 'error');
            window.location.href = '/static/schedule.html';
            return false;
        }
        return true;
    }
}
