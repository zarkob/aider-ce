# BMAD Integration Implementation Plan

## 1. Objective

The primary objective is to integrate the "Breakthrough Method of Agile AI-driven Development" (BMAD) framework into the Aider CLI tool. This will provide Aider users with a structured, workflow-driven approach to software development, combining Aider's powerful code editing capabilities with BMAD's agentic planning and execution methodology.

## 2. High-Level Approach

The integration will be implemented as a new "BMAD mode" within Aider, activated via a `/bmad` command. This mode will guide the user through the two primary phases of the BMAD workflow: Planning and Development. A new `BMADCoder` will be created to manage the state and agent interactions specific to this mode.

The integration will proceed in phases:
1.  **Core Integration:** Set up the basic command structure and BMAD project initialization.
2.  **Planning Workflow:** Implement the functionality for planning agents (Analyst, PM, Architect) to generate project documents.
3.  **Development Workflow:** Implement the core development loop with SM, Dev, and QA agents.
4.  **Tool Integration:** Port supporting BMAD tools like the document sharder and codebase flattener.

## 3. Phase 1: Core Integration & Setup

This phase establishes the foundational components for BMAD mode within Aider.

-   **Create `/bmad` Command:**
    -   Modify `aider.commands.Commands` to add a new `/bmad` command.
    -   This command will switch the current coder to the new `BMADCoder`.

-   **Integrate BMAD Installer Logic:**
    -   Port the logic from `tools/installer/` into an Aider utility.
    -   When `/bmad` is first run in a project, it should prompt the user to initialize it.
    -   Initialization will copy the `bmad-core` directory into the user's project root as `.bmad-core`.
    -   Aider's `.gitignore` logic should be updated to recognize and potentially ignore `.bmad-core`.

-   **Create `BMADCoder`:**
    -   Create a new file `aider/coders/bmad_coder.py`.
    -   This class will inherit from `aider.coders.base_coder.Coder`.
    -   It will manage the state of the BMAD workflow (e.g., current phase, active agent).
    -   It will use custom prompts derived from the BMAD agent definitions (`.bmad-core/agents/*.md`).

## 4. Phase 2: Planning Workflow Integration

This phase implements the document generation capabilities of the BMAD planning agents.

-   **Agent Persona Loading:**
    -   The `BMADCoder` will load the persona and instructions for the selected agent (e.g., `pm`, `architect`) from the corresponding markdown file in `.bmad-core/agents/`.
    -   The user will be able to switch between planning agents using commands like `/bmad agent pm`.

-   **Document Generation with Templates:**
    -   Implement the logic for the `create-doc` task from BMAD (`common/tasks/create-doc.md`).
    -   The active agent will interact with the user to fill out the YAML templates found in `.bmad-core/templates/`.
    -   The final output (e.g., `prd.md`, `architecture.md`) will be saved to the `docs/` directory in the user's project.

-   **Elicitation and Refinement:**
    -   Implement the `advanced-elicitation` task to allow for interactive refinement of generated documents, as described in the BMAD workflow.

## 5. Phase 3: Development Workflow Integration

This phase implements the core SM -> Dev -> QA development loop.

-   **Document Sharding:**
    -   Integrate the `shard-doc` task. After planning documents are created, the user will be prompted to shard them.
    -   This will split `docs/prd.md` and `docs/architecture.md` into smaller, digestible files in `docs/prd/` and `docs/architecture/`.

-   **Scrum Master (SM) Agent:**
    -   When the user is ready to begin development, they will switch to the `sm` agent.
    -   The `sm` agent will execute the `create-next-story` task, reading the sharded documents to generate a detailed story file in `docs/stories/`.

-   **Developer (Dev) Agent:**
    -   The `dev` agent's role is to implement the story.
    -   The `BMADCoder` will pass the content of the approved story file to the LLM.
    -   The Dev agent will then generate code changes. This step should leverage Aider's existing strengths by using one of Aider's standard edit formats (like `editblock` or `udiff`) for the actual code modifications. The `BMADCoder` will delegate the final code application to an appropriate existing coder.

-   **QA Agent:**
    -   The `qa` agent will review the code implemented by the Dev agent.
    -   This will involve adding the changed files to the context and having the QA agent's persona review them against the story's acceptance criteria.
    -   The QA agent can suggest further edits, which would be applied by the Dev agent.

## 6. Phase 4: Supporting Tool Integration

-   **Codebase Flattener:**
    -   Integrate the logic from `tools/flattener/` as a new Aider command, e.g., `/flatten`.
    -   This will allow users to easily prepare their codebase for consumption by external web-based AIs.

-   **Checklists:**
    -   Integrate the `execute-checklist` task.
    -   Agents like the `po` and `architect` will use this to validate the generated artifacts against the checklists in `.bmad-core/checklists/`.

## 7. User Experience (UX)

-   **Guided Workflow:** Aider should actively guide the user through the BMAD process. After one step is complete (e.g., PRD creation), it should suggest the next logical step (e.g., "Your PRD is complete. Shall we now create the architecture with the architect agent?").
-   **Clear State Management:** The user should always be aware of the current phase (Planning/Development), the active agent, and the current task. Aider's status bar could be updated to reflect this.
-   **New Commands:**
    -   `/bmad init`: Initializes BMAD in the current project.
    -   `/bmad agent <agent_name>`: Switches to a specific BMAD agent.
    -   `/bmad task <task_name>`: Executes a specific BMAD task.
    -   `/bmad workflow <workflow_name>`: Starts a guided workflow.
    -   `/bmad status`: Shows the current state of the BMAD process.

## 8. Future Work: Expansion Packs

-   The initial integration will focus on `bmad-core`.
-   A mechanism will be needed to allow users to install and use BMAD expansion packs.
-   This could involve a command like `/bmad install-pack <pack_name>` which would download and set up the pack's files.
-   The `BMADCoder` would need to be able to resolve agent/task dependencies across both `.bmad-core` and any installed expansion pack directories.

