# 🛡️ ShadowTrap AI

> **An AI-Powered Adaptive Honeypot & Deception Platform for Real-Time Threat Analysis, Attacker Persona Generation, Behavior Intelligence, and Autonomous SOC Response.**

ShadowTrap AI is an enterprise-grade Security Operations Center (SOC) intelligence and deception platform. Rather than acting as a traditional passive firewall, ShadowTrap AI lures, detains, observes, analyzes, and explains threat actor behavior across dual deception environments: a public-facing **Decoy Corporate Web Trap** and an interactive **Cowrie SSH/Telnet Honeypot**.

---

## 🌟 Key Features & Capabilities

### 🌐 Dual Deception Architecture
* **Web Deception Trap**: Public decoy website (**TechNova Solutions**) with a fake admin console (`/admin`) that silently collects browser telemetry, hardware fingerprints, form inputs, and ergonomic mouse/keyboard behavior.
* **Cowrie SSH/Telnet Honeypot**: Interactive shell emulation capturing keystrokes, brute-force credentials, remote file payload downloads, and terminal execution patterns.

### 🧠 Advanced AI & Behavioral Analytics Engine
* **🎯 10-Stage MITRE-Aligned Attack Progression Detector**: Automatically maps incoming session commands to 10 distinct attack stages:
  $$\text{Reconnaissance} \rightarrow \text{Discovery} \rightarrow \text{Credential Theft} \rightarrow \text{Payload Download} \rightarrow \text{Privilege Escalation} \rightarrow \text{Persistence} \rightarrow \text{Defense Evasion} \rightarrow \text{C2} \rightarrow \text{Collection} \rightarrow \text{Exfiltration}$$
* **🎭 Attacker Persona & Intent Classifier**: Evaluates sophistication scores ($0{-}100$), skill levels (*Beginner*, *Intermediate*, *Advanced*, *Expert*), threat intent (*Ransomware Staging*, *Botnet Dropper*, *Credential Harvesting*, *Espionage*), and primary motivations.
* **🔮 Markov-Chain Next Attack Predictor**: Utilizes probabilistic transition matrices to predict an attacker's next likely commands and tactics.
* **📐 Behavioral Vector Embedding & Anomaly Detection**: Converts command line sequences into high-dimensional vector embeddings to quantify deviation from baseline behavior.
* **📊 Composite Threat Scoring Engine ($0{-}100$)**: Synthesizes command risk, stage depth, duration, and downloaded payloads into a single actionable threat index.

### 🤖 Local AI Copilot & LLM Threat Explanation
* **Security Copilot**: AI-powered SOC assistant supporting local GGUF models (`llama-server.exe` / `llama.cpp`) and Hugging Face inference models with intelligent offline rule fallbacks.
* **Natural Language Explanation**: Generates detailed incident summaries, root-cause analyses, MITRE ATT&CK technique breakdowns, and immediate remediation steps.

### 📢 Incident Response & Real-Time Alerting
* **Telegram Bot Integration**: Pushes instant security alert notifications to Telegram channels when high-severity threat thresholds or honeypot breaches occur.
* **Socket.IO Real-Time Stream**: Pushes live attack events, active session updates, and trap visitor telemetry directly to the SOC Sentinel dashboard.

### 🎬 Forensics & Visualization
* **Interactive Session Playback**: Step-by-step terminal execution replay with multi-speed controls ($0.5\times$, $1\times$, $2\times$, $4\times$).
* **Interactive Knowledge Graph**: Visualizes interconnected relationships between attacker IPs, session IDs, used credentials, executed commands, and MITRE techniques.
* **Executive PDF & JSON Security Reports**: Generates downloadable PDF reports with ReportLab for compliance and executive briefings.

---

## 🏗️ System Architecture

