# Frontend Architecture Documentation

## Overview

The Gym Workout RAG frontend is a modern, scalable Flask application with a beautiful, responsive UI. It follows best practices for web application architecture with clear separation of concerns.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              index.html (SPA)                         │  │
│  │  ┌────────────────┐  ┌──────────────────────────┐   │  │
│  │  │  Model Select  │  │    Workout Form          │   │  │
│  │  │  (Step 1)      │  │    (Step 2)              │   │  │
│  │  └────────────────┘  └──────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
│           │                        │                         │
│           ├── styles.css           └── app.js                │
│           │   (Styling)                (Logic)               │
└───────────┼────────────────────────────┼─────────────────────┘
            │                            │
            │                            │ HTTP/JSON
            ▼                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Flask Frontend (Port 5000)                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    app.py                             │  │
│  │              (Application Factory)                    │  │
│  └──────────────────────────────────────────────────────┘  │
│           │                            │                     │
│           ▼                            ▼                     │
│  ┌─────────────────┐         ┌──────────────────────┐      │
│  │  API Blueprint  │         │  Server Manager      │      │
│  │  (api/routes)   │         │  (utils/server_mgr)  │      │
│  └─────────────────┘         └──────────────────────┘      │
└───────────┼─────────────────────────────┼───────────────────┘
            │                             │
            │ POST /api/generate          │ Start/Stop/Monitor
            │ GET /api/health             │
            ▼                             ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  POST /api/v1/generate  →  RAG Pipeline  →  LLM     │  │
│  │  GET /health            →  System Status             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
frontend/
├── app.py                      # Application entry point
│   ├── create_app()           # Flask app factory
│   └── main()                 # Server startup logic
│
├── api/                        # API Blueprint
│   ├── __init__.py            # Blueprint registration
│   └── routes.py              # API endpoints
│       ├── /api/generate      # Workout generation
│       └── /api/health        # Health check
│
├── utils/                      # Utility modules
│   ├── __init__.py
│   └── server_manager.py      # FastAPI lifecycle management
│       ├── start_server()     # Start backend
│       ├── stop_server()      # Stop backend
│       └── is_server_running() # Health check
│
├── static/                     # Static assets
│   ├── css/
│   │   └── styles.css         # Modern CSS with variables
│   ├── js/
│   │   └── app.js             # ES6+ JavaScript
│   └── images/                # Image assets
│
└── templates/                  # Jinja2 templates
    └── index.html             # Single Page Application
```

## Component Details

### 1. Application Factory (`app.py`)

**Purpose**: Create and configure the Flask application

**Key Functions**:
- `create_app()`: Factory pattern for app creation
- `main()`: Entry point with server management

**Benefits**:
- Testability (can create multiple app instances)
- Configuration flexibility
- Clean separation of concerns

```python
def create_app():
    app = Flask(__name__)
    app.register_blueprint(api_bp)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    return app
```

### 2. API Blueprint (`api/`)

**Purpose**: Handle all API endpoints

**Endpoints**:
- `POST /api/generate`: Generate workout plan
- `GET /api/health`: Combined health check

**Features**:
- Request validation
- Error handling
- Type conversion
- Timeout management

**Benefits**:
- Modular routing
- Easy to test
- Scalable (can add more blueprints)

### 3. Server Manager (`utils/server_manager.py`)

**Purpose**: Manage FastAPI backend lifecycle

**Responsibilities**:
- Start FastAPI server
- Monitor server health
- Wait for initialization
- Graceful shutdown

**Key Methods**:
```python
class ServerManager:
    def start_server(max_wait=180)
    def stop_server()
    def is_server_running()
    def get_server_status()
```

### 4. Static Assets

#### CSS (`static/css/styles.css`)

**Features**:
- CSS Variables for theming
- Responsive design (mobile-first)
- Smooth animations
- Component-based styles
- Custom scrollbars

**Structure**:
```css
:root { /* Variables */ }
* { /* Reset */ }
.component { /* Component styles */ }
@media { /* Responsive */ }
```

#### JavaScript (`static/js/app.js`)

**Architecture**:
- Modular design with namespaces
- State management
- Event handling
- API communication
- UI rendering

**Modules**:
```javascript
AppState          // Global state
DOM               // DOM element cache
ModelConfig       // Model configuration
Navigation        // Page navigation
FormHandler       // Form validation
API               // Backend communication
UI                // UI rendering
App               // Main application
```

### 5. Template (`templates/index.html`)

**Structure**:
- Semantic HTML5
- Two-step workflow
- Model selection (Step 1)
- Workout form (Step 2)
- Output display

**Features**:
- Accessible markup
- SEO-friendly
- Progressive enhancement

## Data Flow

### Workout Generation Flow

```
1. User fills form
   └─> JavaScript validates input
       └─> POST /api/generate
           └─> Flask validates request
               └─> POST to FastAPI backend
                   └─> RAG Pipeline
                       ├─> Vector search (ChromaDB)
                       ├─> Context retrieval
                       └─> LLM generation
                           └─> Workout plan JSON
                               └─> Flask formats response
                                   └─> JavaScript renders UI
