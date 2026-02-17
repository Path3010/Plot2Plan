# AutoCAD Floor Plan Generator – Complete Project Documentation (with Groq Integration)

## Version 2.0

---

## Table of Contents

1. [Introduction](#1-introduction)  
2. [System Overview](#2-system-overview)  
3. [Technology Stack](#3-technology-stack)  
4. [Groq Integration](#4-groq-integration)  
5. [Module Design](#5-module-design)  
   5.1 Landing Page  
   5.2 User Onboarding  
   5.3 Interaction Modes: Chat & Form  
   5.4 Boundary Upload & Processing  
   5.5 Floor Plan Generation Engine  
   5.6 CAD File Generation  
   5.7 3D Model Generation & Viewer  
   5.8 Confirmation & Export  
6. [Data Models](#6-data-models)  
7. [API Design](#7-api-design)  
8. [Algorithms & Logic](#8-algorithms--logic)  
   8.1 Boundary Extraction from Image  
   8.2 Floor Plan Layout Algorithm with LLM Guidance  
   8.3 Room Sizing & Amenity Handling  
9. [UI/UX Design](#9-uiux-design)  
10. [Implementation Plan](#10-implementation-plan)  
11. [Testing Strategy](#11-testing-strategy)  
12. [Deployment Guide](#12-deployment-guide)  
13. [Documentation](#13-documentation)  
14. [Conclusion](#14-conclusion)  

---

## 1. Introduction

### 1.1 Purpose
The **AutoCAD Floor Plan Generator** is a web‑based application that allows users to automatically create detailed 2D CAD floor plans and corresponding 3D models from simple inputs. Users can either chat with an intelligent agent (powered by Groq API) or fill out a structured form. The system accepts boundary drawings (uploaded images or CAD files) and generates a complete housing plan that can be downloaded as a DXF file and visualised in 3D.

### 1.2 Scope
- **Input Methods:**  
  - Chat interface using Groq API for natural language understanding and reasoning (mimicking a Gemini‑like experience)  
  - Multi‑step form with checkboxes for amenities (rooms, fixtures) and quantities  
  - Upload of boundary sketch (image: PNG/JPEG, or CAD: DXF)

- **Outputs:**  
  - 2D floor plan in DXF format (compatible with AutoCAD, LibreCAD, etc.)  
  - Interactive 3D view in the browser (Three.js) with download option (glTF/OBJ)

- **Key Features:**  
  - Groq API used for chat intelligence and layout suggestion (no other external APIs)  
  - Custom geometry engine ensures rooms never overlap and stay within boundary  
  - Handles irregular (unshaped) boundaries via polygon extraction  
  - Amenity‑based room generation with smart placement  
  - One‑click conversion from 2D plan to 3D model  

### 1.3 Target Users
- Homeowners planning a new house  
- Architects and designers seeking rapid prototyping  
- Real estate developers presenting options to clients  

---

## 2. System Overview

The system follows a client‑server architecture with a clear separation of concerns. The Groq API is used exclusively for the chat agent and optional layout reasoning; all core geometry processing remains on‑premises to guarantee precision and data privacy.

![High‑Level Architecture](architecture_diagram.png)  
*(A textual representation is provided below.)*

**Components:**

1. **Frontend (React SPA)** – Landing page, chat interface, form, 3D viewer.  
2. **Backend (FastAPI / Python)** – REST API endpoints, business logic, file handling, Groq API client.  
3. **Database (PostgreSQL)** – Stores user projects, boundary data, generated plans.  
4. **File Storage (MinIO / local)** – Stores uploaded images, CAD files, and 3D models.  
5. **Processing Modules:**  
   - Image Processor (OpenCV) – Extracts polygon from uploaded boundary sketch.  
   - Floor Plan Generator (Shapely, custom algorithm with LLM guidance) – Creates room layout.  
   - CAD Exporter (ezdxf) – Produces DXF files.  
   - 3D Model Generator (Trimesh / custom extrusion) – Creates 3D mesh.  
6. **Groq API Client** – Used for chat responses and extracting structured requirements.

All non‑chat processing is self‑contained; Groq API calls are the only external dependency.

---

## 3. Technology Stack

| Layer          | Technology Choices                                                                 | Justification                                                                 |
|----------------|-------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Frontend**   | React 18, Tailwind CSS, Three.js, React Three Fiber, Socket.IO (for chat)          | Rich UI, real‑time 3D, component reuse, large ecosystem.                     |
| **Backend**    | Python 3.10, FastAPI, Uvicorn, Groq Python SDK                                     | High performance, easy integration with scientific libraries, async support.  |
| **Database**   | PostgreSQL 14 with PostGIS (optional for spatial queries)                          | Reliable, ACID, spatial extensions for future polygon operations.             |
| **File Store** | MinIO (S3‑compatible) or local filesystem                                          | Self‑hosted, no external dependencies.                                        |
| **Processing** | OpenCV (image contour detection), Shapely (geometry), ezdxf (DXF export), Trimesh (3D) | Mature, open‑source.                                                          |
| **AI**         | Groq API (using models like Mixtral-8x7b or LLaMA3)                                | Fast inference, no need for self‑hosted LLM.                                  |
| **Deployment** | Docker, Docker Compose, Nginx (reverse proxy)                                      | Consistent environment, easy scaling.                                         |

---

## 4. Groq Integration

### 4.1 Purpose
Groq API provides the conversational intelligence for the chat‑based interaction. It also assists in extracting structured room/amenity requirements from free‑form user descriptions and can optionally suggest high‑level room arrangements (e.g., “place living room on the south side with windows”).

### 4.2 API Key Management
- The API key is stored as an environment variable (`GROQ_API_KEY`) on the backend server.  
- All requests to Groq are made from the backend, never exposed to the frontend.

### 4.3 Prompt Engineering
To make the chatbot “think like Gemini” and generate coherent, helpful responses, we design system prompts that guide the model:

- **System Prompt:**  
  “You are an AI assistant specialized in residential floor plan design. Help the user describe their dream home. Ask clarifying questions about total area, number of rooms, special amenities, and any irregular boundary shapes. Be concise and friendly. After gathering enough information, summarize the requirements in a structured format that can be used by the floor plan generator.”

- **User Input Handling:**  
  The chat history is sent with each request. The model’s response is parsed to:  
  - Extract key‑value pairs (area, room types, quantities) using regex or JSON mode.  
  - Identify when the user uploads an image (the chat includes a special token indicating an upload event).  
  - Detect commands like “generate now” to trigger the floor plan creation.

### 4.4 Fallback Mechanism
If the Groq API is unavailable or times out, a simple rule‑based chatbot takes over (using predefined questions and keyword matching). This ensures the system remains functional.

### 4.5 Cost and Performance
Groq offers fast inference; we expect each chat turn to complete in under 2 seconds. We monitor token usage and may implement rate limiting per session.

---

## 5. Module Design

### 5.1 Landing Page
- Simple, modern design with a hero section explaining the service.  
- **Call‑to‑action:** “Get Started” button that takes the user to the main workspace.  
- Footer with links to documentation and contact.

### 5.2 User Onboarding
- No mandatory registration (to lower friction).  
- A session ID is generated and stored in browser local storage; all project data is associated with this session until the user decides to save/export.  
- Option to create an account (future enhancement) for persistent storage.

### 5.3 Interaction Modes: Chat & Form

#### 5.3.1 Chat Interface (Groq‑Powered)
- Implemented using WebSocket (Socket.IO) for real‑two‑way communication.  
- Each user message is sent to the backend, which calls the Groq API with the conversation history.  
- The Groq response is streamed back to the frontend character‑by‑character for a natural feel.  
- When the user uploads an image during chat, the image is processed immediately, and the resulting polygon is attached to the conversation context (the next Groq call includes a description of the boundary).  
- The chat agent also maintains a “state” (e.g., waiting for area, waiting for room list) and can prompt the user accordingly.

**Example Conversation:**
- User: “I have 1220 sq ft area, build a home design in an unshaped boundary.”  
- Bot: “Great! I see you have an irregular boundary. Could you upload a sketch or photo of the plot? Also, how many bedrooms and bathrooms do you need?”  
- User uploads an image.  
- Bot (after processing): “I’ve extracted the boundary. It looks like an L‑shaped plot. Now, let’s decide the rooms. You mentioned 1220 sq ft. Typical for that size: 2 bedrooms, 1 bathroom, living, kitchen, dining. Does that sound right?”  
- User: “Yes, but add a study room.”  
- Bot: “Okay, study room added. Shall I generate the floor plan now?”  
- User: “Yes, generate.”

#### 5.3.2 Form Interface
- A multi‑step form that collects:
  - **Step 1:** Total area (sq ft) and optional name.  
  - **Step 2:** Boundary input (upload image/CAD or draw manually using a simple canvas editor).  
  - **Step 3:** Amenities selection:  
    - Checkboxes for each room type (Bedroom, Bathroom, Kitchen, Living, Dining, Study, etc.)  
    - For each selected room, input fields for quantity and optionally desired dimensions.  
    - Advanced amenities: garage, garden, swimming pool, etc.  
  - **Step 4:** Review and generate.

### 5.4 Boundary Upload & Processing
- **Supported formats:** PNG, JPEG, DXF.  
- **Image processing pipeline:**  
  1. Convert image to grayscale and apply Gaussian blur.  
  2. Use Canny edge detection and find contours (OpenCV).  
  3. Select the largest contour (assumed to be the boundary).  
  4. Simplify contour using Douglas‑Peucker algorithm to reduce vertex count.  
  5. Return polygon as a list of (x,y) coordinates (scaled to real dimensions using a reference scale provided by the user – e.g., “1 pixel = 0.1 ft”).  
- **DXF processing:**  
  - Parse DXF using ezdxf, extract all LINE and LWPOLYLINE entities.  
  - Merge connected lines to form a closed polygon.  
- The resulting polygon is stored in the database as a PostGIS geometry or as a JSON array.

### 5.5 Floor Plan Generation Engine
This component translates the boundary polygon and room list into a non‑overlapping floor plan.

**Inputs:**  
- Boundary polygon (closed, possibly concave).  
- Total area (used for scaling if not already consistent).  
- List of required rooms with quantities and optional desired areas (may be provided by form or extracted from chat by Groq).

**Algorithm Overview:**  
1. **Preprocessing:**  
   - If the polygon area differs from the user‑provided total area, scale the polygon accordingly.  
2. **Room Sizing:**  
   - Assign target areas to each room based on typical defaults or user preferences.  
3. **LLM‑Guided Layout Suggestion (Optional):**  
   - Before running the geometry engine, we may call Groq with a prompt like:  
     “Given a boundary polygon (list of coordinates) and a list of rooms with areas, suggest a plausible arrangement. Output as JSON with room names and approximate positions (e.g., ‘living room’ near south wall).”  
   - This suggestion is used as a seed for the packing algorithm, improving the chance of a “natural” layout.  
4. **Space Partitioning (Core Algorithm):**  
   - Use a **binary space partitioning (BSP)** approach: recursively split the polygon along its longest dimension to allocate space for rooms.  
   - Alternatively, use a **treemap‑like algorithm** that places rooms as rectangles, then morphs them to fit the polygon using a “squarified” layout and subsequent warping.  
   - **Constraint:** All rooms must remain inside the boundary and not overlap. We use Shapely operations to enforce this.  
5. **Wall Generation:**  
   - Convert room polygons into wall centerlines, then offset to create thick walls (e.g., 0.5 ft thickness).  
   - Add doors at appropriate locations (automatic placement on shared edges).  
   - Add windows on exterior walls.  
6. **Output:**  
   - A set of polygons representing walls, doors, windows, and rooms.

### 5.6 CAD File Generation
- Use `ezdxf` (Python library) to create a DXF file.  
- Layers:  
  - `WALLS` – outlines and hatches.  
  - `DOORS` – arcs and lines.  
  - `WINDOWS` – rectangles.  
  - `ROOMS` – room labels.  
- All geometry is written with real‑world units (feet or meters).  
- The DXF file is returned to the frontend for download.

### 5.7 3D Model Generation & Viewer
- From the 2D floor plan geometry, extrude walls to a standard height (e.g., 10 ft).  
- Use `Trimesh` (Python) to create a 3D mesh.  
- Add simple roof (flat or pitched) based on boundary shape.  
- Export as **glTF** (binary) for efficient web rendering.  
- Frontend uses **Three.js** (with React Three Fiber) to load and display the model.  
- User can rotate, zoom, and toggle layers.  
- A button “Make same in 3D” triggers the generation and switches to the 3D view.

### 5.8 Confirmation & Export
- After generation, the user is shown a preview of the 2D plan (SVG rendering) alongside the 3D view.  
- Buttons:  
  - **Download DXF**  
  - **Download 3D Model (glTF/OBJ)**  
  - **Edit** – returns to form/chat to modify inputs.  
  - **New Project** – resets session.

---

## 6. Data Models

**Entities:**

- `Project`  
  - `id` (UUID, PK)  
  - `session_id` (string) – for anonymous users  
  - `created_at` (timestamp)  
  - `total_area` (float) – sq ft  
  - `boundary_polygon` (JSON or PostGIS geometry)  
  - `status` (enum: drafting, processing, completed)  
  - `chat_history` (JSON) – for context continuity (optional)

- `Room`  
  - `id` (UUID, PK)  
  - `project_id` (FK)  
  - `room_type` (enum: bedroom, bathroom, kitchen, …)  
  - `quantity` (int)  
  - `desired_area` (float, nullable)  
  - `generated_polygon` (JSON) – after layout

- `Amenity` (optional advanced)  
  - Similar to Room but for non‑room features (garage, pool, etc.)

- `BoundaryUpload`  
  - `id` (UUID)  
  - `project_id` (FK)  
  - `file_path` (string)  
  - `file_type` (image/dxf)  
  - `processed_polygon` (JSON)

---

## 7. API Design

All endpoints return JSON.

| Endpoint                     | Method | Description                                      |
|------------------------------|--------|--------------------------------------------------|
| `/api/project`               | POST   | Create a new project, return `project_id`.       |
| `/api/project/{id}`          | GET    | Retrieve project details.                        |
| `/api/upload-boundary`       | POST   | Upload image/DXF, process, return polygon.       |
| `/api/generate-floorplan`    | POST   | Trigger floor plan generation (body: room list). |
| `/api/download-dxf/{id}`     | GET    | Download generated DXF file.                      |
| `/api/generate-3d/{id}`      | POST   | Generate 3D model from floor plan.                |
| `/api/3d-model/{id}`         | GET    | Retrieve glTF file for viewer.                    |
| `/api/chat`                  | WebSocket | Real‑time chat messages (backend calls Groq).   |

---

## 8. Algorithms & Logic

### 8.1 Boundary Extraction from Image
- **OpenCV pipeline** (Python):
  ```python
  import cv2
  import numpy as np

  def extract_polygon(image_path, scale_reference=None):
      img = cv2.imread(image_path)
      gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
      blurred = cv2.GaussianBlur(gray, (5,5), 0)
      edges = cv2.Canny(blurred, 50, 150)
      contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
      main_contour = max(contours, key=cv2.contourArea)
      epsilon = 0.01 * cv2.arcLength(main_contour, True)
      approx = cv2.approxPolyDP(main_contour, epsilon, True)
      polygon = approx.squeeze().tolist()
      # Scale polygon if reference provided
      return polygon
  ```

### 8.2 Floor Plan Layout Algorithm with LLM Guidance
The core algorithm combines heuristic packing with optional suggestions from Groq.

Step‑by‑step:

Normalise Boundary – Ensure polygon is closed and oriented counter‑clockwise.

Compute Total Available Area – Using Shapely area. If user‑provided area differs, scale polygon accordingly.

Room List Preparation – From form or Groq‑extracted data, create a list of rooms with target areas.

Optional LLM Suggestion

If chat was used, we may have a structured output from Groq that suggests approximate positions (e.g., “living room near entrance”). This is converted into constraints (e.g., room must touch a specific boundary edge).

Initial Placement (Rectangular Packing)

Compute the oriented bounding box of the polygon.

Sort rooms by area (largest first).

Place each room as a rectangle of required area (aspect ratio default 1:1.5 for bedrooms, 1:1 for kitchens, etc.) inside the bounding box, avoiding overlap, using a simple grid search.

Apply constraints (e.g., if a room must be on an exterior wall, its rectangle is placed against that side).

Morph to Fit Polygon

For each placed rectangle, compute its intersection with the boundary polygon (using Shapely intersection).

If the intersection area is significantly less than the target area, adjust rectangle position or size.

After all rooms are placed, use a relaxation step: move rooms slightly to eliminate overlaps and ensure they remain inside boundary.

Wall Offset

Convert each room polygon to a wall polygon by buffering outward by half wall thickness, then taking the union of all walls.

Subtract doors/windows openings.

Add Doors and Windows

For each shared edge between two rooms, add a door (if it’s an interior wall) at a random position (or centered).

For exterior walls, add windows based on room type (e.g., living room gets larger windows).

This algorithm ensures no overlap and full containment within the boundary.

### 8.3 Room Sizing & Amenity Handling
Predefined typical areas (sq ft) for each room type:

Master Bedroom: 200

Bedroom: 150

Bathroom: 50

Kitchen: 150

Living: 250

Dining: 120

Study: 100

If user provides desired area, use that.

Quantities: multiply typical area by quantity, ensuring total fits within boundary.

## 9. UI/UX Design
Wireframes (text description):

Landing Page: Full‑width background image of a house plan, central headline “Design Your Dream Home in Minutes”, subheadline, “Get Started” button.

Main Workspace:

Left sidebar with tabs: Chat / Form.

Center area: Dynamic content (chat messages or form steps).

Right panel: Preview of boundary (after upload) and final plan (SVG).

Chat View: Bubble chat with typing indicator. System prompts guide user. User can also upload images via a paperclip icon.

Form View: Step indicator at top, input fields, “Next”/“Back” buttons.

3D Viewer: Takes over the main area when activated, with controls overlay.

User Flow Diagram:
Landing → Get Started → Choose Chat or Form → Provide Info → Upload Boundary → Generate → Preview → Download / View 3D → New Project.

## 10. Implementation Plan
Phase 1: Foundation (2 weeks)
Set up project repository, Docker environment.

Implement basic FastAPI server with health check.

Create React frontend with routing and Tailwind CSS.

Implement session management.

Phase 2: Groq Integration & Chat (2 weeks)
Set up Groq API client, implement prompt templates.

Build WebSocket chat endpoint that streams Groq responses.

Implement fallback rule‑based chatbot.

Integrate image upload in chat (process image, attach context to Groq).

Phase 3: Form & Boundary Processing (2 weeks)
Build multi‑step form with dynamic fields.

Implement image upload and boundary extraction (OpenCV).

Implement DXF upload and parsing.

Phase 4: Core Generation (4 weeks)
Develop floor plan layout algorithm (with LLM guidance optional).

Integrate Shapely for geometry operations.

Generate DXF using ezdxf.

Generate 3D mesh with Trimesh and export to glTF.

Integrate Three.js viewer in frontend.

Phase 5: Integration & Polishing (2 weeks)
Connect frontend to backend APIs.

Add confirmation and download buttons.

Implement error handling and loading states.

Write unit tests and integration tests.

Phase 6: Documentation & Deployment (1 week)
Write user manual and developer guide.

Prepare Docker Compose for production.

Deploy to staging, perform UAT.

## 11. Testing Strategy
Unit Tests:

Geometry functions (Shapely operations)

DXF generation (verify layer counts)

Image contour extraction (with sample images)

Groq prompt parsing (mock responses)

Integration Tests:

Full flow: upload → generate → download

Chat message parsing with Groq mock

Performance Tests:

Load test with multiple concurrent users

Benchmark floor plan generation time (< 10 seconds for typical input)

Browser Compatibility: Chrome, Firefox, Safari (latest versions).

## 12. Deployment Guide
12.1 Prerequisites
Docker and Docker Compose installed on server.

Domain name (optional) and SSL certificate (for production).

Groq API key (obtain from console.groq.com).

12.2 Docker Compose Configuration
yaml
version: '3.8'
services:
  postgres:
    image: postgis/postgis:14-3.3
    environment:
      POSTGRES_DB: floorplan
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - pgdata:/var/lib/postgresql/data
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - miniodata:/data
  backend:
    build: ./backend
    depends_on:
      - postgres
      - minio
    environment:
      DATABASE_URL: postgresql://user:pass@postgres/floorplan
      MINIO_ENDPOINT: minio:9000
      GROQ_API_KEY: ${GROQ_API_KEY}
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: http://localhost:8000
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
volumes:
  pgdata:
  miniodata:
12.3 Environment Variables
DATABASE_URL – PostgreSQL connection string.

MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY.

GROQ_API_KEY – Your Groq API key.

SECRET_KEY – for session signing.

12.4 Steps to Deploy
Clone repository on server.

Configure environment variables in .env file (including GROQ_API_KEY).

Run docker-compose up -d.

Set up Nginx reverse proxy with SSL (Let's Encrypt).

Monitor logs with docker-compose logs -f.

## 13. Documentation
13.1 User Manual
How to start a project.

Using the chat assistant (Groq‑powered).

Filling the form.

Uploading boundary sketches.

Interpreting the generated plan.

Downloading files and viewing 3D.

13.2 Developer Guide
Project structure overview.

Setting up development environment (including Groq API key).

Adding new room types and updating prompts.

Extending the floor plan algorithm.

API reference.

All documentation will be maintained in the /docs folder of the repository in Markdown format, and a web version will be served at /docs on the live site.

## 14. Conclusion
The AutoCAD Floor Plan Generator leverages Groq API for a smart, conversational experience while maintaining a robust, on‑premises geometry engine to guarantee non‑overlapping, boundary‑compliant floor plans. This hybrid approach combines the best of AI‑driven interaction with precise, rule‑based generation, resulting in a powerful tool for rapid home design. The system is fully containerised and ready for deployment, following industry best practices.

This document serves as the complete blueprint for development and deployment. All components are open‑source and can be extended or customised as needed.