```
                               ┌─────────────────────────────────────────┐
                               │      ATTACKER / REMOTE HOST (LAN/WAN)   │
                               │       (Kali Linux VM / External IP)     │
                               └────────────────────┬────────────────────┘
                                                    │
                ┌───────────────────────────────────┴───────────────────────────────────┐
                │                                                                       │
                ▼ (Port 5173 / HTTP)                                                    ▼ (Port 22/23 / SSH/Telnet)
 ┌──────────────────────────────────────────────┐                        ┌──────────────────────────────────────────────┐
 │       Frontend Decoy Trap (TechNova)         │                        │           Cowrie SSH/Telnet Honeypot         │
 │  - Silent Canvas & WebGL Fingerprinting      │                        │  - Shell Emulation & Keystroke Logging       │
 │  - DevTools Detection (F12 / Inspect)        │                        │  - File Download & Command Capture           │
 │  - Form Traps & Mouse Ergonomics Tracking    │                        └──────────────────────┬───────────────────────┘
 └──────────────────────┬───────────────────────┘                                               │ Raw JSON Logs
                        │ Telemetry (sendBeacon)                                                ▼
                        │                        ┌──────────────────────────────────────────────────────────────┐
                        │                        │ Autonomous Cowrie Log Collector Daemon (log_collector.py)    │
                        │                        └──────────────────────┬───────────────────────────────────────┘
                        │                                               │ Parsed Log Stream
                        └──────────────────────┬────────────────────────┘
                                               ▼
                        ┌──────────────────────────────────────────────┐
                        │       Flask + Socket.IO Backend API          │
                        │       (Bound to 0.0.0.0:5000 with CORS)      │
                        └──────────────────────┬───────────────────────┘
                                               │
          ┌────────────────────────────────────┼────────────────────────────────────┐
          ▼                                    ▼                                    ▼
 ┌─────────────────────────┐        ┌─────────────────────────┐        ┌─────────────────────────┐
 │   AI & Security Engine  │        │   Services & Telegram   │        │     Security Copilot    │
 │ - 10-Stage Detector     │        │ - Threat Score Engine   │        │ - Local llama-server    │
 │ - Intent & Personas     │        │ - Telegram Alert Bot    │        │ - HuggingFace Inference │
 │ - Markov Predictor      │        │ - IP Geolocation & ASN  │        │ - Rule-Based Engine     │
 │ - Behavioral Embeddings │        │ - PDF Report Generator  │        └─────────────────────────┘
 └────────────┬────────────┘        └────────────┬────────────┘
              │                                  │
              └─────────────────┬────────────────┘
                                ▼
             ┌─────────────────────────────────────┐
             │          MongoDB Database           │
             │  (Sessions, Trap Visitors, Reports) │
             └──────────────────┬──────────────────┘
                                │ REST APIs & Socket.IO WebSockets
                                ▼
             ┌─────────────────────────────────────┐
             │   SOC Sentinel Operations Center    │
             │  (Hidden Dashboard at /sentinel)    │
             └─────────────────────────────────────┘
```

---

## 🎯 Monitored Attack Vectors & Threat Intelligence

ShadowTrap AI captures and analyzes a broad range of malicious activities:

### 1. Web Deception & Browser Reconnaissance
* **DevTools & Inspection Trap (`devtools_detected`)**: Detects when an attacker inspects element source code or opens Developer Tools (`F12`).
* **Silent Fingerprinting**: Captures WebGL GPU vendor/renderer signatures, Canvas hashes, screen resolutions, system color depths, hardware concurrency, and time zones.
* **Bot Ergonomic Tracking**: Analyzes mouse move speed, scroll depths, click patterns, and keystroke frequencies to distinguish automated vulnerability scanners from human attackers.
* **Decoy Web Admin Console**: Provides a realistic, fake administration panel (`/admin`) to entrap web attackers and collect credentials.

### 2. SSH & Telnet Honeypot Attacks
* **Brute-Force & Credential Spraying**: Logs automated login attempts (`hydra`, `medusa`, `crowbar`) and password dictionaries.
* **System Environment Discovery**: Tracks commands probing kernel versions, network configurations, and active users (`uname -a`, `cat /etc/issue`, `ifconfig`, `whoami`).
* **Privilege Escalation & Persistence**: Detects attempts to read `/etc/shadow`, check `sudo` permissions, or modify `/etc/crontab` and `authorized_keys`.
* **Malware Droppers & C2 Registration**: Identifies file download commands (`wget`, `curl`, `fetch`), botnet binaries (e.g. Mirai variants), and staging scripts.
* **Anti-Forensics & Log Cleansing**: Captures commands attempting to wipe logs or clear command histories (`rm -rf /var/log`, `history -c`, `unset HISTFILE`).

---

## 📂 Project Repository Structure

