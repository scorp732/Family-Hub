# Family Hub: AI-Powered Todo & Lifestyle Manager

![Family Hub](https://img.shields.io/badge/Version-1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32.0+-red)

Family Hub is a comprehensive family management application that serves as a central command center for managing daily tasks, events, budgets, and more, all enhanced by an integrated AI assistant.

## Features

- **Multi-Profile Support**: User authentication system with role-based permissions (admin, parent, child)
- **Task & Event Management**: Complete CRUD functionality for tasks and events with calendar integration
- **Budget Tracking**: Budget management with expense tracking and visualization
- **Shopping Lists**: Collaborative shopping lists with check-off functionality
- **AI Assistant**: Natural language processing for managing tasks, scheduling events, and providing advice
- **Customizable Settings**: Configuration system for application settings and AI model integration

## Screenshots

*Screenshots will be added in future releases*

## Installation

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Step 1: Clone the Repository

```bash
git clone https://github.com/scorp732/Family-Hub.git
cd Family-Hub
```

### Step 2: Create a Virtual Environment (Optional but Recommended)

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run the Application

```bash
python run.py
```

By default, the application will run on port 13795. You can access it by opening a web browser and navigating to:

```
http://localhost:13795
```

To specify a different port, use the `--port` option:

```bash
python run.py --port 8501
```

## Configuration

### AI Assistant Configuration

Family Hub supports multiple AI providers:

1. **OpenAI**: GPT-4, GPT-4o, GPT-3.5 Turbo
2. **Anthropic**: Claude, Claude Sonnet, Claude Haiku
3. **Google**: Gemini Pro

To configure the AI assistant:

1. Obtain an API key from your preferred provider
2. Navigate to Settings > AI Assistant in the application
3. Enter your API key and select your preferred model
4. Adjust parameters like temperature and max tokens as needed

The application will work in basic mode without an API key, providing rule-based responses to common queries.

## Project Structure

```
family_hub/
├── ai/                # AI assistant functionality
├── auth/              # Authentication and user management
├── budget/            # Budget and bill tracking
├── calendar/          # Calendar and event management
├── core/              # Core application functionality
├── data/              # Data models and storage
├── models/            # AI models and integrations
├── settings/          # Application settings
├── shopping/          # Shopping list management
├── tasks/             # Task management
├── ui/                # UI components
└── utils/             # Utility functions
```

## Command Line Options

The application supports several command line options:

- `--port PORT`: Specify the port to run the application on (default: 13795)
- `--debug`: Enable debug mode with additional logging
- `--no-auto-kill`: Do not automatically kill processes using the specified port
- `--host HOST`: Host address to bind to (default: 0.0.0.0)

Example:

```bash
python run.py --port 8501 --debug --host 127.0.0.1
```

## Development

### Running in Development Mode

```bash
python run.py --debug
```

### Project Components

- **Models**: Data models are defined in `family_hub/data/models.py`
- **Storage**: Data storage operations are in `family_hub/data/storage.py`
- **UI Components**: Reusable UI components are in `family_hub/ui/components.py`
- **Pages**: Application pages are defined in `family_hub/ui/pages.py`
- **AI Assistant**: AI functionality is in `family_hub/ai/assistant.py`

## Troubleshooting

### Port Already in Use

If you see an error message about the port being in use, you can either:

1. Use a different port with the `--port` option
2. Let the application automatically free the port (default behavior)
3. Manually kill the process using the port

### API Key Issues

If you're having trouble with the AI assistant:

1. Verify your API key is correct
2. Check that you've selected the appropriate model for your API key
3. Ensure your API key has the necessary permissions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Version History

- **1.0.0** (2025-03-18): Initial release
  - Basic authentication system
  - Task and event management
  - Budget tracking
  - Shopping lists
  - AI assistant integration