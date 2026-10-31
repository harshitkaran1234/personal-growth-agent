# Agents plan

The AI agents planned for the Personal Growth Agent, what each one does, and the order they get
built in. Guiding rule: **agents decide, code computes**. Anything that is a calculation or a
fixed rule stays in plain code and is exposed to agents as a tool.

## Agents

| # | Agent | What it does | Tools it needs | When |
|---|---|---|---|---|
| 1 | **Goal planner** | Turns vague goals ("master system design in 3 months") into drafts with milestones, weekly targets and priorities; checks workload; edits plans later | Read profile/goals, save/update/remove draft goal, set priorities, check workload, show plan card | First. Onboarding needs it. |
| 2 | **Check-in agent** | Turns free-text logs ("read 20 pages", "ran 5k yesterday") into entries against the right goal, and asks when unsure. Also runs the evening check-in conversation. | Read goals and today's check-in, add/update entry, save energy/mood/note | Second |
| 3 | **Day planner** | "Help me plan my day": looks at this week's targets, what's done, and fixed times, then suggests what to do today and when | Read goals, this week's progress, fixed times; save today's plan | Third |
| 4 | **Weekly review agent** | Compares planned vs. done (numbers from code), writes the reflection, drafts next week's plan, moves goals to their next milestone | Read the week's check-ins and summary, save reflection, draft next week's plan | Fourth |
| 5 | **Coach** | General questions: "Why do I keep missing Wednesdays?", "Am I on track?" Answers from the user's history, and hands off to another agent when something needs to change. | Read-only access to everything, plus search over notes (RAG) | Fifth, once there's history to answer from |

## Not separate agents

| Piece | What it is instead | Why |
|---|---|---|
| **Router** | A small, fast LLM call that picks which agent handles each message | Needed only once 2+ agents share one chat. Before that, the chat goes straight to the goal planner. |
| **Memory** | A step at the end of the weekly review that saves lasting patterns | Patterns only show up over weeks, and the review already looks at the week |
| **Monthly reflection** | The weekly review agent in "monthly mode" | Same job over a longer period: keep, raise, lower, split or retire each goal |
| **Missed-week recovery** | Code detects the low week, then the goal planner or review agent suggests a lighter plan | Detecting it is a calculation. The agent only handles the conversation. |
| **Reminders / nudges** | Plain code: a scheduler, rules and message templates | Nothing about it needs judgment |
| **Workload check, streaks, pace** | Plain code, exposed to agents as tools | Agents decide, code computes |

## Later (Phase 2)

| Agent | What it does |
|---|---|
| **Room facilitator** | Writes the weekly group recap from progress members chose to share, never from raw notes |

## Build order

```text
Goal planner → Check-in agent → (add router) → Day planner → Weekly review (+ memory step) → Coach
```

5 agents for v1, plus a router. Each one adds a new skill:

- **Goal planner:** tool calling and draft-then-confirm writes
- **Check-in agent:** extracting structured data from free text, and asking when unsure
- **Day planner:** reasoning over time and limits
- **Weekly review:** summarizing, and writing that has to match the data
- **Coach:** RAG and handing off between agents
