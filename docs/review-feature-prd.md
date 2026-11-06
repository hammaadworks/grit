# Product Requirements Document (PRD): Web-Based Diff Viewer for `grit review`

## 1. Objective
To replace the current CLI-based `grit review` output with a rich, interactive, 4-pane web-based diff viewer. This feature will provide developers with a PyCharm-like side-by-side code comparison, real-time AI review streaming, and the ability to leave inline comments.

## 2. Architecture & Data Flow

### 2.1 Backend Server (`review_server.py`)
- **Initialization**: A temporary local HTTP server is spun up when `grit review` is executed.
- **Context Passing**: The server provisions the initial payload (diff data, AI configuration, and context) to the frontend upon load.
- **Streaming (SSE)**: The Python server orchestrates the LLM API calls and streams the generated review chunks to the frontend using Server-Sent Events (SSE).

### 2.2 Browser Close Hook & Finalization
- **Completion Trigger**: The frontend will feature a "Save & Close" mechanism (and listen for `beforeunload`).
- **Data Submission**: On close, the frontend sends a final POST request back to the Python backend containing the user's inline comments.
- **Clipboard**: The backend automatically copies the final comments to the user's clipboard.
- **Persistence**: The review data is saved to `state.db`.

### 2.3 Dashboard Integration
- **Post-Review Navigation**: After saving the review, the CLI will check if the Grit Dashboard is currently running.
- **Routing**: 
  - If the dashboard is running, the user is redirected to `http://localhost:<port>/api/db/data?table=reviews`.
  - If it is not running, the CLI will launch the dashboard and then navigate to the database view for the `reviews` table.

## 3. Database Schema

A new table will be added to `state.db` to maintain a history of recent code reviews.

### 3.1 Table Definition: `reviews`
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `timestamp` (DATETIME): Used to sort by the most recent first.
- `files` (TEXT): A JSON-serialized list of the files included in the diff.
- `ai_summary` (TEXT): The complete text of the AI-generated code review.
- `user_comments` (TEXT): A JSON blob containing the line-by-line comments created by the user during the review session.

### 3.2 FIFO Logic
To manage storage, only the last 10 reviews will be kept. 
- During the `save_review` operation in `StateManager`, after inserting the new record, the system will execute a deletion query to remove any records beyond the 10 most recent entries based on the `timestamp`.

## 4. UI/UX Layout (The 4 Panes)

The web interface (`src/grit/review.html`) will utilize CSS Grid to create a responsive, 4-pane layout.

- **Pane 1 (Top Left): Files List**
  - Displays a vertical list of files present in the current diff.
  - Clicking a file name updates the central diff viewer to show that specific file's changes.

- **Panes 2 & 3 (Center): Monaco Editor Diff**
  - **Component**: Embedded Monaco Editor (loaded via CDN for lightweight implementation without complex build steps).
  - **Features**: Provides a robust, side-by-side (old vs. new) diff view with synchronized scrolling.
  - **Interaction**: Hooks into Monaco's `addZone` or editor action APIs to allow users to click in the gutter to create inline comments mapped to specific lines.

- **Pane 4 (Bottom Right / Sidebar): Comments & AI Stream**
  - **AI Stream**: Displays the real-time, streaming text of the AI's code review as it is generated via SSE.
  - **Comment Log**: Shows an aggregated, chronological list of the comments the user has typed within the Monaco editor panes.