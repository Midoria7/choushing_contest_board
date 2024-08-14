/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      backgroundImage: {
        'custom-gradient-blue-sky': 'linear-gradient(135deg, #a1c4fd, #c2e9fb)',
        'custom-gradient-night-sky': 'linear-gradient(135deg, #292a3a, #536976)',
        'custom-gradient-stary-night': 'linear-gradient(135deg, #001f3f, #0088a9, #00c9a7, #92d5c6, #ebf5ee)',
        'custom-gradient-gracia': 'linear-gradient(135deg, #c7e9fb, #a6defa, #80d4f9, #5bc9f8, #35bef7)',
        'custom-gradient-purple': 'linear-gradient(135deg, #c850c0, #4158d0)',
      },
    },
  },
  plugins: [],
}
