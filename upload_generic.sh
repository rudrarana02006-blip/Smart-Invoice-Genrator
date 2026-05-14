#!/bin/bash
# --- SMART INVOICE GENERIC UPLOAD SCRIPT ---
# This script pushes a generic version of the project to GitHub 
# while keeping your local machine branded as "Devleds".

echo "🚀 Starting Generic Upload Process..."

# 1. Ensure we are in the right directory
cd "$(dirname "$0")"

# 2. Add all local changes to the local repo (branded)
git add .
git commit -m "Local update with branding: $(date)"

# 3. Create a temporary branch for the generic version
git checkout -b temp-generic-branch

# 4. Scrub branding (Genericize)
echo "🧼 Scrubbing branding for GitHub..."
export LC_ALL=C
find . -type f \( -name "*.html" -o -name "*.py" -o -name "*.js" -o -name "*.css" -o -name "*.md" -o -name "*.txt" \) -exec sed -i '' 's/Devleds/Smart Invoice/g' {} +
find . -type f \( -name "*.html" -o -name "*.py" -o -name "*.js" -o -name "*.css" -o -name "*.md" -o -name "*.txt" \) -exec sed -i '' 's/devleds/Smart Invoice/g' {} +
find . -type f \( -name "*.html" -o -name "*.py" -o -name "*.js" -o -name "*.css" -o -name "*.md" -o -name "*.txt" \) -exec sed -i '' 's/DEVLEDS/SMART INVOICE/g' {} +

# 5. Commit the generic changes
git add .
git commit -m "Generic Public Release: $(date)"

# 6. Push to GitHub
echo "📤 Pushing generic version to GitHub..."
git push origin temp-generic-branch:main --force

# 7. Switch back to your branded branch and delete the temp one
git checkout main
git branch -D temp-generic-branch

echo "✅ DONE! Your local files are still 'Devleds', but GitHub is now generic."
echo "⚠️ Note: Uncomment the 'git push' line in this script once you've added your GitHub Remote URL."