```

### Server Startup Flow

```
1. python app.py
   └─> ServerManager.start_server()
       ├─> Check if already running
       ├─> Start FastAPI subprocess
       ├─> Wait for health check
       │   ├─> Server ready?
       │   └─> Exercises loaded?
       └─> Success/Timeout
           └─> Flask app.run()
```

## Design Patterns

### 1. Application Factory Pattern
- **Where**: `app.py`
- **Why**: Testability, flexibility, multiple instances
- **How**: `create_app()` function returns configured app

### 2. Blueprint Pattern
- **Where**: `api/` directory
- **Why**: Modular routing, scalability
- **How**: Separate blueprint for API routes

### 3. Manager Pattern
- **Where**: `utils/server_manager.py`
- **Why**: Encapsulate server lifecycle logic
- **How**: ServerManager class with lifecycle methods

### 4. Module Pattern (JavaScript)
- **Where**: `static/js/app.js`
- **Why**: Namespace isolation, organization
- **How**: Object literals for each module

### 5. State Management Pattern
- **Where**: `static/js/app.js` (AppState)
- **Why**: Centralized state, predictable updates
- **How**: Single source of truth object

## Best Practices

### Python Code
1. **Type Hints**: Use type hints for function parameters
2. **Docstrings**: Document all functions and classes
3. **Error Handling**: Comprehensive try-except blocks
4. **Logging**: Use print statements for user feedback
5. **PEP 8**: Follow Python style guide

### JavaScript Code
1. **ES6+**: Use modern JavaScript features
2. **Const/Let**: No var declarations
3. **Arrow Functions**: Use arrow functions for callbacks
4. **Template Literals**: Use backticks for strings
5. **Async/Await**: Use async/await for promises

### CSS Code
1. **Variables**: Use CSS variables for theming
2. **BEM-like**: Component-based naming
3. **Mobile-First**: Start with mobile styles
4. **Animations**: Smooth transitions
5. **Accessibility**: High contrast, readable fonts

### HTML Code
1. **Semantic**: Use semantic HTML5 elements
2. **Accessibility**: ARIA labels where needed
3. **SEO**: Meta tags, proper headings
4. **Progressive**: Works without JavaScript
5. **Validation**: HTML5 form validation

## Performance Optimizations

### Frontend
- **CSS**: Single stylesheet, minified in production
- **JavaScript**: Single file, deferred loading
- **Images**: Optimized, lazy loading
- **Caching**: Browser caching for static assets

### Backend Communication
- **Timeouts**: 10-minute timeout for LLM
- **Error Handling**: Graceful degradation
- **Health Checks**: Monitor backend status
- **Connection Pooling**: Reuse connections

## Security Considerations

### Input Validation
- **Client-side**: JavaScript validation
- **Server-side**: Flask validation
- **Type Checking**: Pydantic models in backend

### XSS Prevention
- **HTML Escaping**: All user input escaped
- **Content Security**: No inline scripts
- **Sanitization**: Clean user input

### API Security
- **CORS**: Configured for localhost
- **Rate Limiting**: Can be added
- **Authentication**: Can be added for production

## Testing Strategy

### Unit Tests
- Test individual functions
- Mock external dependencies
- Test edge cases

### Integration Tests
- Test API endpoints
- Test server manager
- Test full workflow

### E2E Tests
- Test user workflows
- Test UI interactions
- Test error scenarios

## Deployment Considerations

### Development
```bash
python app.py
# Debug mode enabled
# Auto-reload on changes
```

### Production
```bash
gunicorn -w 4 -b 0.0.0.0:5000 "frontend.app:create_app()"
# Multiple workers
# Production WSGI server
# Environment variables for config
```

### Docker
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "frontend.app:create_app()"]
```

## Future Enhancements

### Planned Features
1. **User Authentication**: Login/signup system
2. **Workout History**: Save and view past workouts
3. **Progress Tracking**: Track fitness progress
4. **Social Features**: Share workouts
5. **Mobile App**: React Native version

### Technical Improvements
1. **WebSockets**: Real-time updates
2. **Service Workers**: Offline support
3. **PWA**: Progressive Web App
4. **CDN**: Static asset delivery
5. **Monitoring**: Application monitoring

## Troubleshooting

### Common Issues

**Issue**: Static files not loading
- **Solution**: Clear browser cache, check file paths

**Issue**: Backend connection error
- **Solution**: Check if FastAPI is running on port 8000

**Issue**: Slow workout generation
- **Solution**: Use smaller model or LM Studio

**Issue**: UI not responsive
- **Solution**: Check browser console for errors

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask Blueprints](https://flask.palletsprojects.com/en/2.3.x/blueprints/)
- [Modern JavaScript](https://javascript.info/)
- [CSS Variables](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)
- [Responsive Design](https://web.dev/responsive-web-design-basics/)

---

**Last Updated**: 2026-05-17  
**Version**: 2.0.0  
**Maintainer**: Gym Workout RAG Team