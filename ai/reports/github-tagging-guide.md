# Complete Guide to Git Tagging and GitHub Releases

## The TXO Workflow (Recommended)

**TL;DR**: Tag the merge commit on main AFTER the PR is merged.

### Quick Reference
1. Develop on feature branch
2. Create PR, get approval
3. Merge PR to main (via GitHub)
4. Pull main locally
5. **Verify HEAD** with `git log -1`
6. **Tag HEAD** with `git tag -a v3.3.0`
7. Push tag to GitHub
8. Create GitHub Release (select existing tag)

**What gets tagged**: The merge commit on main created when GitHub merged your PR.

**Why this way**: Tags mark stable code on long-lived branches. Feature branches are temporary and unstable (may be rebased/force-pushed during review).

**Alternative approach exists**: Some teams tag feature branch before merge ("build-once-deploy-everywhere"), but we don't recommend this for TXO because it adds complexity and can point to commits that get rebased during PR review.

---

## Understanding Git Tags vs GitHub Releases

### Git Tags
- **Local tags**: Created in your repository (PyCharm, command line)
- **Remote tags**: Pushed to GitHub
- **Purpose**: Mark specific commits as important points in history

### GitHub Releases
- **Built on top of tags**: Each release is associated with a tag
- **Additional features**: Release notes, binary attachments, download statistics
- **Purpose**: Public distribution points for your software

**Important**: Tags created in PyCharm are LOCAL until explicitly pushed to GitHub!

## Tagging Best Practices

### Version Naming Convention (Semantic Versioning)

```
vMAJOR.MINOR.PATCH

v2.0.0
│ │ │
│ │ └── Patch: Bug fixes (backwards compatible)
│ └──── Minor: New features (backwards compatible)
└────── Major: Breaking changes

Examples:
v1.0.0 - Initial release
v1.0.1 - Bug fix
v1.1.0 - New feature
v2.0.0 - Breaking changes
```

### Tag Types

#### Release Tags (Public)
```bash
v1.0.0      # Stable release
v2.0.0      # Major release
v2.1.0      # Feature release
```

#### Pre-release Tags
```bash
v2.0.0-rc1   # Release candidate
v2.0.0-beta  # Beta version
v2.0.0-alpha # Alpha version
```

#### Internal Tags (Development)
```bash
dev-2025-01-15        # Development checkpoint
feature-complete-api  # Feature milestone
before-refactor       # Backup point
tested-production     # QA approved
```

## Creating Tags in PyCharm

### Method 1: Via Git Log (Recommended)

1. **Open Git Log**
   - View → Tool Windows → Git (Alt+9)
   - Or click Git tab at bottom

2. **Select the commit to tag**
   - Navigate to the specific commit in the log
   - Right-click on the commit

3. **Create the tag**
   - Select "New Tag..."
   - Enter tag name: `v2.0.0`
   - Enter message: `Version 2.0.0 - Enhanced with rate limiting`
   - Click "Create Tag"

### Method 2: Via VCS Menu

1. **Open tag dialog**
   - VCS → Git → New Tag...
   - Or Git → New Tag... (newer PyCharm)

2. **Configure tag**
   - Tag name: `v2.0.0`
   - Message: Your release description
   - Commit: Leave blank to tag HEAD (current commit), or select specific commit from list

### Method 3: Via Branch Widget

1. **Click branch name** (bottom-right corner)
2. **Click "+ New Tag"**
3. **Enter tag details**

### ⚠️ Critical Step: Push Tags to GitHub

**Tags created in PyCharm are LOCAL only! You must push them:**

#### Option 1: Push with commits
1. Press **Ctrl+Shift+K** (Push)
2. In push dialog, check ✅ **"Push Tags"**
3. Select:
   - "All" - pushes all local tags
   - "Current branch" - pushes tags on current branch
4. Click **Push**

#### Option 2: Push tags separately
1. VCS → Git → Push Tags...
2. Select tags to push
3. Click **Push Tags**

#### Option 3: Via Terminal in PyCharm
```bash
# Push specific tag
git push origin v2.0.0

# Push all tags
git push origin --tags
```

### Verifying Tags Are on GitHub

After pushing, verify tags appear on GitHub:

1. **In PyCharm**:
   - Git log should show tag with remote indicator
   - VCS → Git → Branches → Remote tags

