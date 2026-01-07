/**
 * @file diagrams.ts
 * @description Centralized Mermaid diagram definitions. 
 * These match the source of truth in the wiki/diagrams/ folder.
 */

export const DIAGRAMS = {
  ALLOCATOR: `
sequenceDiagram
    participant User
    participant CLI
    participant SQL as SQLite DB
    participant Git
    
    User->>CLI: grit commit -m "..."
    CLI->>SQL: Find first open date (Recursive CTE)
    SQL-->>CLI: 2024-03-24
    CLI->>Git: Injects AUTHOR & COMMITTER DATE
    Git-->>CLI: Exit Code 0
    CLI->>SQL: count++ for 2024-03-24
  `,
  SYNC: `
graph TD
    A[Start: grit sync] --> B{Check Local Log}
    B -->|Parse| C[Local Commit Dates]
    A --> D{Check Public GitHub}
    D -->|Scrape| E[Remote Graph]
    C --> F{Merge Data}
    E --> F
    F -->|MAX Logic| G[(SQLite DB)]
    G --> H[End: Re-Synced]
    
    style F fill:#14b8a6,stroke:#fff,stroke-width:2px,color:#fff
    style G fill:#000,stroke:#14b8a6,stroke-width:2px,color:#fff
  `,
  SCHEMA: `
erDiagram
    CONFIG {
        string key PK
        string value
    }
    COMMITS {
        string date PK
        int count
    }
    CONFIG ||--o{ COMMITS : "defines target"
  `
} as const;
