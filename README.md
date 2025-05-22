# Agentic Analytics

## User Stories
User Story 1: As a user I want to connect my github account to user this app. User connects their github account on signin or signup, select repos to connect from the list, label or explain what each repo is, and initiate indexing and scanning. 

User Story 2: As a user, I want to navigate scanned event tracking from my codebases. User can navigate the scanned analytics events (track, identify, and reset) on the sidebar on the left. Each card of analytics event is a collection of information about event name, context where it is tracked in natural language, tags and location (repo, file, line number) On its right side, user can see the piece of code just like vscode. 

User Story 3: As a user, I want to search my codebases and add event code snippets myself User can search their own codebases just like vscode, and add event code snippets just like github PR review. Select line of code by dragging codes on the left, and a modal shows up on the bottom of the selected code enables users to add. 

User Story 4: As a user, I want to see, edit, and export my entire tracking plan. A spreadsheet of tracking plan on user's hand. They can export it in a sheet, and optionally import new feature plan from figma (TBD).

## Development Checklist

### 1. GitHub Authentication & Repo Connection
- [x] Implement GitHub OAuth for sign in/sign up
- [ ] Allow users to select repositories to connect
- [x] Enable users to label or explain each connected repo
- [x] Initiate indexing and scanning of selected repos

### 2. Event Tracking Navigation
- [ ] Scan codebases for analytics events (`track`, `identify`, `reset`)
- [ ] Display scanned events in a sidebar (left navigation)
- [ ] For each event, show:
  - [ ] Event name
  - [ ] Context (in natural language)
  - [ ] Tags
  - [ ] Location (repo, file, line number)
- [ ] Show code snippet for each event (VSCode-like view)

### 3. Manual Event Snippet Addition
- [ ] Implement codebase search (VSCode-like)
- [ ] Allow users to select code lines (drag to select)
- [ ] Show modal for adding event code snippets to selected code
- [ ] Enable users to annotate or label added snippets

### 4. Tracking Plan Management
- [ ] Display all tracked events in a spreadsheet/table view
- [ ] Allow users to edit tracking plan entries
- [ ] Enable export of tracking plan (e.g., CSV, Excel)
- [ ] (Optional) Import feature plan from Figma