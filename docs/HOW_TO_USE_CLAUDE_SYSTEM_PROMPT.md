# How to Use the Claude Code System Prompt

This guide explains how to use the `.clauderc` system prompt to ensure Claude Code maintains documentation consistency across all sessions.

## What is the .clauderc File?

The `.clauderc` file is a system prompt that instructs Claude Code on how to handle documentation in this project. It ensures:
- The same documentation files are used across all sessions
- No duplicate documentation is created
- Consistent structure and organization
- Predictable file locations for all documentation types

## Automatic Usage (Recommended)

### VSCode Extension
If you're using the Claude Code VSCode extension, it automatically reads `.clauderc` from your project root at the start of each session.

**No action required** - Claude Code will automatically follow the guidelines.

### CLI Usage
If using Claude Code via CLI, you can configure it to read the system prompt:

```bash
# Option 1: Use as a custom instruction file
claude-code --instructions .clauderc

# Option 2: Add to your Claude Code config
# Edit ~/.config/claude-code/config.json
{
  "customInstructions": "/path/to/your/project/.clauderc"
}
```

## Manual Reference (If Needed)

If Claude Code doesn't automatically load the system prompt, you can manually reference it:

1. **At the start of a session**:
   ```
   Please read and follow the system prompt in .clauderc before we begin.
   ```

2. **When working on documentation**:
   ```
   Before creating any documentation, please check the .clauderc file for the correct file to use.
   ```

3. **If Claude creates the wrong file**:
   ```
   Please check .clauderc - we should be using docs/API.md for API documentation, not creating a new file.
   ```

## Quick Reference: Where Does Documentation Go?

According to `.clauderc`, here's where different documentation belongs:

| What You're Documenting | File to Use | Location |
|------------------------|-------------|----------|
| API endpoints, request/response formats | `API.md` | `docs/` |
| System architecture, design | `architecture-mvp.md` | `docs/` |
| Implementation tasks, roadmap | `IMPLEMENTATION_PLAN.md` | root |
| UI components, frontend plans | `UI_IMPLEMENTATION_PLAN.md` | `docs/` |
| Setup instructions | `LOCAL_SETUP.md` | `docs/` |
| Backend-specific info | `README.md` | `backend/` |
| Frontend-specific info | `README.md` | `frontend/` |
| Database schema | `setup.sql` | `backend/` |
| Database documentation | `DATABASE.md` | `docs/` |

## Verification Checklist

Before starting documentation work, verify:

1. **Search existing files**:
   ```
   Does documentation for this topic already exist?
   ```

2. **Check .clauderc**:
   ```
   Which file should I use according to .clauderc?
   ```

3. **Read before writing**:
   ```
   Have I read the entire existing file before making changes?
   ```

4. **Confirm with Claude**:
   ```
   Claude, which file should we update for [topic]?
   ```

## Examples

### Good: Following the System Prompt

**User**: "Add documentation for the new /users endpoint"

**Claude**:
```
I'll add the /users endpoint documentation to docs/API.md,
which is our dedicated file for all API documentation.

[Claude reads docs/API.md first, then adds the new endpoint
following the existing structure]
```

### Bad: Ignoring the System Prompt

**User**: "Add documentation for the new /users endpoint"

**Wrong Response**:
```
I'll create a new file docs/endpoints.md for the API endpoints.

[Creates duplicate documentation]
```

**Correct Action**:
```
Wait, according to .clauderc, I should use docs/API.md for API documentation.
Let me check if it exists and add the endpoint there.
```

## Customizing the System Prompt

If you want to modify the documentation structure:

1. Edit `.clauderc` to update the file mappings
2. Move existing documentation to match the new structure
3. Inform Claude of the changes:
   ```
   I've updated .clauderc. Please review the new structure before we continue.
   ```

## Troubleshooting

### Claude isn't following .clauderc
- Explicitly reference it: "Please read and follow .clauderc"
- Check if the file exists in your project root
- Verify the file path is correct

### Claude creates duplicate documentation
- Remind Claude: "Check .clauderc for the correct file to use"
- Delete the duplicate file
- Ask Claude to move content to the correct file

### Need to override .clauderc
If you genuinely need different documentation structure:
```
For this task, please create a new file [filename] even though
.clauderc suggests [other file]. I want to reorganize the documentation.
```

## Benefits of Using This System

1. **Consistency**: Same files used across all sessions
2. **No Duplicates**: Prevents scattered documentation
3. **Predictability**: Always know where to find documentation
4. **Maintenance**: Easier to keep documentation up-to-date
5. **Collaboration**: Team members know where to look

## Integration with Git

The system prompt includes commit message guidelines:

```bash
# Good commit message for documentation
docs(api): add POST /users endpoint documentation

- Add request/response examples
- Document authentication requirements
- Update error codes section

# Good commit message for setup docs
docs(setup): add Redis installation instructions

# Good commit message for architecture
docs(architecture): update data flow diagram
```

## For Team Members

If you're working with Claude Code on this project:

1. **Never delete .clauderc** - it's critical for consistency
2. **Reference it in PRs** if changing documentation structure
3. **Update it** if you add new documentation categories
4. **Commit changes** to .clauderc when you update it

## Support

If you encounter issues with the system prompt or documentation structure:

1. Check this guide first
2. Review `.clauderc` for the current structure
3. Consult with the team about documentation organization
4. Update `.clauderc` if needed (with team approval)

---

**Version**: 1.0
**Last Updated**: 2025-12-27
**File**: `.clauderc` in project root