2. **On GitHub**:
   - Go to your repository
   - Click the branch dropdown
   - Click "Tags" tab
   - Your tags should be listed

3. **Via command line**:
   ```bash
   # List local tags
   git tag -l
   
   # List remote tags
   git ls-remote --tags origin
   ```

## Creating GitHub Releases

### Step 1: Ensure Tag is on GitHub

**Before creating a release, verify your tag is pushed!**

```bash
# Check if tag exists on GitHub
git ls-remote --tags origin | grep v2.0.0
```

### Step 2: Create Release on GitHub

1. **Navigate to Releases**
   - Go to your repository on GitHub
   - Click "Releases" (right side)
   - Click "Draft a new release"

2. **Configure Release**
   - **Choose a tag**: Select from dropdown (only shows pushed tags!)
   - **Release title**: "v2.0.0 - Enhanced API Resilience"
   - **Description**: Add comprehensive release notes
   - **Pre-release**: Check if beta/RC
   - **Latest release**: Check for stable releases

3. **Generate Release Notes**
   - Click "Generate release notes" button
   - Review auto-generated content
   - Edit and enhance as needed

4. **Save or Publish**
   - **Save draft**: Review later
   - **Publish release**: Make public immediately

### Understanding GitHub's Two Tag Options

When creating a release, GitHub shows:
- **"Choose a tag" dropdown** with existing tags
- **Option to "Create new tag"** by typing new name

#### Option 1: Select Existing Tag (TXO Recommended)
**Use when**: You already created and pushed tag locally (TXO workflow above)

**Steps**:
1. Click "Choose a tag" dropdown
2. Select your existing tag (e.g., "v3.3.0")
3. Add release notes
4. Publish

**What gets tagged**: Your existing local tag (you control exact commit)

**Why recommended**: Explicit control, follows verification workflow, tag points to exact commit you verified

#### Option 2: Create New Tag in GitHub UI
**Use when**: Quick hotfix, simple release, no local git access

**Steps**:
1. Type new tag name in "Choose a tag" field (e.g., "v3.3.0")
2. GitHub shows "Create new tag: v3.3.0 on publish"
3. Add release notes
4. Publish

**What gets tagged**: Current HEAD of target branch (main) - GitHub decides

**Limitation**: You can't control which commit gets tagged - GitHub picks whatever is currently HEAD on the target branch

**TXO Recommendation**: Always use Option 1. It gives you explicit control and allows verification before tagging.

### Step 3: Release Notes Template

```markdown
## 🎉 Highlights
Brief overview of major changes

## ✨ Features
- New feature 1
- New feature 2

## 🐛 Bug Fixes
- Fixed issue 1
- Fixed issue 2

## 💔 Breaking Changes
- List any breaking changes

## 📦 Installation
```bash
pip install package==2.0.0
```

## 📚 Documentation
- [Migration Guide](link)
- [API Docs](link)

## 🙏 Contributors
- @username1
- @username2

**Full Changelog**: [v1.0.0...v2.0.0](link)
```

## Troubleshooting

### Tags Not Showing in GitHub Release Dropdown

**Problem**: Created tag in PyCharm but can't select it when creating release

**Solution**: Tag wasn't pushed to GitHub

```bash
# Check if tag exists locally
git tag -l v2.0.0

# Check if tag exists on GitHub
git ls-remote --tags origin | grep v2.0.0

# If local but not remote, push it
git push origin v2.0.0
```

### PyCharm Not Showing Remote Tags

**Solution**: Fetch from remote

1. VCS → Git → Fetch
2. Or in Terminal: `git fetch --tags`

### Deleted Tag Locally but Still on GitHub

```bash
# Delete local tag
git tag -d v2.0.0

# Delete remote tag
git push origin --delete v2.0.0
```

### Wrong Commit Tagged

```bash
# Delete old tag
git tag -d v2.0.0
git push origin --delete v2.0.0

# Create new tag on correct commit
git tag -a v2.0.0 <commit-hash> -m "Message"
git push origin v2.0.0
```

## Internal vs Public Versioning Strategy

### Recommended Approach

#### Internal Tags (Development Team)
Use descriptive tags for development milestones:
```bash
# Internal development tags
dev-2025-01-15-api-complete
test-ready-2025-01-16
qa-approved-2025-01-17
staging-deployed-2025-01-18
```

