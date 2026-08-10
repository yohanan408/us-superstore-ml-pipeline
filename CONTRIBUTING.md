#  Git Feature Branch & Deployment Update Checklist

Follow this sequence exactly whenever initializing a new feature, fixing a pipeline bug, or deploying a model retrain.

---

###  Phase 1: Isolation & Local Setup
Before writing any code or prompting your agent, isolate your production tracking.
- [ ] **Sync local main:** Ensure your environment matches the live server.
      ```bash
      git checkout main
      git pull origin main
      ```
- [ ] **Spin up a dedicated Feature Branch:** Name it descriptively based on the task category.
      ```bash
      # Naming templates: feat/feature-name, bugfix/issue-name, refactor/change-name
      git checkout -b feat/add-retrain-automation
      ```

---

###  Phase 2: Sandbox Testing & Implementation
Allow the AI agent or yourself to modify the code files inside the isolated branch.
- [ ] **Execute Changes:** Update scripts in `src/`, modify endpoints in `app/main.py`, or update documentation.
- [ ] **Update Dependencies:** If you imported a new python package, lock it down instantly.
      ```bash
      pip freeze > requirements.txt
      ```

---

###  Phase 3: Continuous Integration (The Quality Gate)
Never merge code that hasn't passed local unit validation.
- [ ] **Clear Runtime Caches:** Ensure no old local cache states are skewing results.
- [ ] **Run the Pytest Suite:** Execute your automated test shield in verbose mode.
      ```bash
      pytest tests/ -v
      ```
- [ ] **Verify 100% Pass Rating:** If any test fails, halt the workflow immediately, debug the processing matrix, and re-run until all checkmarks are green.

---

###  Phase 4: Staging & Remote Pull Request
Push your isolated changes to the cloud repository for peer review.
- [ ] **Audit Git Status:** Verify only intentional files are staged (no massive dataset logs or secure token variables).
      ```bash
      git status
      ```
- [ ] **Commit with Semantic Messaging:** Write a clear message detailing the architectural change.
      ```bash
      git add .
      git commit -m "feat: implement automated retraining script with logging triggers"
      ```
- [ ] **Push Feature Branch to GitHub:**
      ```bash
      git push -u origin feat/add-retrain-automation
      ```
- [ ] **Open a Pull Request (PR):** Navigate to your GitHub website repository, click "Compare & pull request", link it to `main`, and verify the visual diff charts look correct.

---

###  Phase 5: Production Merge & Cleanup
Once the PR is approved, finalize your local tracking workspace.
- [ ] **Merge the PR on GitHub:** Click "Squash and Merge" to keep a clean, single-line linear history.
- [ ] **Return Local Environment to Main Track:**
      ```bash
      git checkout main
      git pull origin main
      ```
- [ ] **Prune Spent Local Branch:** Clean up your system's hard drive space by deleting the old temporary feature track.
      ```bash
      git branch -d feat/add-retrain-automation
      ```
