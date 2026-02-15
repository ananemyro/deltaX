# deltaX

**deltaX** is a space mission simulator where you play as Mission Control.  
You don't fly the ship directly - instead, you influence its fate through small propulsions and critical decisions made during planetary encounters.

The objective is simple:

**Reach Earth.**

But the universe fights back. Resources decay, failures emerge, and the longer the journey lasts, the more unstable the system becomes.

This project demonstrates:

- **Entropy:** systems naturally drift toward disorder over time  
- **Butterfly Effect:** small early actions can cause massive long-term trajectory changes  
- **Decision-based survival:** every planet interaction shapes your outcome  

---

## Gameplay

You may succeed or fail in multiple ways:

- Reach Earth (**Success**)  
- Crash into a planet (**Fail**)  
- Miss Earth completely (**Fail**)  
- Run out of resources (oxygen / water / morale / etc.) (**Fail**)  

The game includes dynamic prompts at planets where you must decide whether to stop and repair systems - at a cost.

---

## Tech Stack

- **Backend:** Python + Flask
- **Frontend:** HTML/CSS/JavaScript

---

# Setup Instructions

## Backend (Flask API)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
 ```
## Frontend (Web Client)

```bash
cd frontend
python -m http.server 8000
 ```

---

## Controls

- Use the Mission Control joystick to apply propulsion burns.
- Latch onto planets to trigger decision prompts.
- Keep an eye on the resource bars and trajectory carefully.

---

## Hackathon Theme: 10

*Ten little astronauts flying way up high.
One drifted off too far, and then there were nine.*

---

## Team

- Anastasiia Nemyrovska
- Yun Lei Lin
