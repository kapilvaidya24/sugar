# explore alumni from IITB CSE 🌟

A sleek, modern React application to explore IIT Bombay Computer Science alumni career data. Features clean glass-morphism design, sophisticated dark theme, and instant filtering.

## ✨ Features

- **Modern Dark UI**: Clean, sophisticated design with subtle neon green accents
- **ag-Grid Table**: Professional data grid with sorting, filtering, and column management
- **Expandable Row Details**: Click any row to see full career timeline in a side panel
- **Rich Column Data**: 10+ columns including sector, seniority, company size, remote type
- **Built-in Filtering**: ag-Grid's powerful column filters and search capabilities
- **Career Timeline**: Beautiful timeline view showing full job history with skills
- **Instant Search**: Real-time search across all fields - zero latency
- **Static App**: No backend required - all data processing happens in your browser
- **Mobile Responsive**: Responsive design that works beautifully on all devices
- **Modular Architecture**: Clean, separated components for easy maintenance

## 🏗️ Architecture

- **Frontend Only**: Pure React with static JSON data
- **No Backend**: Data served as static files
- **Client-side Everything**: Search, filtering, sorting all in browser
- **Easy Deployment**: Can be hosted anywhere (Vercel, Netlify, GitHub Pages)

## 🚀 Quick Start

### Prerequisites

- **Node.js 14+** with npm
- That's it! No Python, no Flask, no backend needed.

### Setup & Run

```bash
# Navigate to the app directory
cd iitb-alumni-webapp/frontend

# Install dependencies
npm install

# Start the development server
npm start
```

The app will automatically open at **http://localhost:3000**

## 🎯 Usage

1. **View All Alumni**: Table loads with all ~950 alumni automatically
2. **Search**: Type in the search bar for instant filtering across all fields
3. **Click to Filter**: Use dropdown filters showing actual values:
   - **Current Company**: Click to see all companies (Google, Microsoft, etc.)
   - **Current Role**: Browse actual job titles from the data
   - **Current Location**: Filter by real work locations
   - **Graduation Year**: Select from actual graduation years
4. **LinkedIn**: Click neon "view" buttons to see full LinkedIn profiles

## 🔍 What You Can Explore

- **Company Trends**: See which companies hire the most IIT Bombay CS alumni
- **Role Patterns**: Discover common first job titles
- **Geographic Distribution**: Where alumni end up working
- **Timeline**: Alumni across different graduation years
- **Career Starts**: Everyone's first job after graduation

## 📊 Data Structure

The app focuses on **first job data** for simplicity:

```json
{
  "name": "Alumni Name",
  "grad_yr": 2015,
  "link_ln": "https://linkedin.com/in/...",
  "firstJob": {
    "comp": "Company Name",
    "title": "Job Title", 
    "loc": "Location",
    "start_year": 2015
  }
}
```

## 🚀 Deployment

Since this is a static React app, you can deploy it anywhere:

### Vercel (Recommended)
```bash
npm run build
npx vercel --prod
```

### Netlify
```bash
npm run build
# Upload the 'build' folder to Netlify
```

### GitHub Pages
```bash
npm install --save-dev gh-pages
# Add to package.json: "homepage": "https://yourusername.github.io/repo-name"
npm run build
npm run deploy
```

## 🎨 Customization

### Colors
- Edit CSS variables in component files to change neon colors
- Primary neon: `#00ff88` (green)
- Secondary neon: `#ff6b9d` (pink)
- Accent: `#00d4ff` (blue)

### Data
- Replace `public/data.json` with your own alumni data
- Modify the data processing logic in `App.js` if needed

### Filters
- Add new filter types in `ColumnFilters.js`
- Update the filtering logic in `App.js`

## 🛠️ Development

```bash
# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

## 💡 Why No Backend?

- **Simpler**: One less thing to deploy and maintain
- **Faster**: No API calls during search/filtering
- **Cheaper**: Static hosting is often free
- **Reliable**: No server downtime issues
- **Scalable**: CDN can serve static files globally

## 🔧 Technical Details

- **React 18** with hooks
- **Pure CSS** with custom dark theme
- **Client-side filtering** with real-time updates
- **Responsive table** that works on mobile
- **Static JSON data** served from public folder
- **No external dependencies** for core functionality

## 🎉 Perfect For

- Exploring alumni career patterns
- Finding alumni at specific companies
- Research on career trajectories
- Networking and connections
- Academic analysis

---

**Built for speed, style, and simplicity** ⚡