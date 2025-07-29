# ublue-rebase-tool - Task 5

Execute task 5 for the ublue-rebase-tool specification.

## Task Description
Extend UBlueImageAPI with execution methods

## Code Reuse
**Leverage existing code**: src/ublue-image-manager.py:UBlueImageAPI class structure

## Requirements Reference
**Requirements**: 3.2, 8.4

## Usage
```
/ublue-rebase-tool-task-5
```

## Instructions
This command executes a specific task from the ublue-rebase-tool specification.

**Automatic Execution**: This command will automatically execute:
```
/spec-execute 5 ublue-rebase-tool
```

**Context Loading**:
Before executing the task, you MUST load all relevant context:
1. **Specification Documents**:
   - Load `.claude/specs/ublue-rebase-tool/requirements.md` for feature requirements
   - Load `.claude/specs/ublue-rebase-tool/design.md` for technical design
   - Load `.claude/specs/ublue-rebase-tool/tasks.md` for the complete task list
2. **Steering Documents** (if available):
   - Load `.claude/steering/product.md` for product vision context
   - Load `.claude/steering/tech.md` for technical standards
   - Load `.claude/steering/structure.md` for project conventions

**Process**:
1. Load all context documents listed above
2. Execute task 5: "Extend UBlueImageAPI with execution methods"
3. **Prioritize code reuse**: Use existing components and utilities identified above
4. Follow all implementation guidelines from the main /spec-execute command
5. **Follow steering documents**: Adhere to patterns in tech.md and conventions in structure.md
6. **CRITICAL**: Mark the task as complete in tasks.md by changing [ ] to [x]
7. Confirm task completion to user
8. Stop and wait for user review

**Important Rules**:
- Execute ONLY this specific task
- **Leverage existing code** whenever possible to avoid rebuilding functionality
- **Follow project conventions** from steering documents
- Mark task as complete by changing [ ] to [x] in tasks.md
- Stop after completion and wait for user approval
- Do not automatically proceed to the next task
- Validate implementation against referenced requirements

## Task Completion Protocol
When completing this task:
1. **Update tasks.md**: Change task 5 status from `- [ ]` to `- [x]`
2. **Confirm to user**: State clearly "Task 5 has been marked as complete"
3. **Stop execution**: Do not proceed to next task automatically
4. **Wait for instruction**: Let user decide next steps

## Next Steps
After task completion, you can:
- Review the implementation
- Run tests if applicable
- Execute the next task using /ublue-rebase-tool-task-[next-id]
- Check overall progress with /spec-status ublue-rebase-tool
