@echo off
setlocal ENABLEDELAYEDEXPANSION

REM ===== SETTINGS YOU CAN EDIT =====
set BRANCH=main
REM =================================

echo.
echo === Update & Deploy: protein-site ===
cd /d %~dp0

echo.
echo [1/8] Checking Git installation...
where git >nul 2>&1
if errorlevel 1 (
  echo ❌ Git is not installed or not in PATH.
  echo    Install Git: https://git-scm.com/download/win
  pause
  exit /b 1
)

echo.
echo [2/8] Verifying this is a Git repository...
git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
  echo ❌ This folder is not a Git repository: %cd%
  echo    Run "git init" and connect to GitHub, or open the correct repo folder.
  pause
  exit /b 1
)

echo.
echo Current repo: %cd%
for /f "delims=" %%B in ('git branch --show-current 2^>nul') do set CURBR=%%B
echo Current branch: "%CURBR%"
echo Remotes:
git remote -v

echo.
echo [3/8] Building static pages...
python build_site.py
if errorlevel 1 (
  echo ❌ Build failed. Fix errors above and try again.
  pause
  exit /b 1
)

echo.
echo [4/8] Verifying generated files exist...
set MISSING=0
for %%F in (index.html 3d_plot.html 2d_plot1.html 2d_plot2.html 2d_plot3.html data_table.html) do (
  if not exist "%%F" (
    echo ❌ Missing: %%F
    set MISSING=1
  )
)
if %MISSING%==1 (
  echo One or more generated files are missing. Ensure build_site.py writes them to the repo root.
  pause
  exit /b 1
)

echo.
echo [5/8] Showing status BEFORE staging:
git status -s

echo.
echo [6/8] Staging changes (git add -A)...
git add -A

echo.
echo Files staged (cached diff):
git diff --cached --name-status
echo.

REM Check if anything is staged; exit code 0 = no diff; 1 = diff present
git diff --cached --quiet
if %ERRORLEVEL% EQU 0 (
  echo ℹ️  No changes detected to commit.
  echo     Common reasons:
  echo       - build_site.py wrote files to a different folder than this repo
  echo       - .gitignore is excluding *.html (open .gitignore and make sure it does NOT ignore *.html)
  echo       - You rebuilt but the content is identical (no file changes)
  echo.
  echo Tip: Run "git status" manually to double-check tracked files.
  git status
  pause
  exit /b 0
)

echo.
echo [7/8] Committing...
git commit -m "Rebuild site: %DATE% %TIME%"
if errorlevel 1 (
  echo ❌ Commit failed. Check output above.
  pause
  exit /b 1
)

echo.
echo [8/8] Pushing to origin %BRANCH% ...
git push origin %BRANCH%
if errorlevel 1 (
  echo ❌ Push failed. Possible issues:
  echo    - Wrong branch name (current: "%CURBR%", configured to push: "%BRANCH%")
  echo    - Remote not set or auth issue
  echo    - Try: git push -u origin %BRANCH%
  pause
  exit /b 1
)

echo.
echo ✅ Done! Pushed to GitHub.
echo Cloudflare Pages should redeploy automatically (if linked to this repo/branch).
timeout /t 2 >nul
