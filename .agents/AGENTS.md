# Google Nest Hub / Chromecast Refresh Rules

When modifying the frontend (HTML, JS, CSS) of a dashboard that is being cast to a Google Nest Hub (or any Chromecast) using `catt` (DashCast), be aware of the following caching behavior:

1. **The Issue**: Restarting the backend server (e.g., Flask) does **NOT** automatically force the Chromecast receiver to refresh the page. The Hub's DashCast receiver is a persistent browser session. If you try to cast the same URL while it is already active, it will often ignore the command or fail to do a hard reload, leaving the old cached UI (old `index.html` and old scripts) on the screen permanently.
2. **The Correct Procedure**: To guarantee that the Hub pulls the newly modified frontend code, you must:
   - explicitly stop the current cast session using `catt -d '<Hub Name>' stop`.
   - Wait 2-3 seconds for the Hub to return to the Backdrop/ambient screen.
   - Issue the `catt -d '<Hub Name>' cast_site <URL>` command again, preferably with a cache-busting query parameter (e.g., `?v=<timestamp>`).
   
Never assume that modifying static files and restarting the local server is enough to update the physical screen. Always perform a hard `catt stop` first when verifying UI changes on the physical device.

# Background Process and SSH Execution Rules

When executing background processes locally or over SSH, be aware of the following issues that cause "hanging" processes and blocked tasks, and strictly adhere to the solutions:

1. **Unredirected I/O in SSH (Hanging SSH Sessions) & The Bash `&&` Pitfall**
   - **The Issue**: When running `ssh user@host "cd /dir && nohup command > out 2>&1 &"`, the SSH session will **hang permanently**. Why? Because in Bash, `&` has lower precedence than `&&`. The command is parsed as `(cd /dir && nohup command > out 2>&1) &`. This puts the *entire subshell* into the background. Inside that subshell, `nohup` runs **synchronously**. Even though `nohup` redirects its own I/O, the *subshell* itself still holds the SSH standard file descriptors open! So SSH waits forever for the subshell to exit.
   - **The Solution**: Use a semicolon `;` instead of `&&` before the background command: `ssh user@host "cd /dir ; nohup command > out 2>&1 &"`. The `;` separates the commands, so ONLY the final command is put in the background, and the SSH session can disconnect cleanly.

3. **Temporary GUI/CLI Processes (Ghost Processes)**
   - **The Issue**: Launching commands like `/Applications/Google Chrome.app/... &` to take a screenshot and then letting the task finish leaves Chrome running indefinitely in the background, consuming memory and port resources.
   - **The Solution**: If you spawn a temporary process in the background, you MUST capture its PID and explicitly kill it after your operation (e.g., screenshot) is complete: 
     ```bash
     /Applications/Google\ Chrome.app/... &
     CHROME_PID=$!
     sleep 10
     screencapture -x /tmp/shot.png
     kill $CHROME_PID
     ```
