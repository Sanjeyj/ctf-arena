# Competition Setup & Scoring

Configure time-bounded events and select scoring algorithms that match your tournament style.

---

## 1. Event Scheduling

In **Admin → Competition**, you can configure:
- **Start Time**: When flag submission begins.
- **End Time**: When scoring ends.
- **Is Active**: Toggles platform accessibility.
- **Is Paused**: Temp halts score updates.
- **Freeze Time**: Restricts public scoreboard updates past this timestamp (allows organizers to build hype during final hours).

---

## 2. Point Allocation & Decay

CTF Arena v2 supports three scoring modes:

### Static Points
Challenges have a fixed value (e.g. 100 points) that never changes, regardless of when it is solved or by how many teams.

### Legacy Time Decay
Points reduce gradually as time passes:
- Decrements by 1 point per 10 seconds of competition elapsed.
- Hard floor bounds at `minimum_points` configuration.

### Dynamic Decay
Points decay as the number of solvers increases. Encourages finding unique exploits:
- Points decrease dynamically with each successful solve on the challenge.