#### Public Releases (GitHub Releases)
Use semantic versioning for public releases:
```bash
# Public release tags
v1.0.0
v2.0.0
v2.1.0
```

### Implementation Strategy

1. **During Development**:
   ```bash
   # Create internal tag
   git tag -a dev-api-complete -m "API implementation complete"
   git push origin dev-api-complete
   ```

2. **For QA/Testing**:
   ```bash
   # Create test tag
   git tag -a test-v2.0.0-rc1 -m "Release candidate for testing"
   git push origin test-v2.0.0-rc1
   ```

3. **For Production Release**:
   ```bash
   # Create official version tag
   git tag -a v2.0.0 -m "Version 2.0.0 - Production release"
   git push origin v2.0.0
   # Then create GitHub Release
   ```

### Benefits of This Approach

- **Internal tags**: Track development progress
- **Public releases**: Clean version history for users
- **Flexibility**: Can have many internal tags between releases
- **Clarity**: Users only see stable releases

## Complete Workflow Example

### Scenario: Releasing v3.3.0 (TXO Way)

```bash
# 1. Develop on feature branch
git checkout -b feature/v3.3-enhancements
# ... make changes, commit, push ...
git push origin feature/v3.3-enhancements

# 2. Create Pull Request on GitHub
# - Create PR from feature/v3.3-enhancements → main
# - Get code review approval
# - Ensure all CI tests pass
# - DO NOT TAG YET!

# 3. Merge PR via GitHub UI
# - Click "Merge pull request" button
# - Confirm merge
# - GitHub creates a merge commit on main
# - (Optional) Delete feature branch

# 4. Pull the merged main to local
git checkout main
git pull origin main

# 5. VERIFY you're on the merge commit (CRITICAL!)
git log -1 --oneline
# Expected output: abc1234 Merge pull request #42 from feature/v3.3-enhancements
# This is the commit that will be tagged!

# 6. Tag HEAD (the merge commit)
git tag -a v3.3.0 -m "Version 3.3.0 - Enhanced API resilience"
# Note: No <commit-hash> means tag current HEAD

# 7. Push tag to GitHub
git push origin v3.3.0
# IMPORTANT: Tag must be on GitHub before creating Release

# 8. Verify tag is on GitHub
git ls-remote --tags origin | grep v3.3.0
# Should show: refs/tags/v3.3.0

# 9. Create GitHub Release
# - Go to GitHub repository → Releases
# - Click "Draft a new release"
# - "Choose a tag" → Select "v3.3.0" from dropdown (NOT "Create new tag")
# - Add release title and notes
# - Publish release
```

## Quick Reference

### Essential Commands

```bash
# Create annotated tag on current HEAD (what you're on right now)
git tag -a v2.0.0 -m "Version 2.0.0"

# Create tag on specific commit (override HEAD)
git tag -a v2.0.0 abc1234 -m "Version 2.0.0"

# Push specific tag
git push origin v2.0.0

# Push all tags
git push --tags

# List local tags
git tag -l

# List remote tags
git ls-remote --tags origin

# Delete local tag
git tag -d v2.0.0

# Delete remote tag
git push origin --delete v2.0.0

# Checkout specific tag
git checkout v2.0.0

# See tag details
git show v2.0.0
```

### PyCharm Shortcuts

- **Alt+9**: Open Git window
- **Ctrl+Shift+K**: Push (remember to check "Push Tags")
- **Ctrl+K**: Commit
- **Ctrl+T**: Update project (fetch)

## Best Practices Summary

1. **Always use annotated tags** for releases (`-a` flag)
2. **Push tags explicitly** after creating in PyCharm
3. **Verify tags on GitHub** before creating releases
4. **Use semantic versioning** for public releases
5. **Keep internal tags** separate from version tags
6. **Write comprehensive release notes**
7. **Test locally** before tagging
8. **Verify HEAD before tagging** - Use `git log -1` to confirm you're on the right commit
9. **Tag AFTER merging to main** - Not before or during PR review (feature branches unstable)
10. **Don't reuse tag names** (delete first if needed)
11. **Document breaking changes** clearly

## Additional Resources

- [Semantic Versioning Specification](https://semver.org/)
- [GitHub Releases Documentation](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [Git Tagging Best Practices](https://git-scm.com/book/en/v2/Git-Basics-Tagging)
- [PyCharm Git Integration](https://www.jetbrains.com/help/pycharm/using-git-integration.html)