```
ShadowTrap AI/
├── backend/
│   ├── app/
│   │   ├── ai/                 # AI/ML Analytics Modules
│   │   │   ├── stage_detector.py         # 10-stage MITRE attack stage classifier
│   │   │   ├── intent_detector.py        # Attacker intent & motivation inference
│   │   │   ├── persona_generator.py      # Sophistication & persona builder
│   │   │   ├── next_attack_predictor.py  # Markov-chain transition predictor
│   │   │   ├── behavior_embedding.py     # Command sequence vector embeddings
│   │   │   ├── anomaly_detector.py       # Behavioral anomaly detection
│   │   │   └── explainability.py         # Explainable AI metrics
│   │   ├── blueprints/         # Flask REST API Blueprints
│   │   │   ├── auth.py                   # JWT Auth & User Management
│   │   │   ├── attacks.py                # Attack session queries & filters
│   │   │   ├── trap.py                   # Decoy visitor telemetry ingestion
│   │   │   ├── replay.py                 # Interactive playback endpoint
│   │   │   ├── reports.py                # PDF & JSON report generation
│   │   │   ├── threat_intel.py           # Geolocation & IP intelligence
│   │   │   ├── analytics.py              # SOC dashboard metrics & stats
│   │   │   ├── ai_models.py              # AI inference status endpoints
│   │   │   ├── knowledge_graph.py        # Node-link graph data endpoints
│   │   │   └── remaining.py              # Auxiliary operational routes
│   │   ├── data/               # Static Data & Templates
│   │   │   ├── sample_cowrie_logs.json   # Seed dataset for Cowrie events
│   │   │   └── mitre_attack_mapping.json # Offline MITRE ATT&CK database
│   │   ├── models/             # PyMongo MongoDB Models (Attack, User, TrapVisitor)
│   │   ├── services/           # Core Application Services
│   │   │   ├── cowrie_service.py         # Cowrie JSON log parser
│   │   │   ├── threat_score_service.py   # Composite threat index engine
│   │   │   ├── llm_service.py            # Local Llama / HF inference service
│   │   │   ├── copilot_service.py        # Security Copilot assistant engine
│   │   │   ├── telegram_service.py       # Real-time Telegram alert integration
│   │   │   ├── ip_intel_service.py       # IP Geolocation & ASN lookup
│   │   │   ├── mitre_service.py          # Local MITRE technique mapper
│   │   │   ├── report_service.py         # ReportLab PDF compilation
│   │   │   ├── knowledge_graph_service.py# Relationship graph builder
│   │   │   └── deception_service.py      # Adaptive deception payload engine
│   │   ├── utils/              # Colored logging, JWT decorators, validators
│   │   ├── config.py           # Application configuration & CORS settings
│   │   ├── extensions.py       # PyMongo, JWTManager, SocketIO singletons
│   │   └── __init__.py         # Flask App Factory & database seeder
│   ├── log_collector.py        # Background process monitoring Cowrie log files
│   ├── run.py                  # Backend server entry point (Port 5000)
│   ├── requirements.txt        # Python dependencies
│   └── .env.example            # Environment template
├── frontend/
│   ├── src/
│   │   ├── api/                # Axios API client & endpoint helpers
│   │   ├── components/         # Glassmorphic UI components & Attack Simulator
│   │   ├── context/            # AuthContext & ThemeContext providers
│   │   ├── pages/              # Main Frontend Views
│   │   │   ├── DecoyPage.jsx             # Public Decoy Corporate Landing Page
│   │   │   ├── DecoyAdminLogin.jsx       # Fake Admin Login Page
│   │   │   ├── DecoyAdminConsole.jsx     # Fake Decoy Admin Console Trap
│   │   │   ├── Dashboard.jsx             # Main SOC Sentinel Dashboard
│   │   │   ├── LiveSessions.jsx          # Live active SSH/Telnet sessions
│   │   │   ├── Attacks.jsx               # Comprehensive attack session log
│   │   │   ├── AttackDetails.jsx         # Detailed session investigation view
│   │   │   ├── AttackReplay.jsx          # Interactive terminal session replay
│   │   │   ├── TrapVisitors.jsx          # Web decoy visitor telemetry view
│   │   │   ├── ThreatIntelligence.jsx    # Attacker IP profiles & geolocations
│   │   │   ├── MitreMatrix.jsx           # Interactive MITRE ATT&CK matrix
│   │   │   ├── KnowledgeGraph.jsx        # Threat actor node-link graph
│   │   │   ├── SecurityCopilot.jsx       # AI Copilot chat interface
│   │   │   ├── Reports.jsx               # Executive report export page
│   │   │   ├── Analytics.jsx             # Advanced SOC metrics & charts
│   │   │   └── Login.jsx                 # SOC Sentinel Login view
│   │   ├── lib/                # Socket.IO client initialization
│   │   ├── App.jsx             # Router configuration
│   │   └── main.jsx            # React entry point
│   ├── index.html
│   ├── vite.config.js          # Vite config (Listens on 0.0.0.0:5173)
│   └── package.json
├── Dockerfile                  # Backend Docker container definition
├── Dockerfile.frontend         # Frontend Docker container definition
├── docker-compose.yml          # Multi-container orchestration (MongoDB, Redis, Backend, Frontend)
└── README.md
```

