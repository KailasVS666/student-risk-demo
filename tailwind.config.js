/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './app/templates/**/*.html',
    './app/static/js/**/*.js',
    './app/static/css/**/*.css',
    './app/views/**/*.py'
  ],
  theme: {
    extend: {}
  },
  plugins: []
};