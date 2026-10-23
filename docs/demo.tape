# VHS Tape: CASI Terminal Interactive Demo
# Install VHS: https://github.com/charmbracelet/vhs
# Run: vhs docs/demo.tape

Output docs/assets/demo.gif

Set Shell "bash"
Set FontSize 14
Set Width 960
Set Height 580
Set Padding 24
Set Theme "TokyoNight"
Set WindowBar "Colorful"
Set BorderRadius 10
Set LineHeight 1.35
Set LetterSpacing 0

# 1. Run environment health check
Type "casi doctor"
Sleep 400ms
Enter
Sleep 2s

# 2. Start interactive session
Type "casi interactive --repo ."
Sleep 400ms
Enter
Sleep 2.5s

# 3. Check status
Type "/status"
Sleep 400ms
Enter
Sleep 2s

# 4. Request a task
Type "Fix ZeroDivisionError in @src/analytics/metrics.py and verify tests"
Sleep 600ms
Enter
Sleep 4s

# 5. Approve patch
Type "y"
Sleep 400ms
Enter
Sleep 2.5s

# 6. Exit
Type "/exit"
Sleep 400ms
Enter
Sleep 2s