---

## 🔌 Core API Endpoints

| Category | Endpoint | Method | Description |
| :--- | :--- | :--- | :--- |
| **Auth** | `/api/v1/auth/login` | `POST` | Authenticate SOC analyst & retrieve JWT token |
| **Auth** | `/api/v1/auth/me` | `GET` | Get current authenticated analyst profile |
| **Attacks** | `/api/v1/attacks` | `GET` | Paginated list of attack sessions with filtering |
| **Attacks** | `/api/v1/attacks/<id>` | `GET` | Retrieve full attack session details & timeline |
| **Replay** | `/api/v1/replay/<id>` | `GET` | Retrieve step-by-step terminal execution data |
| **Trap** | `/api/v1/trap/telemetry` | `POST` | Ingest silent browser & hardware telemetry |
| **Copilot** | `/api/v1/copilot/query` | `POST` | Query Security Copilot AI for threat analysis |
| **Intel** | `/api/v1/intel/ip/<ip>` | `GET` | Fetch IP geolocation, ASN, & threat reputation |
| **Graph** | `/api/v1/graph/data` | `GET` | Retrieve threat actor knowledge graph nodes & links |
| **Reports** | `/api/v1/reports/pdf/<id>`| `GET` | Generate and download executive PDF incident report |
| **Analytics**| `/api/v1/analytics/stats` | `GET` | Fetch high-level SOC dashboard metrics & counts |

---

## 🚀 Deployment & Installation

### Prerequisites
* **Python**: `3.10` or higher
* **Node.js**: `18.x` or higher
* **Database**: MongoDB server running locally or accessible via URI (Default: `mongodb://localhost:27017/shadowtrap`)

---

### Option 1: Manual Step-by-Step Setup

#### 1. Setup Backend
```bash
cd backend

# Create & activate virtual environment (optional)
python -m venv venv
# Windows: venv\Scripts\activate | Linux/macOS: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from template
cp .env.example .env

# Run backend server
python run.py
```
> The Flask & Socket.IO backend will start on **`http://0.0.0.0:5000`**.

#### 2. Start Cowrie Log Collector (Optional for real Cowrie integration)
```bash
cd backend
python log_collector.py
```

#### 3. Setup Frontend
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```
> The Vite development server will start on **`http://0.0.0.0:5173`**.

---

### Option 2: Docker Compose Deployment

Deploy the entire stack (MongoDB, Redis, Flask Backend, Vite Frontend) with a single command:

```bash
docker-compose up --build -d
```

- **Decoy Web Trap**: `http://localhost/`
- **SOC Sentinel Dashboard**: `http://localhost/sentinel/login`

---

## 🔑 Default SOC Credentials

To access the SOC Sentinel Operations Center:
* **URL**: `http://<HOST-IP>:5173/sentinel/login`
* **Email**: `admin@shadowtrap.ai`
* **Password**: `ShadowTrap@2024`

---

## 📱 Telegram Alert Integration Setup

To enable real-time Telegram notifications for critical threats:
1. Create a Telegram Bot via `@BotFather` and copy the API token.
2. Get your Chat ID using `@userinfobot`.
3. Add the keys to your `backend/.env` file:
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```
4. Restart the backend service. High-risk events will automatically trigger push notifications.

---

## 🔒 Security & Privacy Features

* **JWT Token Security**: Access and refresh token pair rotation with secure authorization headers.
* **Password Hashing**: Cryptographic password hashing using `bcrypt` (work factor 12).
* **Network Binding**: Configured to bind on `0.0.0.0` with explicit CORS origin controls for local network / VM access (e.g., testing via Kali Linux).
* **Offline Processing**: MITRE ATT&CK mapping, threat scoring, and rule-based AI operate completely offline with zero external API dependencies required.

---

## 📜 License

ShadowTrap AI is an enterprise cybersecurity intelligence and deception platform designed for high-assurance threat monitoring, deception research, and SOC operations.
