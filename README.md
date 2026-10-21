# Cloud Resource Management System Using a Lazy Segment Tree

## Project Overview

This project simulates cloud CPU resource allocation across discrete time slots. It uses a Lazy Segment Tree to support efficient range queries and range updates while managing task allocation and resource release.

## Problem Statement

Manage CPU resources across time slots while ensuring that tasks are allocated only when sufficient resources are available.

## Main Features

- CPU resource allocation and release
- Resource availability checks
- Conflict detection
- Lazy Segment Tree for efficient range operations
- Strict and reserve-based allocation policies
- Task management
- Allocation logging and statistics
- Automated tests
- User interface, if included in the final version

## Technologies Used

- Python
- Data Structures and Algorithms
- Lazy Segment Tree
- Git and GitHub
- Streamlit, if the graphical interface is included

## Project Structure

- `main.py` — terminal interface
- `demo.py` — demonstration program
- `src/segment_tree.py` — Lazy Segment Tree implementation
- `src/manager.py` — CPU resource management
- `src/models.py` — task and allocation-result models
- `src/policies.py` — allocation policies
- `src/observers.py` — logging and statistics
- `tests/` — automated tests
- `app.py` — graphical interface, if included

## Setup

Install Python 3 if it is not already installed.

Install project dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the terminal application:

```bash
python main.py
```

Run the demonstration:

```bash
python demo.py
```

Run the graphical interface, if `app.py` is included:

```bash
python -m streamlit run app.py
```

Run the tests using the command appropriate for the test framework used in this project.

For example, if the project uses pytest:

```bash
python -m pytest
```

## Team Contributions

Each team member is responsible for a designated part of the project. Individual contributions are tracked through GitHub commits.

## Academic Project

Developed as part of a Data Structures and Algorithms laboratory mini-project.