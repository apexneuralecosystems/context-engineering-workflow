# Research Assistant Frontend

A modern React Next.js frontend for the AI Research Assistant.

## Features

- 🎨 Modern, responsive UI with dark mode support
- 💬 Real-time chat interface
- 📄 Document upload and processing
- 📚 Citation and source display
- 🔍 Source relevance analysis
- ⚡ Fast and efficient with Next.js 14

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- Backend API server running (see `api_server.py`)

### Installation

```bash
cd frontend
npm install
# or
yarn install
# or
pnpm install
```

### Environment Variables

Create a `.env.local` file in the `frontend` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8003
PORT=3003
```

**Note:** 
- The frontend runs on port 3003 by default (configurable via `PORT` in `.env.local` or `FRONTEND_PORT` in root `.env`)
- The backend URL should match the `API_PORT` in your root `.env` file (default: 8003)
- You can copy `frontend/.env.example` to `frontend/.env.local` as a starting point

### Development

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

Open [http://localhost:3003](http://localhost:3003) in your browser.

### Building for Production

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/                    # Next.js app directory
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── ChatInterface.tsx  # Main chat component
│   ├── DocumentUpload.tsx # Document upload component
│   ├── ResponseDisplay.tsx # Response display component
│   ├── CitationsDisplay.tsx # Citations display component
│   ├── QueryInput.tsx     # Query input component
│   └── LoadingSpinner.tsx # Loading spinner
├── lib/                   # Utilities
│   ├── api.ts             # API client
│   └── utils.ts           # Utility functions
└── package.json           # Dependencies
```

## API Integration

The frontend communicates with the FastAPI backend (`api_server.py`) through the following endpoints:

- `POST /api/initialize` - Initialize the research assistant
- `GET /api/status` - Get assistant status
- `POST /api/upload-document` - Upload and process a PDF
- `POST /api/query` - Process a research query
- `GET /health` - Health check

## Technologies

- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Lucide React** - Icons
- **Axios** - HTTP client

