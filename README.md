# Super Ainux system: Development guide

##  Authors: Dr. Jin Ling, Dr. Chaofei Gao

## Update date: 2026/03/21

## Background
OpenClaw has become extremely popular recently. Its emergence has made it possible for LLM to operate computers to perform diverse tasks, opening up new scenarios for AI applications. However, it also has many drawbacks:
  - AI has extremely high system privileges, posing potential security risks to users' files and data.
  - Operating systems and software are designed specifically for humans, making AI calls difficult and unable to perform all operations.
  - The basic operating objects of existing systems are files, which is not conducive to AI management and processing, resulting in low execution efficiency.
Ultimately, existing operating systems are designed for human users rather than for AI. Therefore, we propose to design an operating system specifically for AI use.

**Super Ainux** is an operating system specifically designed for artificial intelligence. 

## Hardware architecture
  - x86_64

## System Kernel
  - Linux 6.19.6

## System Features
  - AIs are the owner, supervisor and operator of the system. Users are leaders.
  - The system should be operated by at least two AIs together,one being the supervisor and the other bing the operator.
  - Tasks are the processing objects of the system. Files are merely carriers for the transmission of input and output.
  - Plans, tools (programs), file templates, skills, and user data are involved in handling tasks. Some of them can be obtained from online libraries or local libraries.
  - There is no operation interface. Only the task dashboard including task status, hardware status, result display, input and output areas.
  - Tools, the existing programs, will be gradually iterated into Ai-specific programs switching from interface operation to interface invocation to adapt to the system..
  
## Special Subsystem
  - Supervision subsystem
  - Task subsystem
  - Information organization subsystem
  - Analysis subsystem
  - Advanced log system

### Comparison between SAS and Traditional OS

| Feature | Traditional OS (Windows, macOS, Linux) | Super Ainux System |
| :--- | :--- | :--- |
| **Core Philosophy** | User-centric resource management & GUI | AI-centric automated operation system |
| **Primary Actor** | **User** is the operator; OS is a passive tool | **AI** is the owner/operator; User is the Leader |
| **Operational Logic** | Single-user or multi-user concurrent tasks | **Dual-AI Collaboration** (Supervisor + Operator) |
| **Processing Object** | Processes, Threads, and Files | **Tasks** (The core unit of operation) |
| **Interface (UI)** | GUI (Windows/Icons) or CLI (Terminal) | **Task Dashboard** (Status, Hardware, Results) |
| **Application Type** | Interactive software (Human-operated) | **AI-specific programs** (API/Invocation-driven) |
| **Resource Acquisition** | Manual installation/download by user | Automated retrieval from **Online/Local Libraries** |
| **Security/Audit** | Permissions, Firewalls, and User Passwords | Real-time audit by the **Supervision Subsystem** |

## M0 engineering (baseline host & secrets)

Implementation for milestone **M0** (Linux baseline, single-node Podman Compose, split secrets/config): see [`m0/README.md`](m0/README.md) and the walkthrough [`docs/M0_DEPLOYMENT.zh.md`](docs/M0_DEPLOYMENT.zh.md).

**M1** (task state machine API, append-only audit with hash chain, stub Operator/Supervisor): [`m1/README.md`](m1/README.md), [`docs/M1_API.zh.md`](docs/M1_API.zh.md).
