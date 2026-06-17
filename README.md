# Operating System Simulator

An interactive Operating System simulator focused on CPU scheduling, process state transitions, virtual memory, page replacement, and real-time visualization.

The project was built for an Operating Systems course. It lets users configure processes, choose a scheduling algorithm, enable paged virtual memory, run the simulation tick by tick, and inspect CPU, queue, RAM, swap, a tick-based timeline, and final performance metrics.

## Main Features

### CPU Scheduling

The simulator supports the following scheduling algorithms:

- **FIFO**: First In, First Out. Processes are executed in arrival order.
- **SJF**: Shortest Job First. The ready process with the smallest CPU burst is selected first.
- **Round Robin**: Time-sliced preemptive scheduling with a configurable quantum.
- **EDF**: Earliest Deadline First. The process with the closest absolute deadline has priority.
- **CFS Simulation**: A simplified Completely Fair Scheduler based on virtual runtime.

The simulator tracks:

- process arrivals;
- ready queue ordering;
- running process;
- context switches;
- preemptions;
- idle CPU time;
- per-process completion time;
- deadline compliance.

### Virtual Memory

Virtual memory can be enabled or disabled from the web interface.

When enabled, each process may have a configurable number of logical pages. On each CPU execution tick, the running process requests one of its pages. The memory manager then decides whether the access is a page hit or a page fault.

Supported page replacement policies:

- **FIFO**: replaces the page that entered RAM first;
- **LRU**: replaces the least recently used page.

The memory simulation includes:

- physical RAM frames;
- inverted page table data;
- page hits and page faults;
- page fault blocking cost;
- per-process memory counters;
- current swap contents;
- recent swap history;
- real-time visualization of pages loaded in RAM.

### Real-Time Visualization

The Streamlit interface shows the simulation as it runs:

- current CPU state;
- running process;
- ready queue;
- processes blocked by memory;
- process table with runtime state;
- tick-based CPU/process timeline;
- current memory access;
- processes resident in RAM;
- RAM frame grid;
- swap and recent swap history.

The goal is to make CPU scheduling and memory behavior visible while the simulation evolves, not only after it finishes.

## Metrics

The final result panel includes global and per-process metrics.

### Global Metrics

- **Total time**: total simulated time units.
- **CPU idle time**: time units where no process ran.
- **Context switch overhead**: total time spent in context switch overhead.
- **Accumulated memory block time**: sum of all process time spent blocked by page faults. This is accumulated per process, so it can be greater than the total simulation time when multiple processes are blocked at the same time.
- **Page fault ticks**: number of ticks where page faults were triggered.
- **Context switches**: total number of process switches.
- **Preemptions**: number of forced interruptions caused by quantum expiration or algorithm rules.
- **Throughput**: completed processes divided by total simulation time.
- **CPU utilization**: CPU execution time divided by total simulation time.
- **CPU idleness**: idle time divided by total simulation time.
- **Average turnaround**: average time from process arrival to completion.
- **Average ready-queue wait**: average time each process spent waiting in the ready queue.

### Per-Process Metrics

- **Arrival**: process arrival time.
- **Execution**: required CPU execution time.
- **Deadline**: relative deadline configured by the user.
- **Real deadline**: arrival time plus relative deadline.
- **Priority**: process priority, used by CFS simulation.
- **Start**: first time the process received CPU.
- **Finish**: completion time.
- **Turnaround**: finish time minus arrival time.
- **Ready wait**: time spent waiting in the ready queue.
- **Memory block time**: time spent blocked by page faults.
- **Not executing**: turnaround minus CPU execution time.
- **Page hits**: successful page accesses.
- **Page faults**: page accesses that required loading/replacing a page.
- **Deadline OK**: whether the process finished before or at its real deadline.

## Project Structure

```text
.
├── README.md
├── requirements.txt
├── src
│   ├── processo.py
│   ├── simulador.py
│   ├── memoria.py
│   ├── metricas.py
│   ├── visualizacao.py
│   └── escalonadores
│       ├── base.py
│       ├── fifo.py
│       ├── sjf.py
│       ├── round_robin.py
│       ├── edf.py
│       └── cfs.py
└── web_app
    └── app.py
```

### Core Modules

- `src/processo.py`: defines the `Processo` class and stores process state, timing, memory counters, and final metrics.
- `src/simulador.py`: discrete-event simulation engine. It controls arrivals, CPU dispatching, preemption, context switching, page fault blocking, snapshots, and final metrics.
- `src/memoria.py`: virtual memory manager. It manages RAM frames, page hits, page faults, FIFO/LRU replacement, swap, and memory visualization data.
- `src/metricas.py`: builds final process tables and global metric summaries.
- `src/visualizacao.py`: contains optional Matplotlib plotting helpers kept for standalone visual checks.
- `src/escalonadores/`: contains scheduling algorithm implementations.
- `web_app/app.py`: Streamlit application and user interface.

## Requirements

- Python 3.10 or newer recommended.
- Python packages listed in `requirements.txt`:
  - `streamlit`
  - `pandas`
  - `matplotlib`

## Setup

### 1. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

Start the Streamlit app:

```bash
streamlit run web_app/app.py
```

Or, on Windows using the local virtual environment:

```powershell
.\venv\Scripts\python.exe -m streamlit run web_app/app.py
```

Then open the URL shown by Streamlit, usually:

```text
http://localhost:8501
```

## How to Use

1. Choose the scheduling algorithm in the sidebar.
2. Configure the quantum and context-switch overhead.
3. Enable or disable virtual memory.
4. Select the page replacement policy, RAM frame count, page fault cost, and random seed.
5. Edit the process table:
   - enable or disable processes;
   - set arrival time;
   - set execution time;
   - set relative deadline;
   - set priority;
   - set number of pages.
6. Click **Run simulation**.
7. Observe the CPU, queue, memory, swap, tick timeline, and final metrics.

## Notes About the Memory Model

The virtual memory model is intentionally educational and simplified:

- each process has a fixed number of logical pages;
- page requests are pseudo-random but deterministic through the configured seed;
- a page fault blocks the requesting process for the configured disk cost;
- while a process is blocked by memory, the CPU may continue running other ready processes;
- RAM has a configurable number of frames;
- page replacement occurs only when RAM is full and a requested page is not resident;
- swap history records recent page evictions even if those pages later return to RAM.

## Development and Validation

To quickly validate Python syntax:

```powershell
.\venv\Scripts\python.exe -m compileall src web_app
```

To run a simple engine-level test, import the simulator classes from `src` and instantiate processes, a scheduler, and optionally a memory manager.

## Educational Purpose

This simulator is designed to help students understand how scheduling and virtual memory interact:

- CPU algorithms decide which ready process runs;
- memory accesses may block a process;
- blocked processes leave the CPU available for other ready processes;
- page replacement changes RAM contents over time;
- final metrics reflect both scheduling decisions and memory behavior.
