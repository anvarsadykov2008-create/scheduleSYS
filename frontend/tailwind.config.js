/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                museum: {
                    bg: '#f8f9fa',
                    surface: '#ffffff',
                    'surface-hover': '#f1f3f5',
                    'surface-light': '#e9ecef',
                    accent: '#d35400',
                    'accent-hover': '#e67e22',
                    'accent-soft': 'rgba(211,84,0,0.12)',
                    text: '#212529',
                    'text-secondary': '#495057',
                    'text-muted': '#868e96',
                    border: 'rgba(0,0,0,0.1)',
                    'border-hover': 'rgba(0,0,0,0.2)',
                    danger: '#e74c3c',
                    'danger-soft': 'rgba(231,76,60,0.12)',
                    success: '#2ecc71',
                    'success-soft': 'rgba(46,204,113,0.12)',
                },
            },
            borderRadius: {
                'museum-sm': '8px',
                'museum-md': '16px',
                'museum-lg': '24px',
            },
            fontFamily: {
                museum: ['"DM Sans"', 'system-ui', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
