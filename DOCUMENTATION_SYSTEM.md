# Documentation Consistency System

This project uses a multi-layered approach to ensure documentation consistency across all Claude Code sessions.

## System Components

### 1. SessionStart Hook (Automatic - Primary)
**File**: `.claude/settings.local.json`
**How it works**: At the start of EVERY Claude Code session, an LLM prompt hook runs that reminds Claude of the documentation rules.

**What it does**:
- Displays documentation file mapping
- Reminds of the workflow (search → read → update)
- Lists files that should NEVER be created
- References the full `.clauderc` for details

**Status**: ✅ Active - No action required

### 2. Full System Prompt (Reference)
**File**: `.clauderc`
**Purpose**: Complete documentation standards, conventions, and rules

**Contains**:
- Detailed file structure and purpose
- Comprehensive workflow rules
- API documentation templates
- Code documentation standards
- Git commit message conventions
- Quick reference tables

**When to use**: Reference for detailed guidelines or when clarifying edge cases

### 3. API Documentation Template
**File**: `docs/API.md`
**Purpose**: Single source of truth for ALL API documentation

**Structure**:
- Overview & authentication
- All endpoints with examples
- Data models
- Error handling
- Rate limiting
- Pagination

## How It Works

### Every Session Start:
1. Claude Code loads `.claude/settings.local.json`
2. SessionStart hook executes automatically
3. Claude receives documentation rules as a prompt
4. Claude acknowledges understanding the rules
5. Session proceeds with rules in context

### When Working on Documentation:
1. Claude checks the rules from SessionStart hook
2. Searches for existing documentation files
3. Uses the correct file according to the mapping
4. Reads existing content before editing
5. Updates in place, never creates duplicates

## File Mapping (Quick Reference)

| What You're Documenting | Use This File | Never Create |
|------------------------|---------------|--------------|
| API endpoints | `docs/API.md` | api-docs.md, endpoints.md, API_REFERENCE.md |
| Architecture | `docs/architecture-mvp.md` | system-design.md, tech-arch.md |
| Implementation tasks | `IMPLEMENTATION_PLAN.md` | PLAN.md, TODO.md, ROADMAP.md |
| UI/Frontend | `docs/UI_IMPLEMENTATION_PLAN.md` | frontend-plan.md, UI-DOCS.md |
| Setup | `docs/LOCAL_SETUP.md` | SETUP.md, INSTALL.md |
| Database | `docs/DATABASE.md` + `setup.sql` | db-schema.md, database-design.md |
| Backend specifics | `backend/README.md` | backend-docs.md |
| Frontend specifics | `frontend/README.md` | frontend-docs.md |

## Verification

To verify the system is working:

1. **Start a new Claude Code session**
2. **Look for**: "Loading project documentation guidelines..." status message
3. **Claude should acknowledge** the documentation rules
4. **Test**: Ask Claude to "add API documentation for a new endpoint"
5. **Expected**: Claude should update `docs/API.md`, not create a new file

## Benefits

✅ **Consistency**: Same files used across all sessions
✅ **No Duplicates**: Prevents scattered documentation
✅ **Automatic**: Works without manual intervention
✅ **Predictable**: Always know where to find docs
✅ **Maintainable**: Easy to update one source of truth

## Troubleshooting

### Claude creates wrong file
```
Remind: "Check the SessionStart hook rules - we should use docs/API.md for API docs"
```

### Hook not running
Check `.claude/settings.local.json` has the `hooks` section

### Need to override
```
"For this specific case, please create [new-file.md] even though it's not in our standard structure"
```

## Customization

### To add a new documentation category:

1. **Update** `.claude/settings.local.json` → SessionStart hook prompt
2. **Update** `.clauderc` → Full documentation structure
3. **Create** the new documentation file
4. **Commit** all changes together

### To modify existing rules:

1. **Edit** `.claude/settings.local.json` → SessionStart hook (concise version)
2. **Edit** `.clauderc` → Detailed version
3. **Test** in a new session

## Files in This System

```
tiktok-scraper/
├── .claude/
│   └── settings.local.json          # SessionStart hook (automatic)
├── .clauderc                         # Full system prompt (reference)
├── DOCUMENTATION_SYSTEM.md          # This file (overview)
├── docs/
│   ├── API.md                       # API documentation (template created)
│   ├── architecture-mvp.md          # Current architecture
│   ├── UI_IMPLEMENTATION_PLAN.md    # Frontend plans
│   ├── LOCAL_SETUP.md               # Setup instructions
│   ├── DATABASE.md                  # Database documentation (create when needed)
│   └── HOW_TO_USE_CLAUDE_SYSTEM_PROMPT.md  # Detailed usage guide
└── IMPLEMENTATION_PLAN.md           # Implementation tasks
```

## For Team Members

### When onboarding:
1. Read this file (DOCUMENTATION_SYSTEM.md)
2. Review `.clauderc` for full details
3. Check `docs/API.md` as example template
4. Start using Claude Code - system works automatically

### When documenting:
1. Trust the system - Claude will use correct files
2. If unsure, check this file's mapping table
3. Never manually create documentation files not in the mapping
4. Update existing files instead

### When modifying the system:
1. Discuss changes with team first
2. Update both SessionStart hook AND .clauderc
3. Test in a new session
4. Commit with clear documentation

## Version History

- **v1.0** (2025-12-27): Initial system setup
  - Created `.clauderc` full system prompt
  - Added SessionStart hook to `.claude/settings.local.json`
  - Created `docs/API.md` template
  - Established documentation file structure

---

**Maintained by**: Development Team
**Last Updated**: 2025-12-27
**Status**: ✅ Active and Operational