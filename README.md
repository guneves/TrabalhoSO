# OS Scheduler Simulator

# 🚀 Operating System Scheduler Simulator

This project is a process scheduling algorithm simulator (FIFO, SJF, RR, EDF, CFS) developed for the Operating Systems course.

The goal is to define processes via an interactive web interface, execute the simulation, and generate a Gantt chart and performance metrics. Additionally, it includes a virtual memory management simulation with page replacement policies (FIFO, LRU).

## 🔧 Environment Setup

Follow these steps to set up your local development environment.

### 1. Clone the Repository

```bash
git clone <repository-url>
cd simulador_so
```

### 2. Create and Activate a Virtual Environment (venv)

We recommend using `.venv` as the environment name so it's automatically ignored by `.gitignore`.

#### macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Windows (PowerShell)
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

With the virtual environment activated, install the required libraries:

```bash
pip install -r requirements.txt
```

You're all set! Now you can run the project.

# 🏃 How to Run

The project uses a **Streamlit web application** as its entry point, located at `web_app/app.py`.

To start the application, run:

```bash
streamlit run web_app/app.py
```

This will open a browser window with the simulator interface.

## Features

### Scheduling Algorithms
- **FIFO**: First In, First Out
- **SJF**: Shortest Job First
- **RR**: Round Robin
- **EDF**: Earliest Deadline First
- **CFS**: Completely Fair Scheduler (simulated version)

### Virtual Memory Management (Bonus)
- Page fault handling
- Page replacement policies: FIFO, LRU
- RAM frame visualization
- Inverted page table visualization
- Disk swapping visualization

### Metrics
- Turnaround time
- Waiting time
- Deadline compliance
- CPU utilization
- Throughput
- Number of context switches
- Total page faults
