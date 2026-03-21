# HLTHCR — Claude Code Operating Rules

## 1. Shared Folder

All generated documents (docx, pdf, etc.) should be saved to:

```
/home/femi/projects/shared/HLTHCR/
```

This folder is symlinked from `/home/femi/projects/ai-studio/shared/` and accessible cross-repo.

## 2. Context Window Management

200k token context window. Proactive warnings at:
- **20% remaining** — flag to user, suggest summarising completed work
- **40% remaining** — recommend closing non-essential context
- **60% remaining** — normal awareness
- **80% remaining** — no action needed

## 3. Conventions

- Never delete files — archive instead
- Never modify `> [!human]` blocks
- Commit changes only when explicitly asked
- All CC-created files should include `generated_by: cc` in frontmatter where applicable
- Files may exceed 2,000 words if warranted

## 4. Project Structure

<!-- Fill in as project takes shape -->

## 5. Task Modes

<!-- Define task modes specific to hlthcr -->
