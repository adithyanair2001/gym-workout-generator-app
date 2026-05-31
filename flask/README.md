# Gym Workout RAG - Frontend

Modern, scalable Flask frontend for the Gym Workout RAG system with a beautiful, responsive UI.

## 🏗️ Architecture

The frontend follows a modern, modular architecture:

```
frontend/
├── app.py                 # Main Flask application (entry point)
├── api/                   # API Blueprint
│   ├── __init__.py       # Blueprint initialization
│   └── routes.py         # API endpoints
├── utils/                 # Utility modules
│   ├── __init__.py
│   └── server_manager.py # FastAPI server lifecycle management
├── static/               # Static assets
│   ├── css/
│   │   └── styles.css   # Modern CSS with variables and animations
│   ├── js/
│   │   └── app.js       # ES6+ JavaScript with modular architecture
│   └── images/          # Image assets
└── templates/            # Jinja2 templates
    └── index.html       # Main SPA template
```

## ✨ Features

### Modern UI/UX
- **Gradient Design**: Beautiful purple gradient background
- **Card-based Layout**: Clean, organized interface
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Smooth Animations**: Fade-in effects and hover transitions
- **Custom Scrollbars**: Styled scrollbars for better aesthetics
- **Loading States**: Animated spinner during workout generation

### Technical Features
- **Blueprint Architecture**: Modular, scalable Flask structure
- **Separation of Concerns**: CSS, JS, and HTML in separate files
- **ES6+ JavaScript**: Modern JavaScript with classes and modules
- **CSS Variables**: Easy theme customization
- **Error Handling**: Comprehensive error messages and validation
- **Health Checks**: Monitor both frontend and backend status

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Virtual environment activated
- FastAPI backend configured

### Installation

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp ../.env.example ../.env
# Edit .env with your settings
```

3. **Run the application**:
```bash
python app.py
```

The frontend will automatically:
- Start the FastAPI backend server
- Wait for exercises to load
- Launch the Flask frontend at http://localhost:5000

## 📋 API Endpoints

### Frontend Routes
- `GET /` - Main application page
- `GET /health` - Frontend health check

### API Routes (Blueprint)
- `POST /api/generate` - Generate workout plan
- `GET /api/health` - Combined health check (frontend + backend)

## 🎨 Customization

### Theme Colors

Edit `frontend/static/css/styles.css` to customize the theme:

```css
:root {
    --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --primary-color: #667eea;
    --primary-dark: #764ba2;
    /* ... more variables */
}
```

### Model Options

The UI supports 7 model deployment options:
1. **MLX Local Models** - Mac-only, agent mode
2. **OMLX Server** - OpenAI-compatible MLX server
3. **GGUF Models** - Cross-platform via LangChain
4. **Local Servers** - LM Studio, OLLAMA
5. **OpenAI** - GPT-4 models (paid)
6. **Anthropic** - Claude models (paid)
7. **Groq** - Fast inference (free tier)

## 🔧 Development

### Project Structure

**`app.py`** - Main application factory
- Creates Flask app with blueprints
- Manages server lifecycle
- Entry point for the application

**`api/routes.py`** - API endpoints
- Workout generation endpoint
- Health check endpoint
- Request validation and error handling

**`utils/server_manager.py`** - Backend management
- Start/stop FastAPI server
- Monitor server health
- Handle graceful shutdown

**`static/css/styles.css`** - Styling
- CSS variables for theming
- Responsive design
- Animations and transitions
- Component styles

**`static/js/app.js`** - Frontend logic
- State management
- Form handling
- API communication
- UI rendering

**`templates/index.html`** - Main template
- Semantic HTML5
- Two-step workflow
- Model selection
- Workout form

### Adding New Features

1. **New API Endpoint**:
   - Add route to `api/routes.py`
   - Update `static/js/app.js` to call it

2. **New UI Component**:
   - Add HTML to `templates/index.html`
   - Add styles to `static/css/styles.css`
   - Add logic to `static/js/app.js`

3. **New Model Type**:
   - Add option to model type select in HTML
   - Add configuration section in HTML
   - Update `ModelConfig.getConfig()` in JS

## 🐛 Troubleshooting

### Frontend won't start
```bash
# Check if port 5000 is available
lsof -i :5000

# Kill process if needed
kill -9 <PID>
```

### Backend connection errors
```bash
# Check backend health
curl http://localhost:8000/health

# Restart backend manually
cd ..
python -m uvicorn app.main:app --reload
```

### Static files not loading
```bash
# Clear browser cache
# Or use hard refresh: Cmd+Shift+R (Mac) / Ctrl+Shift+R (Windows)
```

### CSS/JS changes not appearing
- Clear browser cache
- Check browser console for errors
- Verify file paths in HTML template

## 📊 Performance

- **Initial Load**: < 2 seconds
- **Workout Generation**: 30-60 seconds (depends on model)
- **API Response Time**: < 100ms (excluding LLM)
- **Bundle Size**: 
  - CSS: ~15KB
  - JS: ~12KB
  - HTML: ~8KB

## 🔒 Security

- Input validation on both client and server
- XSS prevention with HTML escaping
- CSRF protection (Flask default)
- Secure API key handling (not stored in frontend)
- Request timeout limits

## 📝 Code Style

- **Python**: PEP 8 compliant
- **JavaScript**: ES6+ with consistent naming
- **CSS**: BEM-inspired naming convention
- **HTML**: Semantic HTML5

## 🤝 Contributing

When contributing to the frontend:

1. Follow the existing architecture
2. Add comments for complex logic
3. Test on multiple browsers
4. Ensure responsive design
5. Update this README if needed

## 📄 License

Part of the Gym Workout RAG project.

## 🙏 Credits

- **Design**: Modern gradient design inspired by contemporary web apps
- **Icons**: Emoji icons for simplicity
- **Fonts**: Inter font family from Google Fonts
- **Framework**: Flask with Jinja2 templating

---

**Version**: 2.0.0  
**Last Updated**: 2026-05-17  
**Maintainer**: Gym Workout RAG Team