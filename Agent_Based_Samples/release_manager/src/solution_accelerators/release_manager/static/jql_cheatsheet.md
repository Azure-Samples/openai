**JIRA Query Language (JQL) Cheat Sheet**

## Query Structure
A JQL query consists of:
- **Field**: The attribute of an issue (e.g., `assignee`, `priority`, `status`).
- **Operator**: Defines the relationship between the field and value (e.g., `=`, `>`, `in`).
- **Value/Function**: Specifies the criteria (e.g., `"Open"`, `currentUser()`).

**Example Query:**
```
project = "TEST" AND status = "Open"
```

## Operators
#### Equality Operators
- `=` (equals)
- `!=` (not equal)

#### Comparison Operators
- `>` (greater than)
- `>=` (greater than or equal to)
- `<` (less than)
- `<=` (less than or equal to)

#### Text Search Operators
- `~` (contains, used for text fields)
- `!~` (does not contain)

#### List Operators
- `in` (matches any value in a list)
- `not in` (does not match any value in a list)

#### History Operators
- `was` (was previously in a state)
- `was not` (was never in a state)
- `was in` (was previously in any of these states)
- `was not in` (was never in any of these states)

#### Change Operators
- `changed` (used to track changes in fields)

## Wildcard and Fuzzy Search
- **Single Character Wildcard:** `?`
  - Example: `te?t` (matches `text`, `test`, etc.)
- **Multiple Character Wildcard:** `*`
  - Example: `win*` (matches `windows`, `winner`, etc.)
- **Fuzzy Search:** Add `~` to the end of a term
  - Example: `roam~` (matches similar words like `room`, `roams`)
- **Proximity Search:** Add `~` and a number to a quoted phrase
  - Example: `"Atlassian Jira"~10` (words within 10 words of each other)

### Boosting Search Relevance
Use `^` with a boost factor to prioritize terms.
- Example: `atlassian^4 jira` (boosts `atlassian` relevance)

### Reserved Characters and Words
#### Reserved Characters
`& | * / % ^ $ # @ [ ] , ; ? !`

#### Reserved Words
`and`, `or`, `not`

**Escape Methods:**
- Surround with quotes: `text ~ "encoding"`
- Escape with backslashes: `text ~ "\\specialTerm"`

## Common Fields
- `assignee`
- `priority`
- `status`
- `summary`
- `labels`
- `project`
- `fixVersion`
- `created`

## Functions for Dynamic Queries
#### Date Functions
- `startOfDay()`, `startOfWeek()`, `startOfMonth()`
- `endOfDay()`, `endOfWeek()`, `endOfMonth()`

#### User Functions
- `currentUser()`
- `membersOf("groupName")`

#### Sprint and Issue History Functions
- `openSprints()`
- `issueHistory()`

#### Approval and Watcher Functions
- `myApproval()`, `myPending()`
- `watchedIssues()`

## Example Queries
#### 1. Find issues assigned to the current user, created this week, and either `Open` or `Reopened` with high priority:
```
created > startOfWeek() AND assignee = currentUser() AND (status = Open OR (status = Reopened AND priority IN (High, Highest)))
```

#### 2. Search for text fields containing `"lost luggage"` (fuzzy) and `"mars shuttle"` (within 5 words of each other), with a project filter:
```
text ~ "lost grn~ luggage" AND text ~ '"mars shuttle"~5' AND project IN ("Teams in Space")
```

#### 3. Find issues from a specific project where the field contains `"Test"`:
```
project = "Test"
```

## Default Work Types in Jira

### Business Project Work Types

- **Task** - Represents work that needs to be done.
- **Subtask** - A smaller piece of work required to complete a task.

### Software Project Work Types

- **Epic** - A large user story grouping related bugs, stories, and tasks.
- **Bug** - A problem that impairs or prevents product functionality.
- **Story** - The smallest unit of work needed to be done.
- **Task** - Represents work that needs to be done.
- **Subtask** - A breakdown of a standard work item (bug, story, or task).

### Jira Service Management Work Types

- **Change** - Requesting a modification in IT systems.
- **IT Help** - Requesting assistance for an IT issue.
- **Incident** - Reporting an IT service outage.
- **New Feature** - Requesting a new capability or software feature.
- **Problem** - Investigating the root cause of multiple incidents.
- **Service Request** - Seeking assistance from an internal or customer service team.
- **Service Request with Approval** - Request requiring managerial approval.
- **Support** - Assistance for customer support issues.

## Work Item Statuses

A work item's status represents its stage in the workflow. Default statuses come with Jira templates but can be customized.

### Default Statuses

- **Open** - Ready for work.
- **In Progress** - Actively being worked on.
- **Done** - Work is completed.
- **To Do** - Awaiting action.
- **In Review** / **Under Review** - Awaiting peer review.
- **Approved** - Work is approved.
- **Cancelled** / **Rejected** - Work stopped or not accepted.
- **Draft** - In progress, in draft stage.
- **Published** - Released for internal use.

### Jira-Specific Statuses

- **Reopened** - Work item resolved incorrectly.
- **Resolved** - Awaiting verification.
- **Closed** - Work item finished.
- **Building** / **Build Broken** - Code-related statuses.
- **Backlog** - Future sprint task.
- **Selected for Development** - Verified for future work.

### Jira Service Management Statuses

- **Declined**
- **Waiting for Support / Customer**
- **Pending / Canceled / Escalated**
- **Awaiting Approval / Implementation**
- **Work in Progress / Completed**
- **Under Investigation**

## Work Item Priorities

- **Highest** - Blocks progress.
- **High** - Could block progress.
- **Medium** - May affect progress.
- **Low** - Minor impact.
- **Lowest** - Trivial impact.

## Work Item Resolutions

- **Done** - Work completed.
- **Won't Do** - No action taken.
- **Duplicate** - Already exists.

### Jira-Specific Resolutions
- **Cannot Reproduce** - Issue not replicable.

### Jira Service Management Resolutions
- **Known Error** - Documented issue with a workaround.
- **Hardware Failure / Software Failure** - Root cause identified.