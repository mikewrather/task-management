# Feature Detection Utility

## Purpose

This utility provides standardized feature detection logic for BMAD agents and tasks. It extracts feature names from git branches to determine documentation folder structure.

## Feature Detection Algorithm

### Bash Implementation

```bash
#!/bin/bash
# Feature detection utility for BMAD

get_current_feature() {
    local branch=$(git branch --show-current 2>/dev/null)

    # Handle feature/{name} pattern
    if [[ $branch =~ ^feature/(.+)$ ]]; then
        echo "${BASH_REMATCH[1]}"
        return 0
    fi

    # Handle features/{main}/{sub} pattern
    if [[ $branch =~ ^features/(.+)$ ]]; then
        # Convert nested path to folder-safe format
        echo "${BASH_REMATCH[1]}" | tr '/' '-'
        return 0
    fi

    # No feature branch detected
    echo ""
    return 1
}

validate_feature_name() {
    local feature="$1"

    # Check if feature name is kebab-case
    if [[ ! $feature =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
        echo "ERROR: Feature name '$feature' must be kebab-case (lowercase-with-hyphens)"
        return 1
    fi

    return 0
}

create_feature_branch() {
    local feature_name="$1"

    if ! validate_feature_name "$feature_name"; then
        return 1
    fi

    git checkout -b "feature/$feature_name"
    echo "Created feature branch: feature/$feature_name"
}

# Main function for agents to use
detect_feature_or_prompt() {
    local feature=$(get_current_feature)

    if [ -z "$feature" ]; then
        echo "Not on a feature branch. Create one with:"
        echo "  git checkout -b feature/{feature-name}"
        echo ""
        echo "Feature names should be kebab-case, e.g.:"
        echo "  - user-authentication"
        echo "  - payment-processing"
        echo "  - admin-dashboard"
        return 1
    fi

    if ! validate_feature_name "$feature"; then
        return 1
    fi

    echo "$feature"
    return 0
}
```

### Usage Examples

#### In Agent Prompts

````markdown
## Feature Detection

Before proceeding, detect the current feature:

1. Run the feature detection:
   ```bash
   FEATURE=$(get_current_feature)
   if [ -z "$FEATURE" ]; then
       echo "You must be on a feature branch. Create one with: git checkout -b feature/{name}"
       exit 1
   fi
   ```
````

2. Use feature for paths:
   ```bash
   PRD_PATH="docs/$FEATURE/prd.md"
   STORY_PATH="docs/$FEATURE/stories/"
   ```

````

#### In Tasks
```markdown
### Step 1: Feature Detection
- Run `git branch --show-current`
- Extract feature name using pattern matching
- Validate feature name format (kebab-case)
- Construct feature-aware paths
````

## Git Branch Patterns

### Supported Patterns

```bash
feature/user-auth           → Feature: "user-auth"
feature/payment-gateway     → Feature: "payment-gateway"
features/ecommerce/cart     → Feature: "ecommerce-cart"
features/analytics/reports  → Feature: "analytics-reports"
```

### Naming Rules

1. **Kebab-case**: All lowercase with hyphens (no underscores, spaces, or camelCase)
2. **Descriptive**: Use clear, descriptive names that indicate the feature purpose
3. **Hierarchical**: Use `features/` prefix for nested features
4. **Consistent**: Maintain naming consistency across related features

### Valid Examples

```
✅ feature/user-authentication
✅ feature/payment-processing
✅ feature/admin-dashboard
✅ features/ecommerce/checkout-flow
✅ features/reporting/sales-analytics
```

### Invalid Examples

```
❌ feature/UserAuth          (camelCase)
❌ feature/user_auth         (underscores)
❌ feature/user auth         (spaces)
❌ feature/123-feature       (starts with number)
❌ feature/feature-          (ends with hyphen)
```

## Path Resolution

### Dynamic Path Construction

```bash
# Base paths with feature support
get_doc_path() {
    local doc_type="$1"
    local feature=$(get_current_feature)

    if [ -n "$feature" ]; then
        echo "docs/$feature/$doc_type.md"
    else
        echo "docs/$doc_type.md"  # Backwards compatibility
    fi
}

get_shard_path() {
    local doc_type="$1"
    local feature=$(get_current_feature)

    if [ -n "$feature" ]; then
        echo "docs/$feature/$doc_type/"
    else
        echo "docs/$doc_type/"  # Backwards compatibility
    fi
}
```

### Examples

```bash
PRD_PATH=$(get_doc_path "prd")              # docs/{feature}/prd.md
ARCH_PATH=$(get_doc_path "architecture")    # docs/{feature}/architecture.md
STORY_PATH=$(get_shard_path "stories")      # docs/{feature}/stories/
```

## Integration Points

### For BMAD Agents

1. **Planning Agents** (PM, Architect, UX): Detect feature at start of document creation
2. **Development Agents** (SM, Dev): Detect feature when loading stories and documentation
3. **Quality Agents** (QA, PO): Use feature paths for assessments and gates

### For BMAD Tasks

1. **shard-doc**: Use feature-aware source and destination paths
2. **create-next-story**: Create stories in feature-specific directories
3. **index-docs**: Scan feature folders for documentation indexing

### For BMAD Workflows

1. **Greenfield**: Ensure feature branch exists before planning starts
2. **Brownfield**: Detect feature for enhancement organization
3. **Handoff Prompts**: Use feature-specific paths in all transitions

## Error Handling

### Common Scenarios

1. **No Feature Branch**: Provide clear instructions to create one
2. **Invalid Feature Name**: Suggest corrections for naming convention
3. **Missing Feature Directory**: Auto-create when needed
4. **Git Not Available**: Graceful fallback to manual feature specification

### Error Messages

```bash
# Not on feature branch
"You must be on a feature branch to use BMAD. Create one with: git checkout -b feature/{name}"

# Invalid feature name
"Feature name '{name}' must be kebab-case. Example: user-authentication"

# Git not available
"Could not detect git branch. Please specify feature manually in core-config.yaml"
```

## Backwards Compatibility

### Legacy Project Support

- If `featureMode: false` in core-config.yaml, use traditional paths
- If no feature branch detected, fall back to `docs/` root
- Existing projects can opt-in gradually to feature folders

### Migration Path

1. Enable `featureMode: true` in core-config.yaml
2. Create feature branch: `git checkout -b feature/main-feature`
3. Move existing docs to feature folder: `mkdir -p docs/main-feature && mv docs/*.md docs/main-feature/`
4. Update any hardcoded paths in custom scripts

## Testing

### Validation Tests

```bash
# Test feature detection
git checkout -b feature/test-feature
FEATURE=$(get_current_feature)
assert_equals "$FEATURE" "test-feature"

# Test nested features
git checkout -b features/ecommerce/payments
FEATURE=$(get_current_feature)
assert_equals "$FEATURE" "ecommerce-payments"

# Test non-feature branch
git checkout main
FEATURE=$(get_current_feature)
assert_equals "$?" "1"  # Should fail
```

### Path Resolution Tests

```bash
# Test path construction
FEATURE="user-auth"
PRD_PATH=$(get_doc_path "prd")
assert_equals "$PRD_PATH" "docs/user-auth/prd.md"

STORY_PATH=$(get_shard_path "stories")
assert_equals "$STORY_PATH" "docs/user-auth/stories/"
```
