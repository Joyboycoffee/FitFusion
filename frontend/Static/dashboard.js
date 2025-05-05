// script.js
document.querySelectorAll('.btn').forEach(btn => {
    btn.addEventListener('click', () => {
        alert(`You clicked on ${btn.innerText}`);
    });
});

// Theme management
const themeToggle = {
    init() {
        this.addThemeSwitcher();
        this.loadTheme();
        this.bindEvents();
    },

    addThemeSwitcher() {
        const switcher = document.createElement('div');
        switcher.className = 'theme-switcher';
        switcher.innerHTML = `
            <button data-theme="light">Light</button>
            <button data-theme="dark">Dark</button>
            <button data-theme="system">System</button>
        `;
        document.body.appendChild(switcher);
    },

    loadTheme() {
        const savedTheme = localStorage.getItem('theme') || 'system';
        this.setTheme(savedTheme);
    },

    setTheme(theme) {
        if (theme === 'system') {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
        } else {
            document.documentElement.setAttribute('data-theme', theme);
        }
        localStorage.setItem('theme', theme);
    },

    bindEvents() {
        document.querySelector('.theme-switcher').addEventListener('click', (e) => {
            if (e.target.matches('button')) {
                this.setTheme(e.target.dataset.theme);
            }
        });

        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (localStorage.getItem('theme') === 'system') {
                this.setTheme('system');
            }
        });
    }
};

// API Handlers
const api = {
    async getProfile() {
        const response = await fetch('/profile');
        if (!response.ok) throw new Error('Failed to fetch profile');
        return response.json();
    },

    async predictBodyType(height, weight) {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ height, weight })
        });
        if (!response.ok) throw new Error('Prediction failed');
        return response.json();
    }
};

// UI Controllers
const bodyAnalysis = {
    init() {
        this.modal = document.getElementById('bodyAnalysisModal');
        this.form = document.getElementById('bodyAnalysisForm');
        this.result = document.getElementById('analysisResult');
        this.bodyTypeDisplay = document.getElementById('bodyTypeDisplay');
        this.bindEvents();
    },

    bindEvents() {
        document.getElementById('bodyAnalysisBtn').onclick = () => this.modal.style.display = 'block';
        document.querySelector('.close').onclick = () => this.modal.style.display = 'none';
        this.form.onsubmit = (e) => this.handleSubmit(e);
    },

    async handleSubmit(e) {
        e.preventDefault();
        try {
            const height = document.getElementById('height').value;
            const weight = document.getElementById('weight').value;
            
            this.result.innerHTML = 'Analyzing...';
            const data = await api.predictBodyType(height, weight);
            
            this.bodyTypeDisplay.textContent = data.body_type;
            this.result.innerHTML = `Your body type is: ${data.body_type}`;
        } catch (error) {
            this.result.innerHTML = `Error: ${error.message}`;
        }
    }
};

// Profile Handler
const profile = {
    async init() {
        try {
            const data = await api.getProfile();
            document.getElementById('userName').textContent = data.email;
        } catch (error) {
            console.error('Failed to load profile:', error);
        }
    }
};

// Initialize everything when the page loads
document.addEventListener('DOMContentLoaded', () => {
    themeToggle.init();
    bodyAnalysis.init();
    profile.init();
});